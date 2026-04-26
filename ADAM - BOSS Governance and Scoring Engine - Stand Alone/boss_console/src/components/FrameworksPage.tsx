import { useEffect, useMemo, useState } from "react";
import { getDimensions, getFrameworks } from "../lib/api";
import type { DimensionSummary, Framework } from "../types";
import { DIMENSION_ORDER } from "../types";
import { useToken } from "../lib/useToken";

export default function FrameworksPage() {
  const [token] = useToken();
  const [frameworks, setFrameworks] = useState<Framework[] | null>(null);
  const [dims, setDims] = useState<DimensionSummary[] | null>(null);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    Promise.all([getFrameworks(token), getDimensions(token)])
      .then(([fw, dm]) => {
        if (!alive) return;
        setFrameworks(fw);
        setDims(dm);
      })
      .catch((err) => {
        if (!alive) return;
        setError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      alive = false;
    };
  }, [token]);

  const filtered = useMemo(() => {
    if (!frameworks) return null;
    const q = query.trim().toLowerCase();
    if (!q) return frameworks;
    return frameworks.filter(
      (f) =>
        f.name.toLowerCase().includes(q) ||
        f.key.toLowerCase().includes(q) ||
        (f.publisher ?? "").toLowerCase().includes(q),
    );
  }, [frameworks, query]);

  const dimIndex = useMemo(() => {
    const map = new Map<string, string[]>();
    if (dims) {
      for (const d of dims) map.set(d.dimension, d.frameworks);
    }
    return map;
  }, [dims]);

  return (
    <div className="space-y-6 max-w-6xl">
      <div>
        <h1 className="text-2xl font-semibold">Framework Catalog</h1>
        <p className="text-sm text-slate-400">
          Every framework, regulation, and methodology feeding the BOSS
          dimensions, with provenance URLs.
        </p>
      </div>

      {error && (
        <div className="card-padded text-sm text-tier-ohshat">{error}</div>
      )}

      <section className="card-padded">
        <h2 className="text-sm font-medium mb-3">Attribution by dimension</h2>
        <div className="grid sm:grid-cols-2 gap-3">
          {DIMENSION_ORDER.map((dim) => {
            const keys = dimIndex.get(dim) ?? [];
            return (
              <div
                key={dim}
                className="bg-adam-ink/60 rounded-lg border border-slate-800 p-3"
              >
                <div className="text-sm font-medium capitalize">{dim}</div>
                <div className="mt-1 text-xs text-slate-400">
                  {keys.length > 0 ? keys.join(", ") : "no frameworks"}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <section className="card-padded">
        <div className="flex items-center justify-between mb-3 gap-3">
          <h2 className="text-sm font-medium">
            Frameworks ({filtered?.length ?? 0})
          </h2>
          <input
            placeholder="filter by name, key, publisher…"
            className="bg-adam-ink/70 border border-slate-800 rounded px-2 py-1 text-sm w-64"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        {!filtered && <p className="text-sm text-slate-500">Loading…</p>}
        {filtered && filtered.length === 0 && (
          <p className="text-sm text-slate-500 italic">No matches.</p>
        )}
        <ul className="divide-y divide-slate-800/60">
          {(filtered ?? []).map((fw) => (
            <li
              key={fw.key}
              className="py-3 flex items-center justify-between gap-3"
            >
              <div>
                <div className="text-sm font-medium">{fw.name}</div>
                <div className="text-[11px] text-slate-400">
                  {fw.publisher}
                  {fw.version ? ` · v${fw.version}` : ""} ·{" "}
                  <span className="font-mono">{fw.key}</span>
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
    </div>
  );
}
