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
# Version 1.2 | April 2026 | Aligned with ADAM book v1.7
# BOSS composite tier thresholds used here (SOAP <=10, HIGH at 75, OHSHAT >75)
# match BOSS Score v3.3 canonical tier boundaries in exception-economy-config.yaml.
# Dimension weights are NOT hardcoded in this policy — the composite is supplied
# as an input by the ADAM CORE Engine.
#
# ──────────────────────────────────────────────────────────────────────────────
# REGO AUTHORING DISCIPLINE — REQUIRED READING BEFORE EDITING
# ──────────────────────────────────────────────────────────────────────────────
# • This module REQUIRES Rego v1 (`import rego.v1` below). The OPA process
#   MUST be invoked with `--v1-compatible`. See README and the AGT Light
#   Helm values (`deployment/agt-light-helm-values.yaml`) for the canonical
#   command-line.
# • DO NOT downgrade to `import future.keywords.in` — audit log Section 0210
#   documents seven distinct grammar booby-traps that v0 mode hits.
# • DO NOT replace any `_top_boss_dimension`-style helper with an inline
#   comprehension that uses `max({v | v := dims[_]})`. The bare-reference
#   comprehension body confuses the type checker into reading `|` as set-union
#   (audit log 0210.E). The helper below uses an explicit unrolled approach
#   over the canonical 7 dimensions.
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
default allow := false

allow if count(deny_reasons) == 0

# Collect all deny reasons for structured logging to Flight Recorder.
# Use a partial set rule to aggregate — each `_deny_reason` clause that fires
# contributes one element. This is the canonical Rego v1 idiom.
deny_reasons contains reason if {
	reason := _bosses_composite_ohshat
}

deny_reasons contains reason if {
	reason := _bosses_composite_soap_violation
}

deny_reasons contains reason if {
	reason := _agt_trust_below_soap
}

deny_reasons contains reason if {
	reason := _agt_trust_suspended
}

deny_reasons contains reason if {
	reason := _tool_not_authorized
}

deny_reasons contains reason if {
	reason := _ring_escalation
}

deny_reasons contains reason if {
	reason := _doctrine_hard_rule
}

deny_reasons contains reason if {
	reason := _intent_deviation
}

deny_reasons contains reason if {
	reason := _financial_authority_exceeded
}

deny_reasons contains reason if {
	reason := _sovereignty_violation
}

# ── RULE 1: BOSS SCORE GATE ───────────────────────────────────────────────────
# Block execution if BOSS composite score exceeds OHSHAT boundary.
_bosses_composite_ohshat := msg if {
	input.boss_scores.composite > 75
	top_dim := _top_boss_dimension
	msg := sprintf(
		"BOSS composite %.1f exceeds HIGH threshold (75). Top offending dimension: %s=%.1f. OHSHAT protocol active. Director approval required.",
		[input.boss_scores.composite, top_dim.name, top_dim.score],
	)
}

# Block SOAP execution if BOSS score exceeds SOAP boundary.
_bosses_composite_soap_violation := msg if {
	input.boss_scores.composite > 10
	input.request_autonomous_execution == true
	top_dim := _top_boss_dimension
	msg := sprintf(
		"BOSS composite %.1f exceeds SOAP threshold (10). Top offending dimension: %s=%.1f. Autonomous execution denied. Escalation required.",
		[input.boss_scores.composite, top_dim.name, top_dim.score],
	)
}

# Helper: identify the highest-scoring dimension. Unrolled over the canonical
# 7 BOSS v3.3 dimensions for type-checker safety. If a dimension is missing
# from input, it defaults to 0 (via the `_dim_value` accessor) so the helper
# never returns undefined.
_top_boss_dimension := pick if {
	all_dims := [
		{"name": "security_impact", "score": _dim_value("security_impact")},
		{"name": "sovereignty_action", "score": _dim_value("sovereignty_action")},
		{"name": "financial_exposure", "score": _dim_value("financial_exposure")},
		{"name": "regulatory_impact", "score": _dim_value("regulatory_impact")},
		{"name": "reputational_risk", "score": _dim_value("reputational_risk")},
		{"name": "rights_certainty", "score": _dim_value("rights_certainty")},
		{"name": "doctrinal_alignment", "score": _dim_value("doctrinal_alignment")},
	]
	max_score := max([d.score | some d in all_dims])
	pick := [d | some d in all_dims; d.score == max_score][0]
}

_dim_value(name) := v if {
	v := input.boss_scores.dimensions[name]
} else := 0

