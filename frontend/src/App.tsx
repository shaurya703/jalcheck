import {
  Activity,
  Droplet,
  Flame,
  MapPin,
  ShieldAlert,
  ShieldCheck,
  Users,
} from "lucide-react";
import { useEffect, useState } from "react";
import { checkWater, getMeta, listStates } from "./api";
import type { RiskItem, RiskReport, Severity, StateSummary } from "./types";

const SEV: Record<Severity, { label: string; chip: string; ring: string; bar: string }> = {
  severe: { label: "Severe", chip: "bg-rose-600 text-white", ring: "border-rose-300 bg-rose-50", bar: "bg-rose-500" },
  high: { label: "High", chip: "bg-orange-500 text-white", ring: "border-orange-300 bg-orange-50", bar: "bg-orange-500" },
  moderate: { label: "Moderate", chip: "bg-amber-500 text-white", ring: "border-amber-300 bg-amber-50", bar: "bg-amber-400" },
  localized: { label: "Localized", chip: "bg-yellow-400 text-yellow-950", ring: "border-yellow-300 bg-yellow-50", bar: "bg-yellow-400" },
  none_reported: { label: "None reported", chip: "bg-emerald-600 text-white", ring: "border-emerald-300 bg-emerald-50", bar: "bg-emerald-500" },
};

