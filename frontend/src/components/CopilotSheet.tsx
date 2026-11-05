import { useEffect, useRef, useState, type FormEvent } from "react";
import { api, commodityLabels, type Answer, type Impact, type Place, type Reroutes, type Scenario } from "../api";
import { count, mmt, pct, tonnes } from "../utils/risk";

export interface ScenarioRequest {
  chokepoint: string;
  name: string;
  months: number;
  at: number; // a repeat click re-runs the same scenario
}

interface Turn {
  question: string;
  answer?: Answer;
  error?: string;
}

const SUGGESTIONS = [
  "What happens if Hormuz is closed for 6 months?",
  "Which chokepoint is riskiest right now, and why?",
  "How exposed is India's LNG to the Strait of Hormuz?",
];

export default function CopilotSheet({
  open,
  scenario,
  onClose,
  onPlaces,
}: {
  open: boolean;
  scenario: ScenarioRequest | null;
  onClose: () => void;
  onPlaces: (places: Place[]) => void;
}) {
  const [result, setResult] = useState<{ data?: Scenario; error?: string }>({});
  const [turns, setTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const busy = turns.length > 0 && !turns[turns.length - 1].answer && !turns[turns.length - 1].error;
  const input = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!scenario) return;
    setResult({});
    api.simulate(scenario.chokepoint, scenario.months).then(
      (data) => setResult({ data }),
      (e: Error) => setResult({ error: e.message }),
    );
  }, [scenario]);

  useEffect(() => {
    if (!open) return;
    input.current?.focus({ preventScroll: true });
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  const ask = (question: string) => {
    question = question.trim();
    if (!question || busy) return;
    setDraft("");
    setTurns((t) => [...t, { question }]);
    const settle = (patch: Partial<Turn>) => setTurns((t) => t.map((x, i) => (i === t.length - 1 ? { ...x, ...patch } : x)));
    onPlaces([]);
    api.ask(question).then(
      (answer) => {
        settle({ answer });
        onPlaces(answer.places);
      },
      (e: Error) => settle({ error: e.message }),
    );
  };

  const submit = (e: FormEvent) => {
    e.preventDefault();
    ask(draft);
  };

  return (
    <aside id="copilot" className={`sheet${open ? " is-open" : ""}`} aria-label="Resilience Copilot" aria-hidden={!open}>
      <header className="sheet__header">
        <h2>Copilot</h2>
        <button className="button button--plain" onClick={onClose} aria-label="Close Copilot">
          Done
        </button>
      </header>

      <div className="sheet__body" aria-live="polite">
        {scenario && (
          <ScenarioCard
            title={`${scenario.name} closed for ${scenario.months} month${scenario.months > 1 ? "s" : ""}`}
            result={result}
            onExplain={() => ask(`Explain what happens to India if ${scenario.name} is closed for ${scenario.months} months, and what India can do.`)}
          />
        )}

        {turns.length === 0 && (
          <div className="suggestions">
            <p className="muted">
              Ask about risk, exposure or a closure. A supervisor agent hands the question to a risk analyst and a
              simulation analyst, and each run is saved as a trace.
            </p>
            {SUGGESTIONS.map((s) => (
              <button key={s} className="chip chip--link" onClick={() => ask(s)}>
                {s}
              </button>
            ))}
          </div>
        )}

        {turns.map((t, i) => (
          <article key={i} className="turn">
            <p className="turn__question">{t.question}</p>
            {!t.answer && !t.error && <p className="turn__pending">Analysts are working. This usually takes 10–30 seconds.</p>}
            {t.answer && (
              <>
                <p className="turn__answer">{rich(t.answer.summary)}</p>
                {t.answer.points.length > 0 && (
                  <ul className="turn__points">
                    {t.answer.points.map((p, j) => (
                      <li key={j}>{point(p)}</li>
                    ))}
                  </ul>
                )}
                {t.answer.places.length > 0 && (
                  <p className="turn__places">
                    <span className="swatch swatch--high" /> Marked on the map: {t.answer.places.map((p) => p.name).join(", ")}
                  </p>
                )}
                {t.answer.assumption && <p className="scenario__note">{t.answer.assumption}</p>}
                <p className="turn__trace">Trace saved to {t.answer.trace}</p>
              </>
            )}
            {t.error && (
              <p className="turn__error">
                {t.error}
                <br />
                <span className="muted">Simulate closure works without the Copilot.</span>
              </p>
            )}
          </article>
        ))}
      </div>

      <form className="sheet__composer" onSubmit={submit}>
        <textarea
          ref={input}
          value={draft}
          rows={2}
          maxLength={500}
          placeholder="Ask about India's import risk…"
          aria-label="Question for the Copilot"
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && submit(e)}
        />
        <button className="button button--tint" type="submit" disabled={busy || !draft.trim()}>
          Ask
        </button>
      </form>
    </aside>
  );
}

// The model sometimes still writes **bold**; show it as bold rather than asterisks.
const rich = (text: string) => text.split(/\*\*(.+?)\*\*/g).map((s, i) => (i % 2 ? <strong key={i}>{s}</strong> : s));

