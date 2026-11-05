import asyncio
import json

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from mcp import Client

from flow import agents
from flow.mcp import graph_sim, world


def test_mcp_tools_in_memory() -> None:
    async def run() -> None:
        async with Client(graph_sim.mcp) as c:
            r = await c.call_tool("simulate_closure", {"chokepoints": ["hormuz"], "months": 6})
            assert not r.is_error and json.loads(r.content[0].text)["commodities"]
        async with Client(world.mcp) as c:
            assert (await c.call_tool("query", {"sql": "DELETE FROM routes"})).is_error

    asyncio.run(run())


class Scripted(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


def call(name: str, args: dict, id_: str) -> AIMessage:
    return AIMessage("", tool_calls=[{"name": name, "args": args, "id": id_}])


def test_supervisor_delegates_over_mcp_and_writes_trace(tmp_path) -> None:
    llm = Scripted(
        responses=[
            call("ask_sim_analyst", {"task": "Close Hormuz for 6 months"}, "h1"),
            call("simulate_closure", {"chokepoints": ["hormuz"], "months": 6}, "t1"),
            AIMessage("Hormuz closed 6 months: 54.16 MMT crude lost."),
            call(
                "answer",
                {
                    "summary": "India would lose 54.16 MMT of crude over six months.",
                    "points": ["Crude oil: 54.16 MMT lost"],
                    "places": ["Strait of Hormuz"],
                },
                "a1",
            ),
        ]
    )
    result = asyncio.run(agents.ask("What if Hormuz closes?", llm=llm, trace_dir=tmp_path))
    assert result["answer"].endswith("- Crude oil: 54.16 MMT lost")
    assert result["places"] == ["Strait of Hormuz"]
    trace = json.loads(next(tmp_path.glob("trace-*.json")).read_text())
    specialist = trace["specialists"][0]
    assert specialist["agent"] == "sim_analyst"
    assert '"lost_mmt":54.16' in specialist["steps"][1]["content"]  # real MCP server output
