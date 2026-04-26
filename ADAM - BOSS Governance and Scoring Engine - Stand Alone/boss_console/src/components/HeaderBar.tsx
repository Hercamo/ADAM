import { useEffect, useState } from "react";
import { getHealth } from "../lib/api";
import { useToken } from "../lib/useToken";

type HealthState =
  | { status: "unknown" }
  | { status: "loading" }
  | { status: "ok"; version: string }
  | { status: "error"; message: string };

export default function HeaderBar() {
  const [token, setToken] = useToken();
  const [showToken, setShowToken] = useState(false);
  const [health, setHealth] = useState<HealthState>({ status: "unknown" });

  useEffect(() => {
    let alive = true;
    setHealth({ status: "loading" });
    getHealth()
      .then((body) => {
        if (!alive) return;
        setHealth({ status: "ok", version: body.version });
      })
      .catch((err: unknown) => {
        if (!alive) return;
        setHealth({
          status: "error",
          message: err instanceof Error ? err.message : String(err),
        });
      });
    return () => {
      alive = false;
    };
  }, []);

  const healthPill =
    health.status === "ok"
      ? { label: `healthy · v${health.version}`, color: "bg-tier-soap/20 text-tier-soap" }
      : health.status === "error"
        ? { label: `unreachable · ${health.message}`, color: "bg-tier-ohshat/40 text-red-200" }
        : { label: "checking…", color: "bg-slate-700 text-slate-200" };

  return (
    <header className="border-b border-slate-800/70 bg-adam-navy/80 backdrop-blur sticky top-0 z-20">
      <div className="flex items-center gap-4 px-6 py-3">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-adam-accent/20 grid place-items-center text-adam-accent font-bold">
            B
          </div>
          <div>
            <div className="text-sm font-semibold tracking-tight">
              BOSS Evidence Console
            </div>
            <div className="text-[11px] text-slate-400">
              AI Governance & Risk — standalone engine
            </div>
          </div>
        </div>
        <div className="flex-1" />
        <span className={`pill ${healthPill.color}`}>{healthPill.label}</span>
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowToken((v) => !v)}
            className="pill bg-slate-700 text-slate-200 hover:bg-slate-600"
          >
            {token ? "Token: set" : "Set token"}
          </button>
          {showToken && (
            <div className="absolute right-0 mt-2 w-80 card-padded z-30">
              <div className="text-sm font-medium mb-2">Bearer token</div>
              <input
                className="w-full bg-adam-ink/60 border border-slate-700 rounded px-2 py-1 text-sm font-mono"
                type="password"
                placeholder="paste BOSS admin bearer token"
                value={token}
                onChange={(e) => setToken(e.target.value)}
              />
              <p className="text-[11px] text-slate-400 mt-2">
                Stored in sessionStorage only. Cleared when you close the tab.
              </p>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
