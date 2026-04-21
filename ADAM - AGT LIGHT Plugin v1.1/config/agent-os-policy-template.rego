# ══════════════════════════════════════════════════════════════════════════════
# ADAM Agent OS Policy Template (Rego)
# Runtime Governance Interface — RGI-01: Policy Enforcement
# ══════════════════════════════════════════════════════════════════════════════
# This template is evaluated by AGT Agent OS at the invocation boundary
# for every agent action. Policies are sourced from the CORE Engine Rego export
# and loaded into Agent OS as Kubernetes ConfigMaps.
#
# Evaluation latency target: <0.1ms p99 (Agent OS SLA)
# Default action: deny (fail-closed)
#
# ADAM-specific: Policy rules reference CORE Engine data (doctrine, BOSS tiers,
# agent authority scope). This template represents the policy logic; actual
# policy data is generated from the DNA Tool / DNA Deployment Tool flow.
#
# Version 1.1 | April 2026 | Aligned with ADAM book v1.4
# BOSS composite tier thresholds used here (SOAP <=10, HIGH at 75, OHSHAT >75)
# match BOSS Score v3.2 canonical tier boundaries in exception-economy-config.yaml.
# Dimension weights are NOT hardcoded in this policy — the composite is supplied
# as an input by the ADAM CORE Engine.
# ══════════════════════════════════════════════════════════════════════════════

package adam.agent_os.policy

import rego.v1

# ── MANDATORY INPUTS (provided by Agent OS at invocation) ─────────────────────
# input.agent_id           string  — Agent identifier (DID or CORE Graph agent_id)
# input.action_type        string  — Type of action being evaluated
# input.tool_id            string  — Tool/resource being invoked (if applicable)
# input.target             string  — Target system/resource
# input.boss_scores        object  — Current BOSS score for this action
# input.agt_trust_score    int     — Agent Mesh trust score (0-1000)
# input.execution_ring     int     — Agent's assigned execution ring (0-3)
# input.intent_id          string  — Correlating Intent Object ID
# input.doctrine_version   string  — Doctrine version in effect

# ── MAIN DECISION ─────────────────────────────────────────────────────────────
default allow = false
default deny_reasons = []

allow if {
    count(deny_reasons) == 0
}

# Collect all deny reasons for structured logging to Flight Recorder
deny_reasons := [reason | reason := _deny_reason]

# ── RULE 1: BOSS SCORE GATE ───────────────────────────────────────────────────
# Block execution if BOSS composite score exceeds OHSHAT boundary
# Message names the offending dimension and its raw score so operators see
# *which* of the seven BOSS dimensions tripped the gate, not just the composite.
_deny_reason := msg if {
    input.boss_scores.composite > 75
    top_dim := _top_boss_dimension
    msg := sprintf("BOSS composite %.1f exceeds HIGH threshold (75). Top offending dimension: %s=%.1f. OHSHAT protocol active. Director approval required.", [
        input.boss_scores.composite,
        top_dim.name,
        top_dim.score
    ])
}

# Block SOAP execution if BOSS score exceeds SOAP boundary
_deny_reason := msg if {
    input.boss_scores.composite > 10
    input.request_autonomous_execution == true
    top_dim := _top_boss_dimension
    msg := sprintf("BOSS composite %.1f exceeds SOAP threshold (10). Top offending dimension: %s=%.1f. Autonomous execution denied. Escalation required.", [
        input.boss_scores.composite,
        top_dim.name,
        top_dim.score
    ])
}

# Helper: identify the highest-scoring dimension in the current input.
# Canonical BOSS v3.2 dimensions: security_impact, sovereignty_action,
# financial_exposure, regulatory_impact, reputational_risk, rights_certainty,
# doctrinal_alignment. Each is expected in input.boss_scores.dimensions.
_top_boss_dimension := {"name": name, "score": score} if {
    dims := input.boss_scores.dimensions
    name := [k | dims[k]; dims[k] == max({v | v := dims[_]})][0]
    score := dims[name]
}

# ── RULE 2: AGT TRUST SCORE GATE ─────────────────────────────────────────────
# Block execution if agent trust score below threshold for requested BOSS tier
_deny_reason := msg if {
    input.boss_scores.composite <= 10  # SOAP tier
    input.agt_trust_score < data.thresholds.min_trust_score_soap
    msg := sprintf("Agent trust score %d below SOAP minimum (%d). Escalation required.", [
        input.agt_trust_score,
        data.thresholds.min_trust_score_soap
    ])
}

_deny_reason := msg if {
    input.agt_trust_score < data.thresholds.agent_suspended
    msg := sprintf("Agent trust score %d below suspension threshold (%d). Agent suspended from all execution.", [
        input.agt_trust_score,
        data.thresholds.agent_suspended
    ])
}

