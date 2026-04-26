import { useCallback, useEffect, useState } from "react";
import type { FlightRecorderEvent } from "../types";
import { tailFlightRecorder } from "../lib/api";
import { useToken } from "../lib/useToken";
import { formatTimestamp, shortHash, shortId } from "../lib/format";

const EVENT_TYPES: Array<{ value: string; label: string }> = [
  { value: "", label: "All events" },
  { value: "INTENT_RECEIVED", label: "Intents" },
  { value: "SCORED", label: "Scored" },
  { value: "EXCEPTION_RAISED", label: "Exceptions" },
  { value: "DECISION_RECORDED", label: "Receipts" },
  { value: "CONFIG_CHANGED", label: "Config changes" },
];

export default function FlightRecorderPage() {
  const [token] = useToken();
  const [filter, setFilter] = useState("");
  const [events, setEvents] = useState<FlightRecorderEvent[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [integrityOk, setIntegrityOk] = useState<boolean | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const tail = await tailFlightRecorder(
        { eventType: filter || undefined, limit: 200 },
        token,
      );
      setEvents(tail);
      setIntegrityOk(verifyChain(tail));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setEvents(null);
    } finally {
      setLoading(false);
    }
  }, [filter, token]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Flight Recorder</h1>
          <p className="text-sm text-slate-400">
            Immutable, hash-chained audit log.{" "}
            {integrityOk === null
              ? ""
              : integrityOk
                ? "Chain integrity ✓ verified."
                : "⚠ Chain integrity broken — investigate immediately."}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            className="bg-adam-ink/70 border border-slate-800 rounded px-2 py-1 text-sm"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            {EVENT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => void load()}
            disabled={loading}
            className="px-3 py-1 text-sm rounded bg-slate-700 hover:bg-slate-600"
          >
            {loading ? "Loading…" : "Refresh"}
          </button>
        </div>
      </div>

      {error && (
        <div className="card-padded text-sm text-tier-ohshat">
          {error} — the Flight Recorder tail endpoint is optional and may not be
          enabled on this deployment. Configure{" "}
          <code className="font-mono">BOSS_FLIGHT_RECORDER_TAIL=1</code> on the
          API.
        </div>
      )}

      {!error && events && events.length === 0 && (
        <p className="text-sm text-slate-500 italic">
          No events returned. Submit an intent or sign a receipt to populate
          the log.
        </p>
      )}

      {events && events.length > 0 && (
        <div className="card overflow-hidden">
          <div className="data-row text-[11px] uppercase tracking-widest text-slate-400 border-b border-slate-800 py-2">
            <div className="col-span-2">Timestamp</div>
            <div className="col-span-2">Event</div>
            <div className="col-span-2">Signer</div>
            <div className="col-span-3">Payload keys</div>
            <div className="col-span-3">Hash chain</div>
          </div>
          {events.map((e) => (
            <div key={e.event_id} className="data-row text-sm">
              <div className="col-span-2 text-[12px] text-slate-300">
                {formatTimestamp(e.timestamp)}
              </div>
              <div className="col-span-2">
                <span className="pill bg-slate-800 text-slate-200">
                  {e.event_type}
                </span>
              </div>
              <div className="col-span-2 text-xs text-slate-300">
                {e.signer}
              </div>
              <div className="col-span-3 text-[11px] text-slate-400 font-mono">
                {Object.keys(e.payload).slice(0, 6).join(", ")}
              </div>
              <div className="col-span-3 text-[11px] text-slate-400 font-mono leading-tight">
                <div>prior: {shortHash(e.prior_hash)}</div>
                <div>self:  {shortHash(e.event_hash)}</div>
                <div className="text-slate-500">id {shortId(e.event_id)}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Client-side cheap integrity check — compares each event's prior_hash to
// the previous event's event_hash. A full cryptographic re-hash is done
// server-side; this just surfaces an obvious chain break immediately.
function verifyChain(events: FlightRecorderEvent[]): boolean {
  if (events.length <= 1) return true;
  // The API returns most-recent first; walk in chronological order.
  const chronological = [...events].reverse();
  for (let i = 1; i < chronological.length; i++) {
    if (chronological[i].prior_hash !== chronological[i - 1].event_hash) {
      return false;
    }
  }
  return true;
}
