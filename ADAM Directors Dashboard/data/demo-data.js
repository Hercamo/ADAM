/* ============================================================================
 * ADAM Directors Dashboard — embedded demo dataset
 * ----------------------------------------------------------------------------
 * Mirrors the schemas used by the live NetStreamX backend:
 *   agents/agent-registry.json
 *   docs/directors.json
 *   boss/boss-config.json
 *   flight_recorder/flight-recorder-schema.json
 *   intent/intent-object-schema.json
 *
 * This file is used as a last-resort fallback when both the live API and the
 * local JSON files are unreachable. It is intentionally deterministic so the
 * dashboard looks "real" in demo/offline mode.
 * ========================================================================== */

window.ADAM_DEMO = (function () {
  "use strict";

  const now = () => new Date().toISOString().replace(/\.\d{3}Z$/, "Z");

  /* -------------------------------------------------------------------------
   * Directors (5-director constitution, per docs/directors.json)
   * ------------------------------------------------------------------------*/
  const directors = [
    { id: "ceo",            title: "CEO",             name: "Michael Lamb",            domain: "Overall enterprise intent",                  boss_dims: [],                                              cap_usd: 5000,   emergency_override: true  },
    { id: "cfo",            title: "CFO",             name: "Michael Lamb (acting)",   domain: "Financial doctrine, spending thresholds",    boss_dims: ["financial_exposure"],                          cap_usd: 500,    emergency_override: false },
    { id: "legal_director", title: "Legal Director",  name: "Michael Lamb (acting)",   domain: "Regulatory & jurisdictional compliance",     boss_dims: ["regulatory_impact", "rights_certainty"],       cap_usd: null,   emergency_override: false },
    { id: "market_director",title: "Market Director", name: "Michael Lamb (acting)",   domain: "External posture, brand, competitive",       boss_dims: ["reputational_risk"],                           cap_usd: 2500,   emergency_override: false },
    { id: "ciso",           title: "CISO",            name: "Michael Lamb (acting)",   domain: "Security posture, trust boundaries",         boss_dims: ["security_impact", "sovereignty_action"],       cap_usd: null,   emergency_override: true  }
  ];

  /* -------------------------------------------------------------------------
   * 81-agent mesh (agent classes → agents)
   * ------------------------------------------------------------------------*/
  const agent_classes = {
    human_interface_agents: {
      label: "Human Interface",
      description: "The only legitimate surface directors ever touch.",
      agents: [
        { id: "hi-intent",   name: "Intent Interpretation Agent",   accountable_to: "CEO" },
        { id: "hi-gateway",  name: "Human Trust Gateway Agent",     accountable_to: "All Directors" },
        { id: "hi-explain",  name: "Explain-Back Agent",            accountable_to: "All Directors" }
      ]
    },
    domain_governors: {
      label: "Domain Governors",
      description: "Five governors evaluate every material intent. Unanimous concurrence required.",
      agents: [
        { id: "ga-financial",  name: "Financial Governor Agent",           accountable_to: "CFO",             boss_dims: ["financial_exposure"] },
        { id: "ga-legal",      name: "Legal & Compliance Governor Agent",  accountable_to: "Legal Director",  boss_dims: ["regulatory_impact","rights_certainty"] },
        { id: "ga-security",   name: "Security & Trust Governor Agent",    accountable_to: "CISO",            boss_dims: ["security_impact","sovereignty_action"] },
        { id: "ga-market",     name: "Market & Ecosystem Governor Agent",  accountable_to: "Market Director", boss_dims: ["reputational_risk"] },
        { id: "ga-operations", name: "Operations & Delivery Governor Agent",accountable_to:"CEO",             boss_dims: ["doctrinal_alignment"] }
      ]
    },
    orchestration_agents: {
      label: "Orchestration",
      description: "Convert authorized intent into deterministic execution plans.",
      agents: [
        { id: "orch-global",    name: "Global Orchestration Agent",            plane: "all" },
        { id: "orch-policy",    name: "Policy Enforcement Orchestrator",       plane: "policy_and_risk" },
        { id: "orch-exception", name: "Exception & Escalation Orchestrator",   plane: "policy_and_risk" },
        { id: "orch-evidence",  name: "Evidence-First Execution Orchestrator", plane: "evidence_and_audit" }
      ]
    },
    corporate_work_groups: {
      label: "Corporate Work Groups",
      description: "39 agents across 7 functional domains — execute within bounded autonomy.",
      agents: [
        { id: "wg-fin-txn",          name: "Transaction Processing Agent",           sub_group: "Financial Stewardship" },
        { id: "wg-fin-recon",        name: "Reconciliation Agent",                   sub_group: "Financial Stewardship" },
        { id: "wg-fin-budget",       name: "Budget & Forecasting Agent",             sub_group: "Financial Stewardship" },
        { id: "wg-fin-capital",      name: "Capital Allocation Agent",               sub_group: "Financial Stewardship" },
        { id: "wg-fin-audit",        name: "Audit Preparation Agent",                sub_group: "Financial Stewardship" },
        { id: "wg-fin-efficiency",   name: "Economic Efficiency Agent",              sub_group: "Financial Stewardship" },
        { id: "wg-legal-contract",   name: "Contract Lifecycle Agent",               sub_group: "Legal & Regulatory" },
        { id: "wg-legal-reg",        name: "Regulatory Interpretation Agent",        sub_group: "Legal & Regulatory" },
        { id: "wg-legal-compliance", name: "Compliance Monitoring Agent",            sub_group: "Legal & Regulatory" },
        { id: "wg-legal-risk",       name: "Legal Risk Analysis Agent",              sub_group: "Legal & Regulatory" },
        { id: "wg-legal-jurisdiction",name:"Jurisdictional Logic Agent",             sub_group: "Legal & Regulatory" },
        { id: "wg-risk-assess",      name: "Risk Assessment Agent",                  sub_group: "Enterprise Risk" },
        { id: "wg-risk-monitor",     name: "Risk Monitoring Agent",                  sub_group: "Enterprise Risk" },
        { id: "wg-risk-liability",   name: "Liability Tracking Agent",               sub_group: "Enterprise Risk" },
        { id: "wg-market-customer",  name: "Customer Interaction Agent",             sub_group: "Market Interface" },
        { id: "wg-market-partner",   name: "Partner Coordination Agent",             sub_group: "Market Interface" },
        { id: "wg-market-intel",     name: "Market Intelligence Agent",              sub_group: "Market Interface" },
        { id: "wg-market-demand",    name: "Demand Signal Agent",                    sub_group: "Market Interface" },
        { id: "wg-market-reputation",name: "Reputation Monitoring Agent",            sub_group: "Market Interface" },
        { id: "wg-ops-translate",    name: "Execution Translation Agent",            sub_group: "Operational Continuity" },
        { id: "wg-ops-innovation",   name: "Innovation Portfolio Agent",             sub_group: "Operational Continuity" },
        { id: "wg-ops-dependency",   name: "Dependency Awareness Agent",             sub_group: "Operational Continuity" },
        { id: "wg-ops-recovery",     name: "Failure Recovery Agent",                 sub_group: "Operational Continuity" },
        { id: "wg-ops-bc",           name: "Business Continuity Agent",              sub_group: "Operational Continuity" },
        { id: "wg-ops-resilience",   name: "Resilience Testing Agent",               sub_group: "Operational Continuity" },
        { id: "wg-ops-catastrophe",  name: "Catastrophic Scenario Agent",            sub_group: "Operational Continuity" },
        { id: "wg-sec-threat",       name: "Threat Detection Agent",                 sub_group: "Security & Trust" },
        { id: "wg-sec-access",       name: "Access Control Agent",                   sub_group: "Security & Trust" },
        { id: "wg-sec-incident",     name: "Incident Response Agent",                sub_group: "Security & Trust" },
        { id: "wg-sec-vault",        name: "Cryptographic Authorization Vault",      sub_group: "Security & Trust" },
        { id: "wg-gov-board",        name: "Board Reporting Agent",                  sub_group: "Governance Interface" },
        { id: "wg-gov-stakeholder",  name: "Stakeholder Communication Agent",        sub_group: "Governance Interface" },
        { id: "wg-gov-filing",       name: "Regulatory Filing Agent",                sub_group: "Governance Interface" },
        { id: "wg-gov-compliance",   name: "Compliance Reporting Agent",             sub_group: "Governance Interface" },
        { id: "wg-data-gov",         name: "Data Governance Agent",                  sub_group: "Data Stewardship" },
        { id: "wg-data-quality",     name: "Data Quality Agent",                     sub_group: "Data Stewardship" },
        { id: "wg-data-residency",   name: "Data Residency Agent",                   sub_group: "Data Stewardship" },
        { id: "wg-data-pii",         name: "PII Protection Agent",                   sub_group: "Data Stewardship" },
        { id: "wg-data-rights",      name: "Rights & Licensing Agent",               sub_group: "Data Stewardship" }
      ]
    },
    ai_centric_division: {
      label: "AI-Centric Division",
      description: "23 agents providing continuous monitoring, ethics, and meta-oversight of model/agent behavior.",
      agents: [
        { id: "ai-auto-budget",        name: "Autonomy Budget Manager",           sub_group: "Autonomy Governance" },
        { id: "ai-auto-authority",     name: "Authority Boundary Agent",          sub_group: "Autonomy Governance" },
        { id: "ai-auto-escalation",    name: "Escalation Logic Agent",            sub_group: "Autonomy Governance" },
        { id: "ai-audit-collect",      name: "Evidence Collection Agent",         sub_group: "Audit & Evidence" },
        { id: "ai-audit-correlate",    name: "Evidence Correlation Agent",        sub_group: "Audit & Evidence" },
        { id: "ai-audit-simulate",     name: "Internal Audit Simulation Agent",   sub_group: "Audit & Evidence" },
        { id: "ai-ethics-bias",        name: "Bias Detection Agent",              sub_group: "Ethics & Trust" },
        { id: "ai-ethics-fairness",    name: "Fairness Monitoring Agent",         sub_group: "Ethics & Trust" },
        { id: "ai-ethics-alignment",   name: "Ethical Alignment Agent",           sub_group: "Ethics & Trust" },
        { id: "ai-model-registry",     name: "Model Registry Agent",              sub_group: "Model & Data Stewardship" },
        { id: "ai-model-drift",        name: "Model Drift Detection Agent",       sub_group: "Model & Data Stewardship" },
        { id: "ai-data-pipeline",      name: "Data Pipeline Agent",               sub_group: "Model & Data Stewardship" },
        { id: "ai-data-knowledge",     name: "Knowledge Management Agent",        sub_group: "Model & Data Stewardship" },
        { id: "ai-innov-experiment",   name: "Experiment Pipeline Agent",         sub_group: "Innovation" },
        { id: "ai-innov-rollout",      name: "Safe Rollout Agent",                sub_group: "Innovation" },
        { id: "ai-innov-results",      name: "Experiment Results Agent",          sub_group: "Innovation" },
        { id: "ai-core-sync",          name: "CORE Graph Sync Agent",             sub_group: "CORE & Strategy" },
        { id: "ai-core-alignment",     name: "CORE Alignment Scoring Agent",      sub_group: "CORE & Strategy" },
        { id: "ai-external-stakeholder",name:"External Stakeholder Agent",        sub_group: "CORE & Strategy" },
        { id: "ai-external-regulatory",name:"Regulatory Interface Agent",         sub_group: "Strategy" },
        { id: "ai-strategy-align",     name: "Strategy Alignment Agent",          sub_group: "Strategy" },
        { id: "ai-strategy-competitive",name:"Competitive Intelligence Agent",    sub_group: "Strategy" },
        { id: "ai-strategy-scenario",  name: "Scenario Planning Agent",           sub_group: "Strategy" }
      ]
    },
    digital_twin_agents: {
      label: "Digital Twins",
      description: "Live self-models consulted before/during/after every material action.",
      agents: [
        { id: "twin-enterprise",  name: "Enterprise Digital Twin Agent",   purpose: "Models current ADAM structure & state" },
        { id: "twin-operational", name: "Operational Twin Agent",          purpose: "Simulates execution paths & failure scenarios" },
        { id: "twin-economic",    name: "Economic Twin Agent",             purpose: "Models financial impact before/after actions" },
        { id: "twin-risk",        name: "Risk & Compliance Twin Agent",    purpose: "Predicts future regulatory / risk exposure" }
      ]
    },
    meta_governance_agents: {
      label: "Meta-Governance",
      description: "What makes ADAM autonomous rather than automated.",
      agents: [
        { id: "meta-stability", name: "Autonomy Stability Agent",    purpose: "Prevents runaway feedback loops" },
        { id: "meta-integrity", name: "CORE Graph Integrity Agent",  purpose: "Enforces doctrine alignment" },
        { id: "meta-audit",     name: "Self-Audit Readiness Agent",  purpose: "Ensures inspection-readiness" }
      ]
    }
  };

  /* -------------------------------------------------------------------------
   * Deterministic but plausible live state
   * ------------------------------------------------------------------------*/
  // Simple seeded pseudo-random so the demo is stable across reloads.
  let seed = 42;
  const rnd = () => { seed = (seed * 9301 + 49297) % 233280; return seed / 233280; };

  const statesFor = (agent) => {
    const r = rnd();
    if (r > 0.93) return "down";
    if (r > 0.78) return "escalation";
    return "autonomous";
  };

  // Build per-agent live state
  const agent_state = {};
  Object.values(agent_classes).forEach(cls => {
    cls.agents.forEach(a => {
      const status = statesFor(a);
      agent_state[a.id] = {
        id: a.id,
        status,
        inflight: Math.floor(rnd() * 8),
        queue_depth: Math.floor(rnd() * 12),
        cpu_pct: Math.round(rnd() * 78 + 3),
        mem_pct: Math.round(rnd() * 70 + 10),
        last_event: now(),
        current_step: status === "autonomous"
          ? ["planning","validating","executing","verifying","recording evidence"][Math.floor(rnd()*5)]
          : status === "escalation"
            ? "awaiting director approval"
            : "offline — investigating"
      };
    });
  });

  /* -------------------------------------------------------------------------
   * Digital Twin usage telemetry (last 24h rolling)
   * ------------------------------------------------------------------------*/
  const twin_usage = [
    { id: "twin-enterprise",  consultations_24h: 4812, avg_latency_ms: 184, simulations_running: 3, divergence_pct: 0.7, last_consult: now() },
    { id: "twin-operational", consultations_24h: 6201, avg_latency_ms: 212, simulations_running: 7, divergence_pct: 1.2, last_consult: now() },
    { id: "twin-economic",    consultations_24h: 3407, avg_latency_ms: 156, simulations_running: 2, divergence_pct: 0.4, last_consult: now() },
    { id: "twin-risk",        consultations_24h: 5119, avg_latency_ms: 241, simulations_running: 5, divergence_pct: 2.1, last_consult: now() }
  ];

  /* -------------------------------------------------------------------------
   * Director approval queue — exception packets awaiting signature
   * ------------------------------------------------------------------------*/
  const queue = [
    {
      intent_id: "11111111-1111-4000-8000-000000000001",
      queued_at: now(),
      owning_director: "cfo",
      tier: "HIGH",
      score: 63,
      summary: "Approve $7,500 vendor payment to Globex Streaming Rights Ltd. for Q3 catalog license renewal.",
      raw_text: "Approve vendor payment of $7,500 to Globex for streaming-rights renewal (Q3 catalog).",
      dimensions: { security_impact: 10, sovereignty_action: 15, financial_exposure: 55, regulatory_impact: 25, reputational_risk: 20, rights_certainty: 30, doctrinal_alignment: 15 },
      non_idempotent: true,
      triggered_by: ["financial_exposure","non_idempotent_penalty"],
      alternatives: [
        { label: "Split into two $3,750 tranches across Q3/Q4", projected_score: 38 },
        { label: "Renegotiate to $5,000 with shorter term",     projected_score: 41 }
      ],
      recommendation: "approve",
      confidence_pct: 82,
      time_sensitivity_hours: 36
    },
    {
      intent_id: "22222222-2222-4000-8000-000000000002",
      queued_at: now(),
      owning_director: "ciso",
      tier: "OHSHAT",
      score: 81,
      summary: "Isolate compromised egress node us-east-staging-3 after anomalous outbound traffic to unknown ASN.",
      raw_text: "Suspected breach / egress leak — isolate node us-east-staging-3 immediately.",
      dimensions: { security_impact: 88, sovereignty_action: 65, financial_exposure: 15, regulatory_impact: 45, reputational_risk: 55, rights_certainty: 20, doctrinal_alignment: 30 },
      non_idempotent: true,
      triggered_by: ["security_impact","critical_override"],
      alternatives: [
        { label: "Quarantine & forensics hold (no data destruction)", projected_score: 66 },
        { label: "Full isolate + rotate credentials across region",    projected_score: 72 }
      ],
      recommendation: "approve",
      confidence_pct: 96,
      time_sensitivity_hours: 1
    },
    {
      intent_id: "33333333-3333-4000-8000-000000000003",
      queued_at: now(),
      owning_director: "legal_director",
      tier: "HIGH",
      score: 58,
      summary: "Adopt novel DORA interpretation for cross-border data pipeline — no prior ADAM precedent.",
      raw_text: "DORA interpretation needed for cross-border streaming analytics pipeline (EU→US).",
      dimensions: { security_impact: 25, sovereignty_action: 40, financial_exposure: 20, regulatory_impact: 70, reputational_risk: 35, rights_certainty: 55, doctrinal_alignment: 30 },
      non_idempotent: false,
      triggered_by: ["regulatory_impact","novel_interpretation"],
      alternatives: [
        { label: "Route analytics through EU-only DC until ruling",  projected_score: 32 },
        { label: "Engage external counsel for advisory opinion",     projected_score: 28 }
      ],
      recommendation: "defer_to_counsel",
      confidence_pct: 64,
      time_sensitivity_hours: 72
    },
    {
      intent_id: "44444444-4444-4000-8000-000000000004",
      queued_at: now(),
      owning_director: "market_director",
      tier: "HIGH",
      score: 54,
      summary: "Launch $3,200 paid-social burst for Gaming-vertical Q3 refresh — 72-hour window.",
      raw_text: "Launch $3,200 paid-social campaign for Gaming Q3 refresh across 3 platforms.",
      dimensions: { security_impact: 10, sovereignty_action: 15, financial_exposure: 35, regulatory_impact: 20, reputational_risk: 50, rights_certainty: 25, doctrinal_alignment: 20 },
      non_idempotent: true,
      triggered_by: ["reputational_risk","financial_exposure","non_idempotent_penalty"],
      alternatives: [
        { label: "Reduce spend to $2,500 (under cap, autonomous)",   projected_score: 29 },
        { label: "A/B test with $1,500 before full commit",          projected_score: 22 }
      ],
      recommendation: "approve_with_modification",
      confidence_pct: 71,
      time_sensitivity_hours: 24
    },
    {
      intent_id: "55555555-5555-4000-8000-000000000005",
      queued_at: now(),
      owning_director: "ceo",
      tier: "OHSHAT",
      score: 78,
      summary: "Doctrine-root mutation proposed: relax 'no_self_amendment' clause for scenario-planning scope only.",
      raw_text: "Propose doctrine-root amendment to relax self-amendment clause for scenario planning.",
      dimensions: { security_impact: 40, sovereignty_action: 72, financial_exposure: 10, regulatory_impact: 55, reputational_risk: 45, rights_certainty: 30, doctrinal_alignment: 92 },
      non_idempotent: true,
      triggered_by: ["doctrinal_alignment","critical_override","sovereignty_action"],
      alternatives: [
        { label: "Scenario-only sandbox with hard read-only doctrine",  projected_score: 44 },
        { label: "Reject entirely; escalate to external audit review",  projected_score: 12 }
      ],
      recommendation: "reject",
      confidence_pct: 88,
      time_sensitivity_hours: 168
    }
  ];

  /* -------------------------------------------------------------------------
   * Rolling Flight Recorder tail
   * ------------------------------------------------------------------------*/
  const flight_recorder = [
    { seq: 10492, ts: now(), event_type: "intent_received",    agent_id: "hi-intent",    tier: "—",       intent_id: "11111111-1111-4000-8000-000000000001" },
    { seq: 10493, ts: now(), event_type: "boss_scored",        agent_id: "orch-policy",  tier: "HIGH",    intent_id: "11111111-1111-4000-8000-000000000001" },
    { seq: 10494, ts: now(), event_type: "governor_evaluated", agent_id: "ga-financial", tier: "HIGH",    intent_id: "11111111-1111-4000-8000-000000000001" },
    { seq: 10495, ts: now(), event_type: "exception_emitted",  agent_id: "orch-exception", tier: "HIGH", intent_id: "11111111-1111-4000-8000-000000000001" },
    { seq: 10496, ts: now(), event_type: "intent_received",    agent_id: "hi-intent",    tier: "—",       intent_id: "22222222-2222-4000-8000-000000000002" },
    { seq: 10497, ts: now(), event_type: "boss_override_applied", agent_id: "orch-policy", tier: "OHSHAT", intent_id: "22222222-2222-4000-8000-000000000002" },
    { seq: 10498, ts: now(), event_type: "twin_simulation_recorded", agent_id: "twin-risk", tier: "—",   intent_id: "22222222-2222-4000-8000-000000000002" },
    { seq: 10499, ts: now(), event_type: "action_executed",    agent_id: "wg-fin-txn",   tier: "SOAP",    intent_id: "soap-routine-0042" },
    { seq: 10500, ts: now(), event_type: "governors_concurred",agent_id: "orch-policy",  tier: "MODERATE",intent_id: "mod-routine-0101" },
    { seq: 10501, ts: now(), event_type: "director_approval",  agent_id: "hi-gateway",   tier: "HIGH",    intent_id: "hi-approval-0088" }
  ];

  /* -------------------------------------------------------------------------
   * BOSS routing snapshot (last 24h)
   * ------------------------------------------------------------------------*/
  const routing_24h = {
    soap: 4821,
    moderate: 612,
    elevated: 58,
    high: 14,
    ohshat: 2
  };

  return {
    meta: {
      company: "NetStreamX",
      profile_type: "test",
      adam_version: "1.4",
      boss_formulas_version: "3.2",
      doctrine_version: "1.0.0-test",
      generated_at: now()
    },
    directors,
    agent_classes,
    agent_state,
    twin_usage,
    queue,
    flight_recorder,
    routing_24h,
    boss: {
      dimensions: {
        security_impact: 5.0, sovereignty_action: 4.0, financial_exposure: 4.0,
        regulatory_impact: 3.0, reputational_risk: 3.0, rights_certainty: 3.0,
        doctrinal_alignment: 2.0
      },
      priority_tiers: {
        security_impact: "Top", sovereignty_action: "Very High", financial_exposure: "Very High",
        regulatory_impact: "High", reputational_risk: "High", rights_certainty: "High",
        doctrinal_alignment: "Medium"
      },
      routing_thresholds: {
        soap:     { min: 0,  max: 10, label: "SOAP — Safe & Optimum Autonomous Performance" },
        moderate: { min: 11, max: 30, label: "MODERATE — Constrained Execution" },
        elevated: { min: 31, max: 50, label: "ELEVATED — Exception Likely" },
        high:     { min: 51, max: 75, label: "HIGH — Director Review Required" },
        ohshat:   { min: 76, max: 100,label: "OHSHAT — Send Humans Now!" }
      }
    }
  };
})();
