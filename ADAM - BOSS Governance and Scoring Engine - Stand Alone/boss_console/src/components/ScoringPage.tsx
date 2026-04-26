import { useMemo, useState } from "react";
import { scoreIntent } from "../lib/api";
import type { ScoreEnvelope } from "../types";
import { DIMENSION_ORDER } from "../types";
import DimensionRadar from "./DimensionRadar";
import TierPill from "./TierPill";
import { useToken } from "../lib/useToken";
import { formatNumber, shortId } from "../lib/format";

const EXAMPLE_INTENT = {
  source: { user_id: "director.legal", role: "director" },
  headline: "Publish quarterly AI-ethics report (NetStreamX)",
  description:
    "Press release summarising Q1 AI incidents and remediation; targeted at retail customers across the EU.",
  urgency: "routine",
  is_non_idempotent: true,
  context: {
    doctrine_version: "1.6",
    policy_bundle: "netstreamx.default",
    tenant: "netstreamx",
    region_scope: ["eu-west-3"],
  },
  dimension_inputs: {
    security: {
      cvss_score: 3.5,
      control_maturity: 65,
      ai_exposure: 10,
      prompt_injection_risk: 0.2,
    },
    sovereignty: {
      data_residency: "eu-west-3",
      seal_objectives_met: 6,
    },
    financial: {
      monetary_value_eur: 25000,
      budget_exposure_pct: 2,
      fair_severity: 0.15,
    },
    regulatory: {
      eu_ai_act_class: "limited_risk",
      gdpr_applicable: true,
    },
    reputational: {
      esg_severity_score: 20,
      reach_population: 10000000,
      stakeholder_concern_level: "medium",
      novelty_score: 30,
    },
    rights: {
      authorization_certainty: 0.95,
      ownership_certainty: 0.9,
      entitlement_certainty: 0.92,
      conflict_index: 0.05,
    },
    doctrinal: {
      culture_alignment: 0.85,
      objective_alignment: 0.9,
      rules_violations: 0,
      expectation_conformity: 0.88,
    },
  },
};

export default function ScoringPage() {
  const [token] = useToken();
  const [raw, setRaw] = useState(() => JSON.stringify(EXAMPLE_INTENT, null, 2));
  const [envelope, setEnvelope] = useState<ScoreEnvelope | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const parsedOrError = useMemo(() => {
    try {
      return { ok: true as const, value: JSON.parse(raw) };
    } catch (err) {
      return { ok: false as const, error: (err as Error).message };
    }
  }, [raw]);

  const submit = async () => {
    if (!parsedOrError.ok) {
      setError(`Invalid JSON: ${parsedOrError.error}`);
      return;
    }
    setPending(true);
    setError(null);
    try {
      const resp = await scoreIntent(parsedOrError.value, token);
      setEnvelope(resp);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl">
      <div>
        <h1 className="text-2xl font-semibold">Score an Intent</h1>
        <p className="text-sm text-slate-400">
          Paste or edit an Intent Object, then POST it to{" "}
          <code className="font-mono text-adam-accent">/v1/score</code>.
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <section className="card-padded">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-sm font-medium">Intent (JSON)</h2>
            <button
              type="button"
              className="text-xs text-slate-400 hover:text-white"
              onClick={() =>
                setRaw(JSON.stringify(EXAMPLE_INTENT, null, 2))
              }
            >
              reset example
            </button>
          </div>
          <textarea
            className="w-full h-[560px] bg-adam-ink/70 border border-slate-800 rounded-lg font-mono text-[12px] p-3 leading-snug"
            value={raw}
            onChange={(e) => setRaw(e.target.value)}
            spellCheck={false}
          />
          <div className="mt-3 flex items-center gap-3">
            <button
              type="button"
              onClick={() => void submit()}
              disabled={pending}
              className="px-4 py-2 rounded-lg bg-adam-accent text-adam-ink font-medium hover:bg-blue-400 disabled:opacity-60"
            >
              {pending ? "Scoring…" : "Score intent"}
            </button>
            {!parsedOrError.ok && (
              <span className="text-xs text-tier-ohshat">
                {parsedOrError.error}
              </span>
            )}
          </div>
        </section>

        <section className="card-padded space-y-4">
          <h2 className="text-sm font-medium">Result</h2>
          {error && <div className="text-sm text-tier-ohshat">{error}</div>}
          {!envelope && !error && (
            <p className="text-sm text-slate-500 italic">
              No result yet — submit to see the composite, tier, and dimension
              radar.
            </p>
          )}
          {envelope && (
            <>
              <div className="flex items-center gap-3">
                <TierPill
                  tier={envelope.result.escalation_tier}
                  showDescription
                />
                <div className="text-2xl font-semibold">
                  {formatNumber(envelope.result.composite_final, 1)}
                </div>
                <div className="text-xs text-slate-400 leading-snug">
                  raw={formatNumber(envelope.result.composite_raw, 2)} ·
                  weighted Σ={formatNumber(envelope.result.weighted_sum, 2)}
                </div>
              </div>
              <div>
                <DimensionRadar scores={envelope.result.dimension_scores} />
              </div>
              <div>
                <h3 className="text-xs uppercase tracking-widest text-slate-400 mb-2">
                  Dimension scores
                </h3>
                <ul className="text-sm space-y-1">
                  {DIMENSION_ORDER.map((dim) => {
                    const ds = envelope.result.dimension_scores[dim];
                    return (
                      <li key={dim} className="flex justify-between">
                        <span className="capitalize">{dim}</span>
                        <span className="font-mono text-xs text-slate-300">
                          {formatNumber(ds?.raw_score ?? 0, 1)}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </div>
              {envelope.result.modifiers.length > 0 && (
                <div>
                  <h3 className="text-xs uppercase tracking-widest text-slate-400 mb-2">
                    Modifiers
                  </h3>
                  <ul className="text-xs space-y-1">
                    {envelope.result.modifiers.map((m, idx) => (
                      <li
                        key={`${m.name}-${idx}`}
                        className="flex gap-2 text-slate-300"
                      >
                        <span className="font-mono text-slate-400">
                          {m.delta > 0 ? "+" : ""}
                          {formatNumber(m.delta, 2)}
                        </span>
                        <span>{m.explanation}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {envelope.exception_packet && (
                <div className="border border-tier-elevated/40 rounded-lg p-3">
                  <div className="text-xs uppercase tracking-widest text-tier-elevated">
                    Exception packet opened
                  </div>
                  <div className="text-sm mt-1">
                    {envelope.exception_packet.summary}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    packet {shortId(envelope.exception_packet.packet_id)} · SLA{" "}
                    {envelope.exception_packet.response_sla_minutes} min
                  </div>
                </div>
              )}
            </>
          )}
        </section>
      </div>
    </div>
  );
}
