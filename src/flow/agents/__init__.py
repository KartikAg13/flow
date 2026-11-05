"""LangGraph supervisor and two specialist agents on Groq.

The supervisor delegates through handoff tools (ask_risk_analyst, ask_sim_analyst). Each
specialist runs its own tool loop against one MCP server over stdio, so agents never import
graph/sim/data. Every run writes an auditable JSON trace to artifacts/.
"""

from __future__ import annotations

import asyncio
import json
import operator
import os
import sys
from contextlib import AsyncExitStack
from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from mcp import Client, StdioServerParameters, stdio_client

ROOT = Path(__file__).resolve().parents[3]
SERVERS = {"risk_analyst": "flow.mcp.world", "sim_analyst": "flow.mcp.graph_sim"}
MAX_STEPS = 3  # tool rounds per specialist task; bounds latency
FALLBACK_MODEL = "openai/gpt-oss-20b"  # own Groq rate-limit bucket; fast, needs routing examples

PROMPTS = {
    "supervisor": (
        "You are Flow's Resilience Copilot for India's critical imports: crude oil, LNG and the "
        "fertilizers urea, DAP and MOP. Delegate with one precise task per specialist, calling "
        "both in the same turn when the question needs both. For example, 'what if Hormuz "
        "closes for 3 months?', 'which states and farmers suffer if Suez shuts?' and 'how "
        "exposed is LNG to Hormuz?' go to ask_sim_analyst; "
        "'which chokepoint is riskiest now?' goes to ask_risk_analyst. When the reports are "
        "in, answer in plain words for a busy reader. Copy numbers exactly from the reports, "
        "with units (MMT, % of imports, days), and use no others."
    ),
    "risk_analyst": (
        "You are Flow's risk analyst. Use your tools to answer the task with facts from Flow's "
        "database. Prefer risk_scores, recent_events and import_mix (commodity ids: crude_oil, "
        "lng, urea, dap, mop); use query only for what they do not cover. Report numbers with "
        "units and their source, in under 80 words."
    ),
    "sim_analyst": (
        "You are Flow's simulation analyst. Use your tools (exposure, critical_nodes, "
        "simulate_closure, closure_impact for which states, vehicles and farmers are hit, and "
        "reroute_options for alternative routes and bypass pipelines) "
        "to answer the task. Chokepoint ids: hormuz, bab_el_mandeb, suez, "
        "malacca, cape. Report the key numbers with units and the assumption, in under 80 words."
    ),
}

SKILLS = {
    "risk_analyst": "Use for current risk and news: live chokepoint risk scores, recent GDELT "
    "articles, India's suppliers per commodity, and port and facility facts.",
    "sim_analyst": "Use for any what-if, closure, blockade or exposure question: volumes through "
    "a chokepoint, port or supplier, critical nodes, and closure scenarios (lost MMT, "
    "LNG-to-urea cascade, SPR cover, alternative suppliers, the states, vehicles and farmers "
    "affected, and alternative routes: sea detours and bypass pipelines).",
}
HANDOFFS = [
    {
        "type": "function",
        "function": {
            "name": f"ask_{agent}",
            "description": SKILLS[agent],
            "parameters": {
                "type": "object",
                "properties": {"task": {"type": "string", "description": "What to find out."}},
                "required": ["task"],
            },
        },
    }
    for agent in SERVERS
]
ANSWER = {
    "type": "function",
    "function": {
        "name": "answer",
        "description": "Give the user the final answer.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "One or two sentences that answer."},
                "points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Up to five short facts, each 'Label: detail', e.g. "
                    "'Crude oil: 54.16 MMT lost, 44.8% of imports'.",
                },
                "places": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Chokepoints, Indian ports and facilities the answer names, "
                    "e.g. Strait of Hormuz, Sikka, Dahej LNG.",
                },
                "assumption": {"type": ["string", "null"], "description": "Model assumption."},
            },
            "required": ["summary", "points", "places"],
        },
    },
}


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    trace: Annotated[list[dict], operator.add]


def _dump(m: BaseMessage) -> dict:
    out = {"type": m.type, "content": m.content}
    if model := getattr(m, "response_metadata", {}).get("model_name"):
        out["model"] = model  # shows when a rate-limit fallback answered
    if getattr(m, "tool_calls", None):
        out["tool_calls"] = [{"name": t["name"], "args": t["args"]} for t in m.tool_calls]
    if isinstance(m, ToolMessage):
        out["tool"] = m.name
    return out


async def mcp_tools(stack: AsyncExitStack, module: str) -> list[StructuredTool]:
    """Spawn one MCP server over stdio and wrap its tools for LangChain."""
    params = StdioServerParameters(command=sys.executable, args=["-m", module])
    client = await stack.enter_async_context(Client(stdio_client(params)))

    def caller(name: str):
        async def call(**args) -> str:
            result = await client.call_tool(name, args)
            text = "\n".join(c.text for c in result.content if c.type == "text")
            try:  # MCP pretty-prints JSON; compact it, since every token counts on Groq's free tier
                return json.dumps(json.loads(text), separators=(",", ":"), ensure_ascii=False)
            except ValueError:
                return text

        return call

    return [
        StructuredTool(
            name=t.name,
            description=t.description or "",
            args_schema=t.input_schema,
            coroutine=caller(t.name),
        )
        for t in (await client.list_tools()).tools
    ]


