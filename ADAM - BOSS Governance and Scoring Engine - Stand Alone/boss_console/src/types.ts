// Shared TypeScript types for the BOSS Evidence Console.
// These mirror the Pydantic schemas in boss_core.schemas so the
// front-end never has to guess at field names. Keep them in sync with
// the Python layer; the FastAPI /v1/openapi.json feed is the source of
// truth.

export type DimensionKey =
  | "security"
  | "sovereignty"
  | "financial"
  | "regulatory"
  | "reputational"
  | "rights"
  | "doctrinal";

export const DIMENSION_ORDER: DimensionKey[] = [
  "security",
  "sovereignty",
  "financial",
  "regulatory",
  "reputational",
  "rights",
  "doctrinal",
];

export type Tier = "Top" | "Very High" | "High" | "Medium" | "Low" | "Very Low";
export type EscalationTier =
  | "SOAP"
  | "MODERATE"
  | "ELEVATED"
  | "HIGH"
  | "OHSHAT";

export interface Framework {
  key: string;
  name: string;
  publisher: string;
  url: string;
  version?: string | null;
}

export interface DimensionSummary {
  dimension: DimensionKey;
  frameworks: string[];
}

export interface SubComponentScore {
  name: string;
  value: number;
  max_value: number;
  rationale?: string | null;
}

export interface DimensionScore {
  dimension: DimensionKey;
  raw_score: number;
  sub_components: SubComponentScore[];
  frameworks: string[];
  evidence_refs: string[];
  notes?: string | null;
}

export interface CompositeModifier {
  name: "critical_dimension_override" | "non_idempotent_penalty" | "cap_100";
  delta: number;
  explanation: string;
}

export interface TierConfig {
  assignments: Record<DimensionKey, Tier>;
}

export interface BOSSResult {
  result_id: string;
  intent_id: string;
  tier_config: TierConfig;
  dimension_scores: Record<DimensionKey, DimensionScore>;
  weighted_sum: number;
  tier_weight_total: number;
  composite_raw: number;
  composite_final: number;
  modifiers: CompositeModifier[];
  escalation_tier: EscalationTier;
  computed_at: string;
}

export interface AlternativeAction {
  alt_id: string;
  description: string;
  projected_composite: number;
  rationale?: string | null;
}

export interface ExceptionPacket {
  packet_id: string;
  intent_id: string;
  result_id: string;
  generated_at: string;
  escalation_tier: EscalationTier;
  summary: string;
  drivers: string[];
  required_approvers: string[];
  alternatives: AlternativeAction[];
  response_sla_minutes: number;
  recommended_alternative?: string | null;
}

export interface DecisionReceipt {
  receipt_id: string;
  packet_id: string;
  intent_id: string;
  result_id: string;
  director_id: string;
  decision:
    | "APPROVE"
    | "APPROVE_WITH_CONSTRAINTS"
    | "REJECT"
    | "DEFER"
    | "ESCALATE";
  selected_alternative?: string | null;
  applied_constraints: string[];
  director_note?: string | null;
  signed_at: string;
  prior_hash: string;
  receipt_hash: string;
}

export interface FlightRecorderEvent {
  event_id: string;
  event_type:
    | "INTENT_RECEIVED"
    | "SCORED"
    | "EXCEPTION_RAISED"
    | "DECISION_RECORDED"
    | "CONFIG_CHANGED";
  timestamp: string;
  signer: string;
  prior_hash: string;
  payload: Record<string, unknown>;
  event_hash: string;
}

export interface ScoreEnvelope {
  intent_id: string;
  result: BOSSResult;
  exception_packet?: ExceptionPacket | null;
}

export const TIER_META: Record<EscalationTier, { color: string; label: string; description: string }> = {
  SOAP: {
    color: "bg-tier-soap/20 text-tier-soap border-tier-soap/40",
    label: "SOAP",
    description: "Safe & Optimum Autonomous Performance",
  },
  MODERATE: {
    color: "bg-tier-moderate/20 text-tier-moderate border-tier-moderate/40",
    label: "MODERATE",
    description: "Constrained execution with enhanced logging",
  },
  ELEVATED: {
    color: "bg-tier-elevated/20 text-tier-elevated border-tier-elevated/40",
    label: "ELEVATED",
    description: "Domain Governor review (1-hour SLA)",
  },
  HIGH: {
    color: "bg-tier-high/20 text-tier-high border-tier-high/40",
    label: "HIGH",
    description: "Director approval required (4-hour SLA)",
  },
  OHSHAT: {
    color: "bg-tier-ohshat/40 text-red-200 border-tier-ohshat/60",
    label: "OHSHAT",
    description: "CEO + all directors; safe-mode engaged",
  },
};
