import { useEffect, useState } from "react";
import { getFrameworks, getTierConfig, pingGraph } from "../lib/api";
import type { Framework, TierConfig } from "../types";
import { DIMENSION_ORDER } from "../types";
import { useToken } from "../lib/useToken";

type GraphStatus = "unknown" | "ok" | "degraded";

export default function DashboardPage() {
  const [token] = useToken();
  const [frameworks, setFrameworks] = useState<Framework[] | null>(null);
  const [tiers, setTiers] = useState<TierConfig | null>(null);
  const [graphStatus, setGraphStatus] = useState<GraphStatus>("unknown");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    async function load() {
      try {
        const [fw, cfg, ping] = await Promise.all([
          getFrameworks(token),
          getTierConfig(token),
          pingGraph(token).catch(() => ({ ok: false })),
        ]);
        if (!alive) return;
        setFrameworks(fw);
        setTiers(cfg);
        setGraphStatus(ping.ok ? "ok" : "degraded");
        setError(null);
      } catch (err) {
        if (!alive) return;
        setError(err instanceof Error ? err.message : String(err));
      }
    }
    void load();
    return () => {
      alive = false;
    };
  }, [token]);

  if (error) {
    return <ErrorCard message={error} />;
  }

  const topDimension = tiers
    ? DIMENSION_ORDER.find((dim) => tiers.assignments[dim] === "Top") ?? null
    : null;

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex flex-wrap items-end gap-3 justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Governance Dashboard</h1>
          <p className="text-sm text-slate-400">
            Live view of the BOSS engine: frameworks, tier configuration, graph
            connectivity.
          </p>
        </div>
        <div className="flex gap-2 text-xs text-slate-400">
          <span>Graph:</span>
          <span
            className={
              graphStatus === "ok"
                ? "text-tier-soap"
                : graphStatus === "degraded"
                  ? "text-tier-elevated"
                  : "text-slate-400"
            }
          >
            {graphStatus}
          </span>
        </div>
      </div>

      <section className="grid sm:grid-cols-3 gap-4">
        <Stat
          label="Frameworks"
          value={frameworks ? String(frameworks.length) : "…"}
          caption="Regulations and methodologies in the catalog"
        />
        <Stat
          label="Dimensions"
          value={String(DIMENSION_ORDER.length)}
          caption="Security, Sovereignty, Financial, Regulatory, Reputational, Rights, Doctrinal"
        />
        <Stat
          label="Top Priority"
          value={topDimension ?? "…"}
          caption="Dimension carrying the 5.0 weight"
        />
      </section>

      <section className="card-padded">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium">Priority Tier Configuration</h2>
          {tiers && (
            <span className="text-xs text-slate-400">
              Σ weight = {sumWeights(tiers).toFixed(1)}
            </span>
          )}
        </div>
        {!tiers ? (
          <p className="text-sm text-slate-400">Loading…</p>
        ) : (
          <div className="grid sm:grid-cols-2 gap-3">
            {DIMENSION_ORDER.map((dim) => {
              const tier = tiers.assignments[dim];
              const weight = tierWeight(tier);
              return (
                <div
                  key={dim}
                  className="flex items-center justify-between bg-adam-ink/60 rounded-lg px-3 py-2 border border-slate-800"
                >
                  <div>
                    <div className="text-sm font-medium capitalize">{dim}</div>
                    <div className="text-[11px] text-slate-400">
                      tier {tier} · weight {weight.toFixed(1)}
                    </div>
                  </div>
                  <div className="w-24 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-adam-accent h-full"
                      style={{ width: `${(weight / 5) * 100}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {frameworks && (
        <section className="card-padded">
          <h2 className="text-lg font-medium mb-4">Top Frameworks</h2>
          <ul className="text-sm divide-y divide-slate-800/60">
            {frameworks.slice(0, 8).map((fw) => (
              <li
                key={fw.key}
                className="flex items-center justify-between py-2"
              >
                <div>
                  <div className="font-medium">{fw.name}</div>
                  <div className="text-[11px] text-slate-400">
                    {fw.publisher}
                    {fw.version ? ` · v${fw.version}` : ""}
                  </div>
                </div>
                <a
                  href={fw.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-adam-accent hover:underline"
                >
                  source ↗
                </a>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  caption,
}: {
  label: string;
  value: string;
  caption: string;
}) {
  return (
    <div className="card-padded">
      <div className="text-xs uppercase tracking-wider text-slate-400">
        {label}
      </div>
      <div className="mt-1 text-2xl font-semibold capitalize">{value}</div>
      <div className="mt-1 text-xs text-slate-500 leading-snug">{caption}</div>
    </div>
  );
}

function ErrorCard({ message }: { message: string }) {
  return (
    <div className="card-padded border-tier-ohshat/50">
      <h2 className="text-lg font-medium">Unable to reach the BOSS API</h2>
      <p className="text-sm text-slate-300 mt-2">{message}</p>
      <p className="text-xs text-slate-400 mt-3">
        Check that the API is running (default{" "}
        <code className="font-mono">http://localhost:8080</code>) and that a
        bearer token is set if required.
      </p>
    </div>
  );
}

function tierWeight(
  tier: "Top" | "Very High" | "High" | "Medium" | "Low" | "Very Low",
): number {
  switch (tier) {
    case "Top":
      return 5;
    case "Very High":
      return 4;
    case "High":
      return 3;
    case "Medium":
      return 2;
    case "Low":
      return 1;
    case "Very Low":
      return 0.5;
  }
}

function sumWeights(cfg: TierConfig): number {
  return Object.values(cfg.assignments).reduce(
    (acc, tier) => acc + tierWeight(tier),
    0,
  );
}