async def _specialist(llm, tools: list[StructuredTool], prompt: str, task: str) -> list:
    by_name = {t.name: t for t in tools}
    bound = llm.bind_tools(tools)
    msgs: list[BaseMessage] = [SystemMessage(prompt), HumanMessage(task)]
    for _ in range(MAX_STEPS):
        ai = await bound.ainvoke(msgs)
        msgs.append(ai)
        if not ai.tool_calls:
            break
        for call in ai.tool_calls:
            tool = by_name.get(call["name"])
            out = await tool.ainvoke(call["args"]) if tool else f"unknown tool {call['name']}"
            msgs.append(ToolMessage(out, tool_call_id=call["id"], name=call["name"]))
    else:  # out of steps: hand the raw tool results to the supervisor
        msgs.append(AIMessage("\n".join(m.content for m in msgs if isinstance(m, ToolMessage))))
    return msgs


def build_graph(llm, tools: dict[str, list[StructuredTool]]):
    async def supervisor(state: State) -> dict:
        # First turn: delegate (or answer outright). Once reports are in, the answer tool is forced,
        # so a run is at most two supervisor calls and ends in a structured answer.
        reported = any(isinstance(m, ToolMessage) for m in state["messages"])
        tools, choice = ([ANSWER], "answer") if reported else ([*HANDOFFS, ANSWER], "auto")
        ai = await llm.bind_tools(tools, tool_choice=choice).ainvoke(
            [SystemMessage(PROMPTS["supervisor"]), *state["messages"]]
        )
        return {"messages": [ai]}

    async def delegate(call: dict) -> tuple[ToolMessage, list[dict]]:
        agent, task = call["name"].removeprefix("ask_"), call["args"].get("task", "")
        reply = lambda text: ToolMessage(text, tool_call_id=call["id"], name=call["name"])  # noqa: E731
        if agent not in tools:
            return reply(f"unknown agent {agent}"), []
        msgs = await _specialist(llm, tools[agent], PROMPTS[agent], task)
        steps = [_dump(m) for m in msgs[2:]]
        return reply(msgs[-1].content or "no findings"), [
            {"agent": agent, "task": task, "steps": steps}
        ]

    async def team(state: State) -> dict:  # specialists work in parallel
        done = await asyncio.gather(*map(delegate, state["messages"][-1].tool_calls))
        return {"messages": [m for m, _ in done], "trace": [t for _, ts in done for t in ts]}

    def route(state: State) -> str:
        calls = state["messages"][-1].tool_calls
        return "team" if calls and all(c["name"] != "answer" for c in calls) else END

    g = StateGraph(State)
    g.add_node("supervisor", supervisor)
    g.add_node("team", team)
    g.add_edge(START, "supervisor")
    g.add_conditional_edges("supervisor", route, ["team", END])
    g.add_edge("team", "supervisor")
    return g.compile()


@cache  # one client pool per process; the API runs every Copilot call on one event loop
def groq_llm():
    from dotenv import load_dotenv
    from langchain_groq import ChatGroq

    load_dotenv(ROOT / ".env")
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("Copilot needs GROQ_API_KEY in .env (copy .env.example).")
    model = os.getenv("FLOW_GROQ_MODEL", "openai/gpt-oss-120b")

    def chat(name: str, retries: int) -> ChatGroq:
        effort = {"reasoning_effort": "low"} if "gpt-oss" in name else {}
        return ChatGroq(model=name, temperature=0, max_retries=retries, **effort)

    # Free-tier Groq allows 8K tokens a minute per model. On a 429, switch to a model with its own
    # budget rather than sleep on retry-after; waiting is the last resort.
    return chat(model, 0).with_fallbacks([chat(FALLBACK_MODEL, 0), chat(model, 2)])


async def ask(question: str, llm=None, trace_dir: Path | None = None) -> dict:
    """Answer one question with the supervisor graph. Returns the answer and the trace path."""
    llm = llm or groq_llm()
    async with AsyncExitStack() as stack:
        tools = {agent: await mcp_tools(stack, module) for agent, module in SERVERS.items()}
        state = await build_graph(llm, tools).ainvoke(
            {"messages": [HumanMessage(question)], "trace": []}
        )
    last = state["messages"][-1]
    final = next((c["args"] for c in last.tool_calls if c["name"] == "answer"), None)
    final = final or {"summary": last.content or "No answer."}
    out = {k: final.get(k) or [] for k in ("points", "places")}
    out |= {k: final.get(k) or "" for k in ("summary", "assumption")}
    answer = "\n".join(
        [out["summary"], *(f"- {p}" for p in out["points"])]
        + ([f"Assumption: {out['assumption']}"] if out["assumption"] else [])
    )

    trace_dir = trace_dir or ROOT / "artifacts"
    trace_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    path = trace_dir / f"trace-{stamp}.json"
    record = {
        "question": question,
        "model": getattr(llm, "model_name", type(llm).__name__),
        "answer": answer,
        "supervisor": [_dump(m) for m in state["messages"]],
        "specialists": state["trace"],
    }
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return out | {
        "answer": answer,
        "trace": str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path),
    }