# ── RULE 2: AGT TRUST SCORE GATE ─────────────────────────────────────────────
_agt_trust_below_soap := msg if {
	input.boss_scores.composite <= 10
	input.agt_trust_score < data.thresholds.min_trust_score_soap
	msg := sprintf(
		"Agent trust score %d below SOAP minimum (%d). Escalation required.",
		[input.agt_trust_score, data.thresholds.min_trust_score_soap],
	)
}

_agt_trust_suspended := msg if {
	input.agt_trust_score < data.thresholds.agent_suspended
	msg := sprintf(
		"Agent trust score %d below suspension threshold (%d). Agent suspended from all execution.",
		[input.agt_trust_score, data.thresholds.agent_suspended],
	)
}

# ── RULE 3: TOOL AUTHORISATION ────────────────────────────────────────────────
_tool_not_authorized := msg if {
	input.action_type == "tool_invocation"
	agent := data.agents[input.agent_id]
	not _tool_in_authorized(input.tool_id, agent.tools_authorized)
	msg := sprintf(
		"Tool '%s' not in agent '%s' authorized tool list. AA01/AA04 protection active.",
		[input.tool_id, input.agent_id],
	)
}

_tool_in_authorized(tool, authorized) if {
	some t in authorized
	t == tool
}

# ── RULE 4: EXECUTION RING ENFORCEMENT ───────────────────────────────────────
_ring_escalation := msg if {
	requested_ring := data.capabilities[input.action_type].min_ring
	input.execution_ring > requested_ring
	msg := sprintf(
		"Ring escalation denied: agent '%s' in Ring %d cannot access Ring %d capability '%s'.",
		[input.agent_id, input.execution_ring, requested_ring, input.action_type],
	)
}

# ── RULE 5: DOCTRINE ALIGNMENT CHECK ─────────────────────────────────────────
_doctrine_hard_rule := msg if {
	_action_in_protected(input.action_type, data.doctrine.hard_rule_protected_actions)
	not action_is_authorized_by_governor(input)
	msg := sprintf(
		"Action '%s' is protected by CORE Engine hard rule. Governor Agent approval required.",
		[input.action_type],
	)
}

_action_in_protected(action, protected) if {
	some p in protected
	p == action
}

action_is_authorized_by_governor(inp) if {
	token := inp.governor_approval_token
	token != null
	is_object(token)
	governor_approval_valid(token)
}

governor_approval_valid(token) if {
	is_string(token.intent_id)
	data.governor_approvals[token.intent_id].valid == true
	data.governor_approvals[token.intent_id].expires_at > time.now_ns()
}

# ── RULE 6: INTENT DEVIATION DETECTION ───────────────────────────────────────
_intent_deviation := msg if {
	input.intent_id != null
	intent := data.active_intents[input.intent_id]
	not action_aligns_with_intent(input.action_type, intent.allowed_action_types)
	msg := sprintf(
		"Action '%s' deviates from Intent Object '%s' allowed actions. Potential goal hijacking. AA03 protection active.",
		[input.action_type, input.intent_id],
	)
}

action_aligns_with_intent(action, allowed_actions) if {
	some a in allowed_actions
	a == action
}

# ── RULE 7: FINANCIAL AUTHORITY CHECK ────────────────────────────────────────
_financial_authority_exceeded := msg if {
	input.action_type == "financial_commitment"
	input.financial_amount > data.agents[input.agent_id].max_financial_authority_usd
	msg := sprintf(
		"Financial commitment $%.2f exceeds agent '%s' authority ($%.2f). CFO Director escalation required.",
		[
			input.financial_amount, input.agent_id,
			data.agents[input.agent_id].max_financial_authority_usd,
		],
	)
}

# ── RULE 8: SOVEREIGNTY CHECK ─────────────────────────────────────────────────
_sovereignty_violation := msg if {
	input.action_type == "data_transfer"
	source_region := data.regions[input.source_region].jurisdiction
	target_region := data.regions[input.target_region].jurisdiction
	not data_transfer_permitted(source_region, target_region, input.data_classification)
	msg := sprintf(
		"Data transfer from %s (%s) to %s (%s) violates sovereignty constraints for classification '%s'.",
		[
			input.source_region, source_region, input.target_region, target_region,
			input.data_classification,
		],
	)
}

data_transfer_permitted(source_jurisdiction, target_jurisdiction, classification) if {
	rule := data.sovereignty_rules[classification][source_jurisdiction]
	some d in rule.permitted_destinations
	d == target_jurisdiction
}

# ── AUDIT METADATA ────────────────────────────────────────────────────────────
audit_metadata := {
	"policy_version": data.policy_version,
	"doctrine_version": input.doctrine_version,
	"rules_evaluated": count(deny_reasons),
	"decision": allow,
	"evaluation_timestamp_ns": time.now_ns(),
	"agent_id": input.agent_id,
	"intent_id": input.intent_id,
}