// "Crude oil: 54.16 MMT lost" -> bold label, then the detail.
function point(text: string) {
  const m = text.match(/^([^:]{1,40}):\s*([\s\S]*)$/);
  return m ? (
    <>
      <strong>{m[1].replace(/\*\*/g, "")}</strong> {rich(m[2])}
    </>
  ) : (
    rich(text)
  );
}

function ScenarioCard({
  title,
  result,
  onExplain,
}: {
  title: string;
  result: { data?: Scenario; error?: string };
  onExplain: () => void;
}) {
  const s = result.data;
  return (
    <article className="scenario" aria-label="Closure scenario">
      <h3>{title}</h3>
      {result.error && <p className="turn__error">{result.error}</p>}
      {!s && !result.error && <p className="muted">Simulating…</p>}
      {s && (
        <>
          <dl className="scenario__grid">
            {s.commodities.map((c) => (
              <div key={c.commodity}>
                <dt>{commodityLabels[c.commodity]}</dt>
                <dd>
                  {mmt(c.lost_mmt)} <small>MMT</small>
                </dd>
                <dd className="muted">{pct(c.share_of_imports)} of imports</dd>
              </div>
            ))}
          </dl>
          {s.ports.length > 0 && (
            <p>
              <strong>Ports losing cargo.</strong>{" "}
              {s.ports.slice(0, 4).map((p) => `${p.name}, ${p.state} ${tonnes(p.lost_mmt)}`).join(" · ")} MMT
            </p>
          )}
          {s.facilities.length > 0 && (
            <p>
              <strong>Plants losing feedstock.</strong>{" "}
              {s.facilities.slice(0, 4).map((f) => `${f.name}, ${f.state} ${tonnes(f.lost_mmt)}`).join(" · ")} MMT
            </p>
          )}
          {s.downstream.length > 0 && (
            <p>
              <strong>Inland, by pipeline.</strong>{" "}
              {s.downstream
                .slice(0, 4)
                .map((d) => `${d.from} feeds ${d.sites.map((x) => x.name).join(", ")}`)
                .join("; ")}
              .
            </p>
          )}
          {s.impact.urea_plants.output_lost_share > 0 && (
            <p>
              <strong>Urea plants.</strong> Gas-based urea plants lose about {pct(s.impact.urea_plants.output_lost_share)} of
              their output, among them{" "}
              {s.impact.urea_plants.plants.slice(0, 4).map((p) => `${p.name} (${p.state})`).join(", ")}.
            </p>
          )}
          {s.cascade.urea_output_at_risk_mmt > 0 && (
            <p>
              <strong>Gas to fertilizer.</strong> Losing {mmt(s.cascade.lng_lost_mmt)} MMT of LNG puts about{" "}
              {mmt(s.cascade.urea_output_at_risk_mmt)} MMT of domestic urea output at risk.
            </p>
          )}
          {s.spr.days_of_lost_crude_covered !== null && (
            <p>
              <strong>Strategic reserves.</strong> {s.spr.capacity_mmt} MMT covers about{" "}
              {Math.round(s.spr.days_of_lost_crude_covered)} days of the missing crude.
            </p>
          )}
          <ImpactSection impact={s.impact} />
          <ReroutesSection r={s.reroutes} />
          {Object.entries(s.alternatives).map(([c, alts]) =>
            alts && alts.length ? (
              <p key={c}>
                <strong>{commodityLabels[c as keyof typeof commodityLabels]} still arriving.</strong>{" "}
                {alts.map((a) => `${a.supplier} ${mmt(a.mmt_per_year)} MMT/yr`).join(", ")}
              </p>
            ) : null,
          )}
          <p className="scenario__note">{s.assumption}</p>
          <button className="button" onClick={onExplain}>
            Ask Copilot to explain
          </button>
        </>
      )}
    </article>
  );
}

const label = (c: string) => commodityLabels[c as keyof typeof commodityLabels] ?? c;
// "Crude oil" -> "crude oil" mid-sentence, but keep LNG, DAP, SUVs and other capitals
const inline = (text: string) => (/^[A-Z][a-z]/.test(text) ? text[0].toLowerCase() + text.slice(1) : text);
const days = (d: number) => {
  const n = Math.max(1, Math.round(Math.abs(d)));
  return `${d < 0 ? "" : "+"}${n} day${n === 1 ? "" : "s"}${d < 0 ? " shorter" : ""}`;
};

const LANDS_LABEL: Record<string, string> = { ...commodityLabels, urea_output: "urea output" };