export default function App() {
  const [states, setStates] = useState<StateSummary[]>([]);
  const [state, setState] = useState("");
  const [district, setDistrict] = useState("");
  const [report, setReport] = useState<RiskReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [disclaimer, setDisclaimer] = useState("");

  useEffect(() => {
    listStates().then((r) => setStates(r.states)).catch(() => {});
    getMeta().then((m) => setDisclaimer(m.disclaimer)).catch(() => {});
  }, []);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    if (!state) {
      setError("Pick your state.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setReport(await checkWater(state, district));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-4xl items-center gap-2 px-4 py-3 font-display text-lg font-bold">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-primary text-white">
            <Droplet className="h-4.5 w-4.5" aria-hidden="true" />
          </span>
          JalCheck
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-4 pb-24">
        <div className="py-10">
          <div className="mx-auto max-w-2xl text-center">
            <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
              Is your drinking water <span className="text-primary">contaminated?</span>
            </h1>
            <p className="mt-3 text-slate-700">
              Across India, groundwater carries arsenic, fluoride, nitrate and
              uranium that you can't see, smell or taste — and that boiling won't
              remove. Government surveys know where. Check your area.
            </p>
          </div>

          <form onSubmit={run} className="mx-auto mt-8 max-w-xl rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block">
                <span className="text-sm font-semibold text-slate-700">Your state</span>
                <select
                  value={state}
                  onChange={(e) => setState(e.target.value)}
                  className="mt-1 w-full cursor-pointer rounded-xl border border-slate-300 bg-white p-3 text-base focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                >
                  <option value="">Choose your state…</option>
                  {states.map((s) => (
                    <option key={s.state_code} value={s.state}>{s.state}</option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-slate-700">District <span className="font-normal text-slate-400">(optional)</span></span>
                <div className="relative mt-1">
                  <MapPin className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                  <input
                    value={district}
                    onChange={(e) => setDistrict(e.target.value)}
                    placeholder="e.g. Nalgonda"
                    className="w-full rounded-xl border border-slate-300 bg-white p-3 pl-9 text-base focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  />
                </div>
              </label>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="mt-4 w-full rounded-xl bg-primary py-3 font-semibold text-white transition-colors duration-200 hover:bg-primary-dark focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:opacity-50 motion-reduce:transition-none"
            >
              {loading ? "Checking…" : "Check my water"}
            </button>
            {error && <p className="mt-3 text-center text-sm text-rose-600">{error}</p>}
          </form>

          {report && <Report report={report} />}
          {!report && states.length > 0 && <Overview states={states} onPick={(s) => { setState(s); setDistrict(""); }} />}
        </div>
      </main>

      <footer className="border-t border-slate-200 bg-white py-6 text-center text-sm text-slate-600">
        <p className="mx-auto max-w-2xl px-4">{disclaimer}</p>
      </footer>
    </div>
  );
}

function Report({ report }: { report: RiskReport }) {
  const sev = SEV[report.overall_severity];
  return (
    <div className="mx-auto mt-8 max-w-2xl">
      <div className={`rounded-2xl border p-5 ${sev.ring}`}>
        <div className="flex items-start gap-3">
          <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-full ${sev.chip}`}>
            {report.overall_severity === "none_reported"
              ? <ShieldCheck className="h-5 w-5" aria-hidden="true" />
              : <ShieldAlert className="h-5 w-5" aria-hidden="true" />}
          </span>
          <div>
            <h2 className="font-display text-lg font-bold">{report.headline}</h2>
            <p className="mt-1 text-sm text-slate-700">{report.summary}</p>
          </div>
        </div>

        {report.boiling_warning && (
          <div className="mt-4 flex items-start gap-2 rounded-xl border border-rose-300 bg-white p-3 text-sm text-rose-900">
            <Flame className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            <span>{report.boiling_warning}</span>
          </div>
        )}
        {report.recommended_filter && (
          <div className="mt-3 flex items-start gap-2 rounded-xl border border-sky-300 bg-white p-3 text-sm text-sky-900">
            <Droplet className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            <span>{report.recommended_filter}</span>
          </div>
        )}
        {report.note && <p className="mt-3 text-sm text-slate-600">{report.note}</p>}
      </div>

      {report.risks.length > 0 && (
        <div className="mt-4 space-y-3">
          {report.risks.map((r) => <RiskCard key={r.contaminant_id} risk={r} />)}
        </div>
      )}

      <p className="mt-4 text-xs text-slate-500">
        Sources are listed on each contaminant. Always test your own source at a certified lab to be sure.
      </p>
    </div>
  );
}

function RiskCard({ risk }: { risk: RiskItem }) {
  const sev = SEV[risk.severity];
  const fmt = (n: number) => n.toLocaleString("en-IN");
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <div className="flex items-center gap-2 border-b border-slate-100 p-4">
        <span className="font-display font-bold">{risk.name}</span>
        <span className={`rounded-full px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide ${sev.chip}`}>
          {sev.label}
        </span>
        {risk.in_your_district && (
          <span className="inline-flex items-center gap-1 rounded-full bg-primary px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide text-white">
            <MapPin className="h-3 w-3" aria-hidden="true" /> Your district
          </span>
        )}
      </div>
      <div className="space-y-3 p-4 text-sm">
        <div className="flex items-start gap-2">
          <Activity className="mt-0.5 h-4 w-4 shrink-0 text-rose-500" aria-hidden="true" />
          <p className="text-slate-700">{risk.health_effects}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-slate-600">
          <Users className="h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
          <span className="text-xs">Most at risk:</span>
          {risk.vulnerable.map((v) => (
            <span key={v} className="rounded-full bg-slate-100 px-2 py-0.5 text-xs">{v}</span>
          ))}
        </div>
        <div className="rounded-xl bg-sky-50 p-3 text-sky-900">
          <strong>How to remove it:</strong> {risk.removal}
        </div>
        <div className="grid gap-1 text-xs text-slate-500 sm:grid-cols-2">
          {risk.affected_habitations != null && (
            <span>{fmt(risk.affected_habitations)} affected habitations
              {risk.affected_population != null && ` · ~${fmt(risk.affected_population)} people`}</span>
          )}
          {risk.notable_districts.length > 0 && (
            <span className="sm:col-span-2">Reported in: {risk.notable_districts.join(", ")}</span>
          )}
          <span className="sm:col-span-2">Source: {risk.source}</span>
        </div>
      </div>
    </div>
  );
}

function Overview({ states, onPick }: { states: StateSummary[]; onPick: (s: string) => void }) {
  const order: Severity[] = ["severe", "high", "moderate", "localized", "none_reported"];
  const sorted = [...states].sort(
    (a, b) => order.indexOf(a.worst_severity) - order.indexOf(b.worst_severity) || a.state.localeCompare(b.state),
  );
  return (
    <div className="mx-auto mt-10 max-w-3xl">
      <h2 className="text-sm font-bold uppercase tracking-wide text-slate-500">All states by worst contamination</h2>
      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        {sorted.map((s) => (
          <button
            key={s.state_code}
            onClick={() => onPick(s.state)}
            className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-3 text-left transition-colors duration-200 hover:border-primary/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 motion-reduce:transition-none"
          >
            <span>
              <span className="font-semibold">{s.state}</span>
              {s.contaminant_count > 0 && (
                <span className="block text-xs text-slate-500">{s.contaminants.join(", ")}</span>
              )}
            </span>
            <span className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide ${SEV[s.worst_severity].chip}`}>
              {SEV[s.worst_severity].label}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