# ── RULE 3: TOOL AUTHORISATION ────────────────────────────────────────────────
# Block tool invocations not in agent's authorized tool list (AA01, AA04)
_deny_reason := msg if {
    input.action_type == "tool_invocation"
    agent := data.agents[input.agent_id]
    not input.tool_id in agent.tools_authorized
    msg := sprintf("Tool '%s' not in agent '%s' authorized tool list. AA01/AA04 protection active.", [
        input.tool_id,
        input.agent_id
    ])
}

# ── RULE 4: EXECUTION RING ENFORCEMENT ───────────────────────────────────────
# Block cross-ring privilege escalation (AA01, AA06)
_deny_reason := msg if {
    requested_ring := data.capabilities[input.action_type].min_ring
    input.execution_ring > requested_ring  # Agent ring number HIGHER = LOWER privilege
    msg := sprintf("Ring escalation denied: agent '%s' in Ring %d cannot access Ring %d capability '%s'.", [
        input.agent_id,
        input.execution_ring,
        requested_ring,
        input.action_type
    ])
}

# ── RULE 5: DOCTRINE ALIGNMENT CHECK ─────────────────────────────────────────
# Block actions that violate CORE Engine hard rules (AA03)
_deny_reason := msg if {
    input.action_type in data.doctrine.hard_rule_protected_actions
    not action_is_authorized_by_governor(input)
    msg := sprintf("Action '%s' is protected by CORE Engine hard rule. Governor Agent approval required.", [
        input.action_type
    ])
}

action_is_authorized_by_governor(inp) if {
    token := inp.governor_approval_token
    token != null
    is_object(token)
    governor_approval_valid(token)
}

governor_approval_valid(token) if {
    # Type guard: token must be an object with intent_id string key
    is_string(token.intent_id)
    # Token verification: signature checked against Governor Agent's Ed25519 key
    # Implementation: resolved by Agent Mesh identity service
    data.governor_approvals[token.intent_id].valid == true
    data.governor_approvals[token.intent_id].expires_at > time.now_ns()
}

# ── RULE 6: INTENT DEVIATION DETECTION ───────────────────────────────────────
# Detect semantic deviation from declared Intent Object (AA03 goal hijacking)
_deny_reason := msg if {
    input.intent_id != null
    intent := data.active_intents[input.intent_id]
    not action_aligns_with_intent(input.action_type, intent.allowed_action_types)
    msg := sprintf("Action '%s' deviates from Intent Object '%s' allowed actions. Potential goal hijacking. AA03 protection active.", [
        input.action_type,
        input.intent_id
    ])
}

action_aligns_with_intent(action, allowed_actions) if {
    action in allowed_actions
}

# ── RULE 7: FINANCIAL AUTHORITY CHECK ────────────────────────────────────────
# Block financial actions exceeding agent's financial authority scope
_deny_reason := msg if {
    input.action_type == "financial_commitment"
    input.financial_amount > data.agents[input.agent_id].max_financial_authority_usd
    msg := sprintf("Financial commitment $%.2f exceeds agent '%s' authority ($%.2f). CFO Director escalation required.", [
        input.financial_amount,
        input.agent_id,
        data.agents[input.agent_id].max_financial_authority_usd
    ])
}

# ── RULE 8: SOVEREIGNTY CHECK ─────────────────────────────────────────────────
# Block data transfers that violate data residency requirements
_deny_reason := msg if {
    input.action_type == "data_transfer"
    source_region := data.regions[input.source_region].jurisdiction
    target_region := data.regions[input.target_region].jurisdiction
    not data_transfer_permitted(source_region, target_region, input.data_classification)
    msg := sprintf("Data transfer from %s (%s) to %s (%s) violates sovereignty constraints for classification '%s'.", [
        input.source_region, source_region,
        input.target_region, target_region,
        input.data_classification
    ])
}

data_transfer_permitted(source_jurisdiction, target_jurisdiction, classification) if {
    rule := data.sovereignty_rules[classification][source_jurisdiction]
    target_jurisdiction in rule.permitted_destinations
}

# ── AUDIT METADATA ────────────────────────────────────────────────────────────
# Structured metadata forwarded to RGI-04 adapter for Flight Recorder entry
audit_metadata := {
    "policy_version": data.policy_version,
    "doctrine_version": input.doctrine_version,
    "rules_evaluated": count(deny_reasons),
    "decision": allow,
    "evaluation_timestamp_ns": time.now_ns(),
    "agent_id": input.agent_id,
    "intent_id": input.intent_id,
}
