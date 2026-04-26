import { useState } from "react";
import TierPill from "./TierPill";
import type { ExceptionPacket } from "../types";
import { createException } from "../lib/api";
import { useToken } from "../lib/useToken";
import { formatTimestamp, shortId } from "../lib/format";

// The BOSS Engine does not expose a "list all exceptions" endpoint by
// design — exception packets are either queried from the Flight
// Recorder or pushed to the console by a client embedded in your agent
// framework. This page therefore demonstrates *creating* an exception
// and keeps an in-memory audit view of whatever was created from this
// session. Your operations team can replace this with a tail against
// the Flight Recorder once the tail endpoint is wired to your SIEM.

const SAMPLE_ALTERNATIVES = [
  {
    alt_id: "alt-noop",
    description: "Do not proceed.",
    projected_composite: 0,
  },
  {
    alt_id: "alt-restrict",
    description:
      "Proceed with restricted distribution (internal stakeholders only).",
    projected_composite: 22,
  },
  {
    alt_id: "alt-delay",
    description: "Defer 24 hours for Director of Marketing approval.",
    projected_composite: 35,
  },
];

export default function ExceptionQueuePage() {
  const [token] = useToken();
  const [resultId, setResultId] = useState("");
  const [intentId, setIntentId] = useState("");
  const [summary, setSummary] = useState(
    "Risk composite above autonomous band — director review requested.",
  );
  const [queue, setQueue] = useState<ExceptionPacket[]>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    if (!intentId || !resultId) {
      setError("Both intent_id and result_id are required.");
      return;
    }
    setPending(true);
    setError(null);
    try {
      const packet = await createException(
        {
          intent_id: intentId,
          result_id: resultId,
          summary,
          alternatives: SAMPLE_ALTERNATIVES,
        },
        token,
      );
      setQueue((prev) => [packet, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-semibold">Exception Queue</h1>
        <p className="text-sm text-slate-400">
          Open exception packets for results scored ELEVATED or above. Packets
          created here are stored on the engine and surfaced in the Flight
          Recorder; this session view is in-memory.
        </p>
      </div>

      <section className="card-padded">
        <h2 className="text-sm font-medium mb-3">Open a packet</h2>
        <div className="grid sm:grid-cols-2 gap-3">
          <Field
            label="intent_id"
            value={intentId}
            onChange={setIntentId}
            mono
          />
          <Field
            label="result_id"
            value={resultId}
            onChange={setResultId}
            mono
          />
          <div className="sm:col-span-2">
            <Field label="summary" value={summary} onChange={setSummary} />
          </div>
        </div>
        <div className="mt-3 flex items-center gap-3">
          <button
            type="button"
            onClick={() => void submit()}
            disabled={pending}
            className="px-4 py-2 rounded-lg bg-adam-accent text-adam-ink font-medium hover:bg-blue-400 disabled:opacity-60"
          >
            {pending ? "Creating…" : "Open exception"}
          </button>
          {error && <span className="text-xs text-tier-ohshat">{error}</span>}
        </div>
      </section>

      <section className="card-padded">
        <h2 className="text-sm font-medium mb-3">
          This session ({queue.length})
        </h2>
        {queue.length === 0 && (
          <p className="text-sm text-slate-500 italic">
            No packets opened yet.
          </p>
        )}
        <ul className="divide-y divide-slate-800/60">
          {queue.map((pkt) => (
            <li key={pkt.packet_id} className="py-3">
              <div className="flex items-center gap-3">
                <TierPill tier={pkt.escalation_tier} />
                <span className="font-mono text-xs text-slate-400">
                  {shortId(pkt.packet_id)}
                </span>
                <span className="ml-auto text-[11px] text-slate-500">
                  SLA {pkt.response_sla_minutes} min ·{" "}
                  {formatTimestamp(pkt.generated_at)}
                </span>
              </div>
              <div className="mt-1 text-sm">{pkt.summary}</div>
              {pkt.drivers.length > 0 && (
                <div className="mt-1 text-[11px] text-slate-400">
                  drivers: {pkt.drivers.join(", ")}
                </div>
              )}
              {pkt.alternatives.length > 0 && (
                <ul className="mt-2 ml-4 text-xs text-slate-300 list-disc">
                  {pkt.alternatives.map((alt) => (
                    <li key={alt.alt_id}>
                      <span className="font-mono text-slate-500">
                        {alt.alt_id}
                      </span>{" "}
                      · {alt.description}
                      <span className="text-slate-500">
                        {" "}
                        (proj {alt.projected_composite.toFixed(0)})
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  mono,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  mono?: boolean;
}) {
  return (
    <label className="block text-xs uppercase tracking-widest text-slate-400">
      {label}
      <input
        className={`mt-1 w-full bg-adam-ink/70 border border-slate-800 rounded px-2 py-1 text-sm ${
          mono ? "font-mono" : ""
        }`}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}
