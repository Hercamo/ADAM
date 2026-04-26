import { useState } from "react";
import { submitReceipt } from "../lib/api";
import { useToken } from "../lib/useToken";
import type { DecisionReceipt } from "../types";
import { formatTimestamp, shortHash, shortId } from "../lib/format";

const DECISIONS: DecisionReceipt["decision"][] = [
  "APPROVE",
  "APPROVE_WITH_CONSTRAINTS",
  "REJECT",
  "DEFER",
  "ESCALATE",
];

export default function ReceiptsPage() {
  const [token] = useToken();
  const [packetId, setPacketId] = useState("");
  const [intentId, setIntentId] = useState("");
  const [resultId, setResultId] = useState("");
  const [directorId, setDirectorId] = useState("cfo");
  const [decision, setDecision] = useState<DecisionReceipt["decision"]>(
    "APPROVE_WITH_CONSTRAINTS",
  );
  const [note, setNote] = useState("Approved with constraint: EU-only distribution.");
  const [receipts, setReceipts] = useState<DecisionReceipt[]>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    setPending(true);
    setError(null);
    try {
      const receipt = await submitReceipt(
        {
          packet_id: packetId,
          intent_id: intentId,
          result_id: resultId,
          director_id: directorId,
          decision,
          director_note: note,
          applied_constraints: [],
          selected_alternative: null,
        },
        token,
      );
      setReceipts((prev) => [receipt, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-semibold">Decision Receipts</h1>
        <p className="text-sm text-slate-400">
          Record a director's decision against an open exception packet.
          Receipts are hash-chained — each receipt's{" "}
          <code className="font-mono text-adam-accent">prior_hash</code> is the{" "}
          <code className="font-mono text-adam-accent">receipt_hash</code> of
          the previous entry.
        </p>
      </div>

      <section className="card-padded">
        <h2 className="text-sm font-medium mb-3">Sign a decision</h2>
        <div className="grid sm:grid-cols-3 gap-3">
          <Field
            label="packet_id"
            value={packetId}
            onChange={setPacketId}
            mono
          />
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
          <Field
            label="director_id"
            value={directorId}
            onChange={setDirectorId}
            mono
          />
          <label className="block text-xs uppercase tracking-widest text-slate-400">
            decision
            <select
              className="mt-1 w-full bg-adam-ink/70 border border-slate-800 rounded px-2 py-1 text-sm"
              value={decision}
              onChange={(e) =>
                setDecision(e.target.value as DecisionReceipt["decision"])
              }
            >
              {DECISIONS.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </label>
          <div className="sm:col-span-3">
            <Field label="director_note" value={note} onChange={setNote} />
          </div>
        </div>
        <div className="mt-3 flex items-center gap-3">
          <button
            type="button"
            onClick={() => void submit()}
            disabled={pending}
            className="px-4 py-2 rounded-lg bg-adam-accent text-adam-ink font-medium hover:bg-blue-400 disabled:opacity-60"
          >
            {pending ? "Signing…" : "Sign receipt"}
          </button>
          {error && <span className="text-xs text-tier-ohshat">{error}</span>}
        </div>
      </section>

      <section className="card-padded">
        <h2 className="text-sm font-medium mb-3">
          This session ({receipts.length})
        </h2>
        {receipts.length === 0 && (
          <p className="text-sm text-slate-500 italic">
            No receipts signed yet.
          </p>
        )}
        <ul className="divide-y divide-slate-800/60">
          {receipts.map((r) => (
            <li key={r.receipt_id} className="py-3">
              <div className="flex items-center gap-3 text-sm">
                <span className="pill bg-slate-700 text-slate-100">
                  {r.decision}
                </span>
                <span className="font-mono text-xs text-slate-400">
                  {shortId(r.receipt_id)}
                </span>
                <span className="text-[11px] text-slate-500 ml-auto">
                  {formatTimestamp(r.signed_at)}
                </span>
              </div>
              <div className="text-xs text-slate-400 mt-1">
                director {r.director_id} · packet {shortId(r.packet_id)}
              </div>
              {r.director_note && (
                <div className="text-sm mt-1">{r.director_note}</div>
              )}
              <div className="grid grid-cols-2 gap-2 mt-2 text-[11px] font-mono text-slate-400">
                <div>prior: {shortHash(r.prior_hash)}</div>
                <div>self:  {shortHash(r.receipt_hash)}</div>
              </div>
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
