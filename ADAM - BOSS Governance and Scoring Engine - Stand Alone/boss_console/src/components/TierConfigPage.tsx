import { useEffect, useMemo, useState } from "react";
import { getTierConfig, putTierConfig } from "../lib/api";
import { useToken } from "../lib/useToken";
import type { Tier, TierConfig } from "../types";
import { DIMENSION_ORDER } from "../types";

const TIERS: Tier[] = ["Top", "Very High", "High", "Medium", "Low", "Very Low"];
const WEIGHTS: Record<Tier, number> = {
  Top: 5,
  "Very High": 4,
  High: 3,
  Medium: 2,
  Low: 1,
  "Very Low": 0.5,
};

export default function TierConfigPage() {
  const [token] = useToken();
  const [current, setCurrent] = useState<TierConfig | null>(null);
  const [draft, setDraft] = useState<TierConfig["assignments"] | null>(null);
  const [author, setAuthor] = useState("boss.console");
  const [reason, setReason] = useState(
    "Priority rebalance approved by the director circle.",
  );
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    getTierConfig(token)
      .then((cfg) => {
        if (!alive) return;
        setCurrent(cfg);
        setDraft({ ...cfg.assignments });
      })
      .catch((err) => {
        if (!alive) return;
        setStatus(err instanceof Error ? err.message : String(err));
      });
    return () => {
      alive = false;
    };
  }, [token]);

  const totals = useMemo(() => {
    if (!draft) return { sum: 0, tops: 0, ok: false };
    const tops = Object.values(draft).filter((t) => t === "Top").length;
    const sum = Object.values(draft).reduce(
      (acc, t) => acc + WEIGHTS[t as Tier],
      0,
    );
    return { sum, tops, ok: tops === 1 };
  }, [draft]);

  const submit = async () => {
    if (!draft) return;
    if (!totals.ok) {
      setStatus("Exactly one dimension must be tier 'Top'.");
      return;
    }
    try {
      const saved = await putTierConfig(
        { assignments: draft, author, reason },
        token,
      );
      setCurrent(saved);
      setStatus("Tier configuration saved ✓");
    } catch (err) {
      setStatus(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-semibold">Priority Tier Configuration</h1>
        <p className="text-sm text-slate-400">
          Assign a tier to every BOSS dimension. Changes are director-only and
          written to the Flight Recorder as a{" "}
          <code className="font-mono text-adam-accent">CONFIG_CHANGED</code>{" "}
          event.
        </p>
      </div>

      {!draft && <p className="text-sm text-slate-500">Loading…</p>}

      {draft && (
        <>
          <section className="card-padded">
            <div className="grid grid-cols-12 gap-2 text-[11px] uppercase tracking-widest text-slate-400 mb-2">
              <div className="col-span-4">Dimension</div>
              <div className="col-span-4">Tier</div>
              <div className="col-span-4">Weight</div>
            </div>
            {DIMENSION_ORDER.map((dim) => {
              const tier = draft[dim] as Tier;
              return (
                <div
                  key={dim}
                  className="grid grid-cols-12 gap-2 items-center py-1 border-t border-slate-800/60"
                >
                  <div className="col-span-4 text-sm capitalize">{dim}</div>
                  <div className="col-span-4">
                    <select
                      className="bg-adam-ink/70 border border-slate-800 rounded px-2 py-1 text-sm w-full"
                      value={tier}
                      onChange={(e) =>
                        setDraft({
                          ...draft,
                          [dim]: e.target.value as Tier,
                        })
                      }
                    >
                      {TIERS.map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="col-span-4 text-xs text-slate-400">
                    {WEIGHTS[tier].toFixed(1)}
                  </div>
                </div>
              );
            })}
            <div className="mt-3 text-xs flex gap-4">
              <span>Σ weight = {totals.sum.toFixed(1)}</span>
              <span
                className={
                  totals.tops === 1 ? "text-tier-soap" : "text-tier-ohshat"
                }
              >
                {totals.tops === 1
                  ? "Exactly one Top ✓"
                  : `${totals.tops} dimensions set to Top (must be 1)`}
              </span>
            </div>
          </section>

          <section className="card-padded">
            <h2 className="text-sm font-medium mb-3">Audit fields</h2>
            <div className="grid sm:grid-cols-2 gap-3">
              <label className="block text-xs uppercase tracking-widest text-slate-400">
                author
                <input
                  className="mt-1 w-full bg-adam-ink/70 border border-slate-800 rounded px-2 py-1 text-sm"
                  value={author}
                  onChange={(e) => setAuthor(e.target.value)}
                />
              </label>
              <label className="block text-xs uppercase tracking-widest text-slate-400">
                reason
                <input
                  className="mt-1 w-full bg-adam-ink/70 border border-slate-800 rounded px-2 py-1 text-sm"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                />
              </label>
            </div>
            <div className="mt-3 flex items-center gap-3">
              <button
                type="button"
                onClick={() => void submit()}
                disabled={!totals.ok}
                className="px-4 py-2 rounded-lg bg-adam-accent text-adam-ink font-medium hover:bg-blue-400 disabled:opacity-60"
              >
                Save configuration
              </button>
              {current && (
                <button
                  type="button"
                  onClick={() => setDraft({ ...current.assignments })}
                  className="text-xs text-slate-400 hover:text-white"
                >
                  revert to server
                </button>
              )}
              {status && (
                <span
                  className={`text-xs ${
                    status.includes("✓")
                      ? "text-tier-soap"
                      : "text-tier-ohshat"
                  }`}
                >
                  {status}
                </span>
              )}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
