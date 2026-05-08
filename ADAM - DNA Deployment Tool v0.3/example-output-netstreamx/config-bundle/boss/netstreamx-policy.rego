# ============================================================
# ADAM DNA Deployment Specification — Company Hard-Rule Bundle
# Platform: ADAM Configuration Bundle (Platform-Agnostic)
# Company: NetStreamX
# Generated: 2026-04-26
# ADAM Version: 1.7 | DNA Questionnaire Version: 1.1 | BOSS Formulas: v3.3
# ============================================================
# Encodes the 8 NetStreamX hard rules (R1–R8) as OPA `deny` blocks.
# R2, R6, R7 are enforced in-agent (orchestration-layer behaviour) rather
# than as OPA deny rules; the remaining R1, R3, R4, R5, R8 live here.
# Composite `allow` returns true when no deny rule fires.
#
# ──────────────────────────────────────────────────────────────────────────────
# REGO AUTHORING DISCIPLINE — REQUIRED READING BEFORE EDITING THIS FILE
# ──────────────────────────────────────────────────────────────────────────────
# This module REQUIRES OPA Rego v1 grammar (`import rego.v1`) and the OPA
# process MUST be invoked with `--v1-compatible`. See sibling boss-routing.rego
# for the full discipline note and audit-log cross-references.
#
# Rules of thumb that future maintainers MUST respect:
#   • R3 (autonomy budget) MUST negate a fully-bound HELPER rule, never an
#     iteration variable directly. Audit log Section 0210.D documents the
#     unsafe-var defect this prevents.
#   • R4 (PII residency) MUST use ARRAY tuples for the allow-list, NOT sets
#     of two strings. `{"US","us-east"}` is parsed as an unordered set and
#     matches the reverse pair, silently breaking directionality. Use
#     `["US","us-east"]` instead. Audit log Section 0210 / B2.
# ──────────────────────────────────────────────────────────────────────────────

package adam.netstreamx

import rego.v1

# ──────────────────────────────────────────────────────────────────────────────
# Configuration constants
# ──────────────────────────────────────────────────────────────────────────────

# OFAC + EU sanctions allow-list (DENY pattern uses set membership).
sanctioned_counterparties := {
	"OFAC-SDN-001",
	"OFAC-SDN-002",
	"EU-SANC-NK-001",
	"EU-SANC-IR-001",
	"EU-SANC-RU-001",
}

# Per-transaction autonomous cap (USD). Above this requires director approval.
per_txn_cap_usd := 500.0

# PII residency allow-list — ARRAYS, not sets (directional pairs).
# `[subject_jurisdiction, destination_region]`. See discipline note above.
residency_allowed_pairs := {
	["US", "us-east"],
	["US", "us-west"],
	["NL", "eu-west"],
	["DE", "eu-central"],
	["FR", "eu-west"],
	["GB", "uk-south"],
}

# ──────────────────────────────────────────────────────────────────────────────
# R1 — Sanctions screening (deny intents naming a sanctioned counterparty).
# ──────────────────────────────────────────────────────────────────────────────
deny contains msg if {
	some outcome in input.intent.desired_outcomes
	some c in outcome.counterparties
	sanctioned_counterparties[c]
	msg := sprintf("R1 violation: counterparty '%s' is on sanctions list", [c])
}

# ──────────────────────────────────────────────────────────────────────────────
# R3 — Autonomy budget cap (deny over-cap intents lacking director approval).
# ──────────────────────────────────────────────────────────────────────────────
# Negation of HELPER rule, not of an iteration variable. Audit log 0210.D.
deny contains msg if {
	input.intent.financial_amount_usd > per_txn_cap_usd
	not has_director_approval
	msg := sprintf(
		"R3 violation: amount $%.2f exceeds per-txn cap $%.2f without director approval",
		[input.intent.financial_amount_usd, per_txn_cap_usd],
	)
}

has_director_approval if {
	some condition in input.intent.approval_conditions
	condition.approval == "director"
}

# ──────────────────────────────────────────────────────────────────────────────
# R4 — PII residency (deny PII transfers to disallowed jurisdiction pairs).
# ──────────────────────────────────────────────────────────────────────────────
# Directional check via ARRAY pair, not set. Audit log 0210 / B2.
deny contains msg if {
	input.intent.data_transfer.contains_pii
	pair := [
		input.intent.data_transfer.subject_jurisdiction,
		input.intent.data_transfer.destination_region,
	]
	not residency_allowed_pairs[pair]
	msg := sprintf(
		"R4 violation: PII transfer %s → %s not in allowed residency pairs",
		[
			input.intent.data_transfer.subject_jurisdiction,
			input.intent.data_transfer.destination_region,
		],
	)
}

# ──────────────────────────────────────────────────────────────────────────────
# R5 — Doctrine mutation requires director (deny non-director doctrine writes).
# ──────────────────────────────────────────────────────────────────────────────
deny contains msg if {
	input.intent.action.type == "mutate"
	input.intent.action.domain == "doctrine"
	input.intent.source.role != "director"
	msg := "R5 violation: doctrine mutation requires director role"
}

# ──────────────────────────────────────────────────────────────────────────────
# R8 — Idempotency key required on all mutating actions.
# ──────────────────────────────────────────────────────────────────────────────
deny contains msg if {
	input.intent.action.type == "mutate"
	not input.intent.idempotency_key
	msg := "R8 violation: mutating action missing idempotency_key"
}

# ──────────────────────────────────────────────────────────────────────────────
# Composite allow — true when no deny rule fired.
# ──────────────────────────────────────────────────────────────────────────────
default allow := false

allow if count(deny) == 0