// Where the shortfall lands and who runs short: states, fuel users, farm holdings.
function ImpactSection({ impact: i }: { impact: Impact }) {
  if (!i.states_hit.length) return null;
  const fuel = (label: string, f: Impact["fuel"]["diesel"]) =>
    f.short_mmt > 0 && (
      <p>
        <strong>{label}.</strong> {tonnes(f.short_mmt)} MMT short, {pct(f.share_of_use)} of normal use (about{" "}
        {Math.round(f.days_of_use_lost)} days): {f.segments.slice(0, 5).map((s) => `${inline(s.segment)} ${tonnes(s.kt / 1000)}`).join(", ")}{" "}
        MMT.
      </p>
    );
  const fert = Object.entries(i.fertilizer).filter(([, v]) => v.share_of_use > 0);
  return (
    <section className="impact" aria-label="Who is affected">
      <h4>Where it lands</h4>
      <p>
        {i.states_hit.slice(0, 4).map((st) => (
          <span key={st.state} className="impact__state">
            <strong>{st.state}</strong> {tonnes(st.lost_mmt)} MMT{" "}
            <span className="muted">({Object.keys(st.by).slice(0, 3).map((c) => LANDS_LABEL[c] ?? c).join(", ")})</span>
          </span>
        ))}
      </p>
      <h4>Who runs short</h4>
      {fuel("Diesel", i.fuel.diesel)}
      {fuel("Petrol", i.fuel.petrol)}
      {fert.length > 0 && (
        <p>
          <strong>Farmers.</strong> {fert.map(([c, v]) => `${commodityLabels[c as keyof typeof commodityLabels]} ${pct(v.share_of_use)}`).join(", ")}{" "}
          short, reaching about {count(i.farm_holdings_affected)} farm holdings.
        </p>
      )}
      {i.city_gas_lost_mmt_lng > 0 && (
        <p>
          <strong>City gas.</strong> CNG vehicles and piped cooking gas lose {tonnes(i.city_gas_lost_mmt_lng)} MMT of LNG; power
          plants lose {tonnes(i.power_gas_lost_mmt_lng)} MMT.
        </p>
      )}
      {i.farm_short_states.length > 0 && (
        <table className="impact__table">
          <thead>
            <tr>
              <th scope="col">State</th>
              <th scope="col">Fuel short</th>
              <th scope="col">Fertilizer short</th>
              <th scope="col">Farm holdings</th>
            </tr>
          </thead>
          <tbody>
            {i.farm_short_states.slice(0, 6).map((r) => (
              <tr key={r.state}>
                <th scope="row">{r.state}</th>
                <td>{tonnes((r.diesel_kt + r.petrol_kt) / 1000)}</td>
                <td>{tonnes(r.fertilizer_kt / 1000)}</td>
                <td>{count(r.farm_holdings)}</td>
              </tr>
            ))}
          </tbody>
          <caption>Million tonnes over the closure; states with the most farm holdings affected</caption>
        </table>
      )}
      <p className="scenario__note">{i.assumption}</p>
    </section>
  );
}

// Ways around the closure: bypass pipelines, sea detours, what stays stuck, open entry points.
function ReroutesSection({ r }: { r: Reroutes }) {
  const lost = r.recovered.filter((c) => c.lost_mmt > 0);
  if (!lost.length) return null;
  const stuck = r.stranded.filter((x) => x.reason !== "origin not known");
  return (
    <section className="impact" aria-label="Alternative routes">
      <h4>Alternative routes</h4>
      <table className="impact__table">
        <thead>
          <tr>
            <th scope="col">Commodity</th>
            <th scope="col">Lost</th>
            <th scope="col">Rerouted</th>
            <th scope="col">Still lost</th>
          </tr>
        </thead>
        <tbody>
          {lost.map((c) => (
            <tr key={c.commodity}>
              <th scope="row">{label(c.commodity)}</th>
              <td>{tonnes(c.lost_mmt)}</td>
              <td>{tonnes(c.recovered_mmt)}</td>
              <td>{tonnes(c.still_lost_mmt)}</td>
            </tr>
          ))}
        </tbody>
        <caption>Million tonnes over the closure</caption>
      </table>
      {r.bypasses.map((b) => (
        <p key={b.pipeline}>
          <strong>{b.supplier} by pipeline.</strong> {b.pipeline} to {b.outlet}, then {b.via.join(", ")}: about{" "}
          {tonnes(b.mmt)} of {tonnes(b.of_blocked_mmt)} MMT ({days(b.extra_days)}).
        </p>
      ))}
      {r.detours.length > 0 && (
        <p>
          <strong>Sea detours.</strong>{" "}
          {r.detours
            .slice(0, 5)
            .map((d) => `${d.supplier} ${inline(label(d.commodity))} via ${d.via.join(" and ")} (${days(d.extra_days)})`)
            .join("; ")}
          .
        </p>
      )}
      {stuck.length > 0 && (
        <p>
          <strong>No way around.</strong>{" "}
          {stuck.map((x) => `${x.supplier} ${inline(label(x.commodity))} ${tonnes(x.mmt)}`).join(", ")} MMT.
        </p>
      )}
      {r.entry_points.length > 0 && (
        <p>
          <strong>Open entry points.</strong>{" "}
          {r.entry_points
            .slice(0, 4)
            .map((e) => `${e.site} (${e.pipeline.split(" (")[0]} to ${e.reaches.join(", ")})`)
            .join("; ")}
          .
        </p>
      )}
      <p className="scenario__note">{r.assumption}</p>
    </section>
  );
}
