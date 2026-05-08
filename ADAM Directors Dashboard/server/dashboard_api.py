#!/usr/bin/env python3
"""
ADAM Directors Dashboard API (v0.2 — production-grade)
======================================================

This module is the *server side* of the upgraded Directors Dashboard.
It is a Flask Blueprint that mounts under ``/api/dashboard`` on the
NetStreamX customer backend.  It is the single entry point the
front-end uses for everything: bootstrap config, live mesh state,
demo state, agent cards, intent-object cards, and the director
action workflows (approve / reject / modify / deny / comment plus
agent control: start / restart / diagnose).

Doctrine alignment (ADAM Book New)
----------------------------------
* The Flight Recorder chain is **append-only**.  Director actions
  become FR events, never edits.  We therefore implement
  idempotency by writing a deterministic ``action_id`` into every
  director event and refusing to write a second event with the
  same ``action_id``.  The first call wins; subsequent calls
  return the original outcome — i.e. classic POST-Once-Exactly.
* Doctrine never self-amends.  The director's COMMENT and
  WHAT-IF analyses are recorded as evidence on FR events, not as
  modifications to the doctrine seed.
* Software-HSM only (no blockchain) — we delegate signing to the
  Flight Recorder which already wraps the HSM.
* Sovereign-local: every read is from local services; demo mode
  is a server-rendered fixture so the UI never fakes data
  silently.
* Director constitution: 5 mandatory + 2 optional (CPO active,
  CTO included as planned-active).  CEO and CISO have full mesh
  visibility and full edit rights; the others are scoped to their
  domain agents.  Any director may *view* any dashboard.
* test_proxy_mode honoured: every director action is also stamped
  with the natural person actually signing (Michael Lamb in this
  test instance) and emits a ``director_proxy_acting`` event.

Endpoints
---------
GET  /api/dashboard/bootstrap                       static configuration
GET  /api/dashboard/state?mode=live|demo&dir=<id>   normalised dashboard model
GET  /api/dashboard/agents                          full agent list w/ state
GET  /api/dashboard/agent/<agent_id>?mode=...       agent-card payload
POST /api/dashboard/agent/<agent_id>/control        agent control (start/restart/diagnose)
GET  /api/dashboard/intent/<intent_id>?mode=...     intent-card payload
POST /api/dashboard/intent/<intent_id>/decision     director action (approve/reject/...)
GET  /api/dashboard/intents                         all intents seen so far
GET  /api/dashboard/director/<id>/scope             agent IDs visible to that director
GET  /api/dashboard/health                          health probe of the dashboard API
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

import requests
from flask import Blueprint, jsonify, request, send_from_directory


# ---------------------------------------------------------------------------
#  Configuration (matches netstreamx_app.py environment contract)
# ---------------------------------------------------------------------------

EXC_URL          = os.environ.get("EXC_URL",       "http://exception-router:8220")
FR_URL           = os.environ.get("FR_URL",        "http://flight-recorder:8200")
INTERFACE_URL    = os.environ.get("INTERFACE_URL", "http://interface-agents:8300")
BOSS_URL         = os.environ.get("BOSS_URL",      "http://boss-scorer:8210")
DOCTRINE_VERSION = os.environ.get("DOCTRINE_VERSION", "1.1.0-test")

# Locate registry / directors / boss config relative to the deployment tree.
# The blueprint loads them once at startup and refreshes on the bootstrap
# endpoint.  Search order mirrors the rest of the production stack so the
# dashboard remains drop-in-compatible with both the docker layout
# (/app/...) and the source-tree layout used by RunADAM.bat.
_HERE = Path(__file__).resolve().parent
_DEPLOY = _HERE.parent
_CANDIDATE_PATHS = {
    "directors": [
        Path("/app/governance/directors.json"),
        _DEPLOY / "docs" / "directors.json",
        _DEPLOY / "iac" / "generated" / "config-bundle" / "governance" / "directors.json",
    ],
    "agents": [
        Path("/app/agents/agent-registry.json"),
        _DEPLOY / "agents" / "agent-registry.json",
        _DEPLOY / "iac" / "generated" / "config-bundle" / "agents" / "agent-registry.json",
    ],
    "boss": [
        Path("/app/boss/boss-config.json"),
        _DEPLOY / "boss" / "boss-config.json",
        _DEPLOY / "iac" / "generated" / "config-bundle" / "boss" / "boss-config.json",
    ],
}


def _load_first(kind: str) -> dict:
    for p in _CANDIDATE_PATHS[kind]:
        try:
            if p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            continue
    return {}


# ---------------------------------------------------------------------------
#  Director scope rules
# ---------------------------------------------------------------------------
#
#  Per the user's brief: CEO and CISO see all 81 agents; the other directors
#  see only their domain agents (governor, work-group, AI-centric and any
#  meta/twin agents that support their function).  Every director can VIEW
#  every dashboard, but only EDIT their own scope.  CEO and CISO can edit any.
#
#  "Scope" is expressed as a list of agent-id prefixes plus explicit ids.
#  The membership check is: an agent is in scope if any prefix matches OR
#  if the explicit id list contains it OR if the director is CEO/CISO.

_DIRECTOR_SCOPES: dict[str, dict] = {
    "ceo": {
        "prefixes": ["*"],
        "explicit": [],
        "edit_all": True,
    },
    "ciso": {
        "prefixes": ["*"],
        "explicit": [],
        "edit_all": True,
    },
    "cfo": {
        "prefixes": ["hi-", "ga-financial", "orch-", "wg-fin-", "ai-audit-", "ai-auto-budget", "meta-", "twin-"],
        "explicit": ["ga-operations"],
        "edit_all": False,
    },
    "legal_director": {
        "prefixes": ["hi-", "ga-legal", "orch-", "wg-legal-", "ai-ethics-", "meta-", "twin-"],
        "explicit": ["wg-data-pii", "wg-data-rights", "wg-data-residency", "wg-gov-filing", "wg-gov-compliance"],
        "edit_all": False,
    },
    "market_director": {
        "prefixes": ["hi-", "ga-market", "orch-", "wg-market-", "meta-", "twin-"],
        "explicit": ["wg-gov-stakeholder", "ai-strategy-competitive", "ai-external-stakeholder", "ai-external-regulatory"],
        "edit_all": False,
    },
    "cpo": {
        "prefixes": ["hi-", "ga-operations", "orch-", "wg-ops-", "ai-innov-", "ai-strategy-", "meta-", "twin-"],
        "explicit": ["wg-fin-budget", "wg-fin-capital"],
        "edit_all": False,
    },
    "cto": {
        "prefixes": ["hi-", "ga-operations", "orch-", "wg-data-", "wg-sec-vault", "ai-model-", "ai-data-", "ai-core-", "meta-", "twin-"],
        "explicit": ["ga-security"],
        "edit_all": False,
    },
}


def _agent_in_scope(agent_id: str, director_id: str) -> bool:
    rules = _DIRECTOR_SCOPES.get(director_id) or _DIRECTOR_SCOPES["ceo"]
    if rules.get("edit_all") or "*" in rules.get("prefixes", []):
        return True
    if agent_id in rules.get("explicit", []):
        return True
    for pref in rules.get("prefixes", []):
        if agent_id.startswith(pref):
            return True
    return False


def _can_edit(director_id_acting: str, target_director_id: str) -> bool:
    if not director_id_acting:
        return False
    if director_id_acting in ("ceo", "ciso"):
        return True
    return director_id_acting == target_director_id


# ---------------------------------------------------------------------------
#  Demo dataset (server-side, deterministic)
# ---------------------------------------------------------------------------
#  The front-end demo dataset (data/demo-data.js) is the *contract* — this
#  function returns the same shape from the server so a director toggling
#  LIVE→DEMO at runtime gets a dataset rendered through the same code path.

def _demo_state() -> dict:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return {
        "meta": {
            "company": "NetStreamX",
            "profile_type": "test",
            "adam_version": "1.4",
            "boss_formulas_version": "3.2",
            "doctrine_version": DOCTRINE_VERSION,
            "generated_at": now,
            "mode": "demo",
        },
        "directors": _DEFAULT_DIRECTORS,
        "agent_classes": _DEFAULT_AGENT_CLASSES,
        "agent_state": _synthetic_agent_state(),
        "twin_usage": [
            {"id": "twin-enterprise",  "consultations_24h": 4812, "avg_latency_ms": 184, "simulations_running": 3, "divergence_pct": 0.7},
            {"id": "twin-operational", "consultations_24h": 6201, "avg_latency_ms": 212, "simulations_running": 7, "divergence_pct": 1.2},
            {"id": "twin-economic",    "consultations_24h": 3407, "avg_latency_ms": 156, "simulations_running": 2, "divergence_pct": 0.4},
            {"id": "twin-risk",        "consultations_24h": 5119, "avg_latency_ms": 241, "simulations_running": 5, "divergence_pct": 2.1},
        ],
        "queue": _DEMO_QUEUE,
        "flight_recorder": _DEMO_FR_TAIL,
        "routing_24h": {"soap": 4821, "moderate": 612, "elevated": 58, "high": 14, "ohshat": 2},
        "boss": _DEFAULT_BOSS,
    }


# Static defaults loaded once and cached.  These are derived from the live
# config files when present, but ship with sensible defaults so the dashboard
# boots even on a brand-new sovereign install.

_DEFAULT_DIRECTORS = [
    {"id": "ceo",             "title": "CEO",             "name": "Michael Lamb",          "domain": "Overall enterprise intent",                  "boss_dims": [],                                          "cap_usd": 5000, "emergency_override": True,  "active": True,  "edit_all": True},
    {"id": "cfo",             "title": "CFO",             "name": "Michael Lamb (acting)", "domain": "Financial doctrine, spending thresholds",    "boss_dims": ["financial_exposure"],                       "cap_usd": 500,  "emergency_override": False, "active": True,  "edit_all": False},
    {"id": "legal_director",  "title": "Legal Director",  "name": "Michael Lamb (acting)", "domain": "Regulatory & jurisdictional compliance",     "boss_dims": ["regulatory_impact", "rights_certainty"],   "cap_usd": None, "emergency_override": False, "active": True,  "edit_all": False},
    {"id": "market_director", "title": "Market Director", "name": "Michael Lamb (acting)", "domain": "External posture, brand, competitive",       "boss_dims": ["reputational_risk"],                        "cap_usd": 2500, "emergency_override": False, "active": True,  "edit_all": False},
    {"id": "ciso",            "title": "CISO",            "name": "Michael Lamb (acting)", "domain": "Security posture, trust boundaries",         "boss_dims": ["security_impact", "sovereignty_action"],   "cap_usd": None, "emergency_override": True,  "active": True,  "edit_all": True},
    {"id": "cpo",             "title": "CPO",             "name": "Michael Lamb (acting)", "domain": "Product & innovation, autonomy budget",      "boss_dims": ["doctrinal_alignment"],                      "cap_usd": 2000, "emergency_override": False, "active": True,  "edit_all": False},
    {"id": "cto",             "title": "CTO",             "name": "Michael Lamb (acting)", "domain": "Technology stewardship, model & data lifecycle", "boss_dims": [],                                       "cap_usd": 1000, "emergency_override": False, "active": True,  "edit_all": False},
]

_DEFAULT_BOSS = {
    "dimensions": {
        "security_impact": 5.0, "sovereignty_action": 4.0, "financial_exposure": 4.0,
        "regulatory_impact": 3.0, "reputational_risk": 3.0, "rights_certainty": 3.0,
        "doctrinal_alignment": 2.0,
    },
    "routing_thresholds": {
        "soap":     {"min": 0,  "max": 10, "label": "SOAP — Safe & Optimum Autonomous Performance"},
        "moderate": {"min": 11, "max": 30, "label": "MODERATE — Constrained Execution"},
        "elevated": {"min": 31, "max": 50, "label": "ELEVATED — Exception Likely"},
        "high":     {"min": 51, "max": 75, "label": "HIGH — Director Review Required"},
        "ohshat":   {"min": 76, "max": 100,"label": "OHSHAT — Send Humans Now!"},
    },
}


def _humanize(s: str) -> str:
    return " ".join(w.capitalize() for w in s.split("_"))


def _build_agent_classes_from_registry(reg: dict) -> dict:
    out: dict = {}
    for k, v in (reg.get("agent_classes") or {}).items():
        out[k] = {
            "label": _humanize(k),
            "description": v.get("description", ""),
            "agents": v.get("agents", []),
        }
    return out


# Initial defaults — the full 81-agent NetStreamX mesh expressed as a fallback
# so the dashboard works even when the registry file is absent (which is also
# how the addon ships when dropped into a fresh ADAM host).
_DEFAULT_AGENT_CLASSES: dict[str, dict] = {
    "human_interface_agents": {
        "label": "Human Interface",
        "description": "The only legitimate surface directors ever touch.",
        "agents": [
            {"id": "hi-intent",  "name": "Intent Interpretation Agent",  "accountable_to": "CEO"},
            {"id": "hi-gateway", "name": "Human Trust Gateway Agent",    "accountable_to": "All Directors"},
            {"id": "hi-explain", "name": "Explain-Back Agent",           "accountable_to": "All Directors"},
        ],
    },
    "domain_governors": {
        "label": "Domain Governors",
        "description": "Five governors evaluate every material intent. Unanimous concurrence required.",
        "agents": [
            {"id": "ga-financial",  "name": "Financial Governor Agent",            "accountable_to": "CFO",             "boss_dims": ["financial_exposure"]},
            {"id": "ga-legal",      "name": "Legal & Compliance Governor Agent",   "accountable_to": "Legal Director",  "boss_dims": ["regulatory_impact","rights_certainty"]},
            {"id": "ga-security",   "name": "Security & Trust Governor Agent",     "accountable_to": "CISO",            "boss_dims": ["security_impact","sovereignty_action"]},
            {"id": "ga-market",     "name": "Market & Ecosystem Governor Agent",   "accountable_to": "Market Director", "boss_dims": ["reputational_risk"]},
            {"id": "ga-operations", "name": "Operations & Delivery Governor Agent","accountable_to": "CEO",             "boss_dims": ["doctrinal_alignment"]},
        ],
    },
    "orchestration_agents": {
        "label": "Orchestration",
        "description": "Convert authorized intent into deterministic execution plans.",
        "agents": [
            {"id": "orch-global",    "name": "Global Orchestration Agent",            "plane": "all"},
            {"id": "orch-policy",    "name": "Policy Enforcement Orchestrator",       "plane": "policy_and_risk"},
            {"id": "orch-exception", "name": "Exception & Escalation Orchestrator",   "plane": "policy_and_risk"},
            {"id": "orch-evidence",  "name": "Evidence-First Execution Orchestrator", "plane": "evidence_and_audit"},
        ],
    },
    "corporate_work_groups": {
        "label": "Corporate Work Groups",
        "description": "39 agents across 7 functional domains.",
        "agents": [
            {"id": "wg-fin-txn",          "name": "Transaction Processing Agent",      "sub_group": "Financial Stewardship"},
            {"id": "wg-fin-recon",        "name": "Reconciliation Agent",              "sub_group": "Financial Stewardship"},
            {"id": "wg-fin-budget",       "name": "Budget & Forecasting Agent",        "sub_group": "Financial Stewardship"},
            {"id": "wg-fin-capital",      "name": "Capital Allocation Agent",          "sub_group": "Financial Stewardship"},
            {"id": "wg-fin-audit",        "name": "Audit Preparation Agent",           "sub_group": "Financial Stewardship"},
            {"id": "wg-fin-efficiency",   "name": "Economic Efficiency Agent",         "sub_group": "Financial Stewardship"},
            {"id": "wg-legal-contract",   "name": "Contract Lifecycle Agent",          "sub_group": "Legal & Regulatory"},
            {"id": "wg-legal-reg",        "name": "Regulatory Interpretation Agent",   "sub_group": "Legal & Regulatory"},
            {"id": "wg-legal-compliance", "name": "Compliance Monitoring Agent",       "sub_group": "Legal & Regulatory"},
            {"id": "wg-legal-risk",       "name": "Legal Risk Analysis Agent",         "sub_group": "Legal & Regulatory"},
            {"id": "wg-legal-jurisdiction","name":"Jurisdictional Logic Agent",        "sub_group": "Legal & Regulatory"},
            {"id": "wg-risk-assess",      "name": "Risk Assessment Agent",             "sub_group": "Enterprise Risk"},
            {"id": "wg-risk-monitor",     "name": "Risk Monitoring Agent",             "sub_group": "Enterprise Risk"},
            {"id": "wg-risk-liability",   "name": "Liability Tracking Agent",          "sub_group": "Enterprise Risk"},
            {"id": "wg-market-customer",  "name": "Customer Interaction Agent",        "sub_group": "Market Interface"},
            {"id": "wg-market-partner",   "name": "Partner Coordination Agent",        "sub_group": "Market Interface"},
            {"id": "wg-market-intel",     "name": "Market Intelligence Agent",         "sub_group": "Market Interface"},
            {"id": "wg-market-demand",    "name": "Demand Signal Agent",               "sub_group": "Market Interface"},
            {"id": "wg-market-reputation","name": "Reputation Monitoring Agent",       "sub_group": "Market Interface"},
            {"id": "wg-ops-translate",    "name": "Execution Translation Agent",       "sub_group": "Operational Continuity"},
            {"id": "wg-ops-innovation",   "name": "Innovation Portfolio Agent",        "sub_group": "Operational Continuity"},
            {"id": "wg-ops-dependency",   "name": "Dependency Awareness Agent",        "sub_group": "Operational Continuity"},
            {"id": "wg-ops-recovery",     "name": "Failure Recovery Agent",            "sub_group": "Operational Continuity"},
            {"id": "wg-ops-bc",           "name": "Business Continuity Agent",         "sub_group": "Operational Continuity"},
            {"id": "wg-ops-resilience",   "name": "Resilience Testing Agent",          "sub_group": "Operational Continuity"},
            {"id": "wg-ops-catastrophe",  "name": "Catastrophic Scenario Agent",       "sub_group": "Operational Continuity"},
            {"id": "wg-sec-threat",       "name": "Threat Detection Agent",            "sub_group": "Security & Trust"},
            {"id": "wg-sec-access",       "name": "Access Control Agent",              "sub_group": "Security & Trust"},
            {"id": "wg-sec-incident",     "name": "Incident Response Agent",           "sub_group": "Security & Trust"},
            {"id": "wg-sec-vault",        "name": "Cryptographic Authorization Vault", "sub_group": "Security & Trust"},
            {"id": "wg-gov-board",        "name": "Board Reporting Agent",             "sub_group": "Governance Interface"},
            {"id": "wg-gov-stakeholder",  "name": "Stakeholder Communication Agent",   "sub_group": "Governance Interface"},
            {"id": "wg-gov-filing",       "name": "Regulatory Filing Agent",           "sub_group": "Governance Interface"},
            {"id": "wg-gov-compliance",   "name": "Compliance Reporting Agent",        "sub_group": "Governance Interface"},
            {"id": "wg-data-gov",         "name": "Data Governance Agent",             "sub_group": "Data Stewardship"},
            {"id": "wg-data-quality",     "name": "Data Quality Agent",                "sub_group": "Data Stewardship"},
            {"id": "wg-data-residency",   "name": "Data Residency Agent",              "sub_group": "Data Stewardship"},
            {"id": "wg-data-pii",         "name": "PII Protection Agent",              "sub_group": "Data Stewardship"},
            {"id": "wg-data-rights",      "name": "Rights & Licensing Agent",          "sub_group": "Data Stewardship"},
        ],
    },
    "ai_centric_division": {
        "label": "AI-Centric Division",
        "description": "23 agents providing continuous monitoring, ethics, and meta-oversight.",
        "agents": [
            {"id": "ai-auto-budget",        "name": "Autonomy Budget Manager",          "sub_group": "Autonomy Governance"},
            {"id": "ai-auto-authority",     "name": "Authority Boundary Agent",         "sub_group": "Autonomy Governance"},
            {"id": "ai-auto-escalation",    "name": "Escalation Logic Agent",           "sub_group": "Autonomy Governance"},
            {"id": "ai-audit-collect",      "name": "Evidence Collection Agent",        "sub_group": "Audit & Evidence"},
            {"id": "ai-audit-correlate",    "name": "Evidence Correlation Agent",       "sub_group": "Audit & Evidence"},
            {"id": "ai-audit-simulate",     "name": "Internal Audit Simulation Agent",  "sub_group": "Audit & Evidence"},
            {"id": "ai-ethics-bias",        "name": "Bias Detection Agent",             "sub_group": "Ethics & Trust"},
            {"id": "ai-ethics-fairness",    "name": "Fairness Monitoring Agent",        "sub_group": "Ethics & Trust"},
            {"id": "ai-ethics-alignment",   "name": "Ethical Alignment Agent",          "sub_group": "Ethics & Trust"},
            {"id": "ai-model-registry",     "name": "Model Registry Agent",             "sub_group": "Model & Data Stewardship"},
            {"id": "ai-model-drift",        "name": "Model Drift Detection Agent",      "sub_group": "Model & Data Stewardship"},
            {"id": "ai-data-pipeline",      "name": "Data Pipeline Agent",              "sub_group": "Model & Data Stewardship"},
            {"id": "ai-data-knowledge",     "name": "Knowledge Management Agent",       "sub_group": "Model & Data Stewardship"},
            {"id": "ai-innov-experiment",   "name": "Experiment Pipeline Agent",        "sub_group": "Innovation"},
            {"id": "ai-innov-rollout",      "name": "Safe Rollout Agent",               "sub_group": "Innovation"},
            {"id": "ai-innov-results",      "name": "Experiment Results Agent",         "sub_group": "Innovation"},
            {"id": "ai-core-sync",          "name": "CORE Graph Sync Agent",            "sub_group": "CORE & Strategy"},
            {"id": "ai-core-alignment",     "name": "CORE Alignment Scoring Agent",     "sub_group": "CORE & Strategy"},
            {"id": "ai-external-stakeholder","name":"External Stakeholder Agent",       "sub_group": "CORE & Strategy"},
            {"id": "ai-external-regulatory","name":"Regulatory Interface Agent",        "sub_group": "Strategy"},
            {"id": "ai-strategy-align",     "name": "Strategy Alignment Agent",         "sub_group": "Strategy"},
            {"id": "ai-strategy-competitive","name":"Competitive Intelligence Agent",   "sub_group": "Strategy"},
            {"id": "ai-strategy-scenario",  "name": "Scenario Planning Agent",          "sub_group": "Strategy"},
        ],
    },
    "digital_twin_agents": {
        "label": "Digital Twins",
        "description": "Live self-models consulted before/during/after every material action.",
        "agents": [
            {"id": "twin-enterprise",  "name": "Enterprise Digital Twin Agent", "purpose": "Models current ADAM structure & state"},
            {"id": "twin-operational", "name": "Operational Twin Agent",        "purpose": "Simulates execution paths & failure scenarios"},
            {"id": "twin-economic",    "name": "Economic Twin Agent",           "purpose": "Models financial impact before/after actions"},
            {"id": "twin-risk",        "name": "Risk & Compliance Twin Agent",  "purpose": "Predicts future regulatory / risk exposure"},
        ],
    },
    "meta_governance_agents": {
        "label": "Meta-Governance",
        "description": "What makes ADAM autonomous rather than automated.",
        "agents": [
            {"id": "meta-stability", "name": "Autonomy Stability Agent",   "purpose": "Prevents runaway feedback loops"},
            {"id": "meta-integrity", "name": "CORE Graph Integrity Agent", "purpose": "Enforces doctrine alignment"},
            {"id": "meta-audit",     "name": "Self-Audit Readiness Agent", "purpose": "Ensures inspection-readiness"},
        ],
    },
}


def _synthetic_agent_state(seed: int = 7919) -> dict:
    """Deterministic per-agent state for demo mode."""
    state: dict = {}
    for cls in _DEFAULT_AGENT_CLASSES.values():
        for a in cls.get("agents", []):
            seed = (seed * 9301 + 49297) % 233280
            r = seed / 233280.0
            # Conceptual-role agents in the registry are presumed autonomous
            # unless an explicit director control or self-audit fault says
            # otherwise. ~12% are in "escalation" (awaiting director approval
            # on a recent intent) for realistic demo variety. None start "down" —
            # an agent goes down only when something specific has happened, and
            # that something must be discoverable in the chain.
            status = "escalation" if r > 0.88 else "autonomous"
            seed = (seed * 9301 + 49297) % 233280
            state[a["id"]] = {
                "id": a["id"],
                "status": status,
                "inflight": int((seed / 233280.0) * 8),
                "queue_depth": int((seed / 233280.0) * 12),
                "cpu_pct": int((seed / 233280.0) * 80) + 5,
                "mem_pct": int((seed / 233280.0) * 70) + 10,
                "last_event": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "current_step": (
                    {"autonomous": "executing",
                     "escalation": "awaiting director approval",
                     "down": "offline (investigation logged)",
                     "safe_mode": "safe mode (limited authority)"}[status]
                ),
            }
    return state


_DEMO_QUEUE = [
    {
        "intent_id": "11111111-1111-4000-8000-000000000001",
        "queued_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "owning_director": "cfo",
        "tier": "HIGH", "score": 63,
        "summary": "Approve $7,500 vendor payment to Globex Streaming Rights Ltd. for Q3 catalog license renewal.",
        "raw_text": "Approve vendor payment of $7,500 to Globex for streaming-rights renewal (Q3 catalog).",
        "dimensions": {"security_impact": 10, "sovereignty_action": 15, "financial_exposure": 55, "regulatory_impact": 25, "reputational_risk": 20, "rights_certainty": 30, "doctrinal_alignment": 15},
        "non_idempotent": True,
        "triggered_by": ["financial_exposure", "non_idempotent_penalty"],
        "alternatives": [
            {"label": "Split into two $3,750 tranches across Q3/Q4", "projected_score": 38},
            {"label": "Renegotiate to $5,000 with shorter term",     "projected_score": 41},
        ],
        "recommendation": "approve", "confidence_pct": 82, "time_sensitivity_hours": 36,
    },
    {
        "intent_id": "22222222-2222-4000-8000-000000000002",
        "queued_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "owning_director": "ciso",
        "tier": "OHSHAT", "score": 81,
        "summary": "Isolate compromised egress node us-east-staging-3 after anomalous outbound traffic to unknown ASN.",
        "raw_text": "Suspected breach / egress leak — isolate node us-east-staging-3 immediately.",
        "dimensions": {"security_impact": 88, "sovereignty_action": 65, "financial_exposure": 15, "regulatory_impact": 45, "reputational_risk": 55, "rights_certainty": 20, "doctrinal_alignment": 30},
        "non_idempotent": True,
        "triggered_by": ["security_impact", "critical_override"],
        "alternatives": [
            {"label": "Quarantine & forensics hold (no data destruction)", "projected_score": 66},
            {"label": "Full isolate + rotate credentials across region",    "projected_score": 72},
        ],
        "recommendation": "approve", "confidence_pct": 96, "time_sensitivity_hours": 1,
    },
    {
        "intent_id": "33333333-3333-4000-8000-000000000003",
        "queued_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "owning_director": "legal_director",
        "tier": "HIGH", "score": 58,
        "summary": "Adopt novel DORA interpretation for cross-border data pipeline — no prior ADAM precedent.",
        "raw_text": "DORA interpretation needed for cross-border streaming analytics pipeline (EU→US).",
        "dimensions": {"security_impact": 25, "sovereignty_action": 40, "financial_exposure": 20, "regulatory_impact": 70, "reputational_risk": 35, "rights_certainty": 55, "doctrinal_alignment": 30},
        "non_idempotent": False,
        "triggered_by": ["regulatory_impact", "novel_interpretation"],
        "alternatives": [
            {"label": "Route analytics through EU-only DC until ruling", "projected_score": 32},
            {"label": "Engage external counsel for advisory opinion",    "projected_score": 28},
        ],
        "recommendation": "defer_to_counsel", "confidence_pct": 64, "time_sensitivity_hours": 72,
    },
    {
        "intent_id": "44444444-4444-4000-8000-000000000004",
        "queued_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "owning_director": "market_director",
        "tier": "HIGH", "score": 54,
        "summary": "Launch $3,200 paid-social burst for Gaming-vertical Q3 refresh — 72-hour window.",
        "raw_text": "Launch $3,200 paid-social campaign for Gaming Q3 refresh across 3 platforms.",
        "dimensions": {"security_impact": 10, "sovereignty_action": 15, "financial_exposure": 35, "regulatory_impact": 20, "reputational_risk": 50, "rights_certainty": 25, "doctrinal_alignment": 20},
        "non_idempotent": True,
        "triggered_by": ["reputational_risk", "financial_exposure", "non_idempotent_penalty"],
        "alternatives": [
            {"label": "Reduce spend to $2,500 (under cap, autonomous)", "projected_score": 29},
            {"label": "A/B test with $1,500 before full commit",        "projected_score": 22},
        ],
        "recommendation": "approve_with_modification", "confidence_pct": 71, "time_sensitivity_hours": 24,
    },
    {
        "intent_id": "55555555-5555-4000-8000-000000000005",
        "queued_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "owning_director": "ceo",
        "tier": "OHSHAT", "score": 78,
        "summary": "Doctrine-root mutation proposed: relax 'no_self_amendment' clause for scenario-planning scope only.",
        "raw_text": "Propose doctrine-root amendment to relax self-amendment clause for scenario planning.",
        "dimensions": {"security_impact": 40, "sovereignty_action": 72, "financial_exposure": 10, "regulatory_impact": 55, "reputational_risk": 45, "rights_certainty": 30, "doctrinal_alignment": 92},
        "non_idempotent": True,
        "triggered_by": ["doctrinal_alignment", "critical_override", "sovereignty_action"],
        "alternatives": [
            {"label": "Scenario-only sandbox with hard read-only doctrine", "projected_score": 44},
            {"label": "Reject entirely; escalate to external audit review", "projected_score": 12},
        ],
        "recommendation": "reject", "confidence_pct": 88, "time_sensitivity_hours": 168,
    },
    {
        "intent_id": "66666666-6666-4000-8000-000000000006",
        "queued_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "owning_director": "cpo",
        "tier": "HIGH", "score": 56,
        "summary": "Approve Gaming-vertical innovation pilot rollout (autonomy budget +$2,000 / quarter).",
        "raw_text": "Approve Gaming-vertical innovation pilot — increase autonomy budget by $2,000/quarter for 6 months.",
        "dimensions": {"security_impact": 15, "sovereignty_action": 25, "financial_exposure": 40, "regulatory_impact": 15, "reputational_risk": 35, "rights_certainty": 20, "doctrinal_alignment": 60},
        "non_idempotent": False,
        "triggered_by": ["doctrinal_alignment", "financial_exposure"],
        "alternatives": [
            {"label": "Limit pilot to single platform & 90 days",      "projected_score": 33},
            {"label": "Defer to next quarterly OKR review",              "projected_score": 18},
        ],
        "recommendation": "approve_with_modification", "confidence_pct": 74, "time_sensitivity_hours": 96,
    },
    {
        "intent_id": "77777777-7777-4000-8000-000000000007",
        "queued_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "owning_director": "cto",
        "tier": "ELEVATED", "score": 47,
        "summary": "Approve Ed25519 → ML-DSA-65 PQC key rotation on Flight Recorder signing key.",
        "raw_text": "Rotate Flight Recorder signing key from Ed25519 to ML-DSA-65 (FIPS 204).",
        "dimensions": {"security_impact": 55, "sovereignty_action": 35, "financial_exposure": 5, "regulatory_impact": 25, "reputational_risk": 15, "rights_certainty": 10, "doctrinal_alignment": 40},
        "non_idempotent": True,
        "triggered_by": ["security_impact", "non_idempotent_penalty"],
        "alternatives": [
            {"label": "Stage rotation to non-prod first",                "projected_score": 28},
            {"label": "Defer until next planned maintenance window",     "projected_score": 22},
        ],
        "recommendation": "approve", "confidence_pct": 92, "time_sensitivity_hours": 168,
    },
]

_DEMO_FR_TAIL = [
    {"seq": 10492, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z"), "event_type": "intent_received",        "agent_id": "hi-intent",      "tier": "—",        "intent_id": "11111111-1111-4000-8000-000000000001"},
    {"seq": 10493, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z"), "event_type": "boss_scored",            "agent_id": "orch-policy",    "tier": "HIGH",     "intent_id": "11111111-1111-4000-8000-000000000001"},
    {"seq": 10494, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z"), "event_type": "governor_evaluated",     "agent_id": "ga-financial",   "tier": "HIGH",     "intent_id": "11111111-1111-4000-8000-000000000001"},
    {"seq": 10495, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z"), "event_type": "exception_emitted",      "agent_id": "orch-exception", "tier": "HIGH",     "intent_id": "11111111-1111-4000-8000-000000000001"},
    {"seq": 10496, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z"), "event_type": "intent_received",        "agent_id": "hi-intent",      "tier": "—",        "intent_id": "22222222-2222-4000-8000-000000000002"},
    {"seq": 10497, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z"), "event_type": "boss_override_applied",  "agent_id": "orch-policy",    "tier": "OHSHAT",   "intent_id": "22222222-2222-4000-8000-000000000002"},
    {"seq": 10498, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z"), "event_type": "twin_simulation_recorded","agent_id":"twin-risk",       "tier": "—",        "intent_id": "22222222-2222-4000-8000-000000000002"},
    {"seq": 10499, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z"), "event_type": "action_executed",        "agent_id": "wg-fin-txn",     "tier": "SOAP",     "intent_id": "soap-routine-0042"},
    {"seq": 10500, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z"), "event_type": "governors_concurred",    "agent_id": "orch-policy",    "tier": "MODERATE", "intent_id": "mod-routine-0101"},
    {"seq": 10501, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z"), "event_type": "director_approval",      "agent_id": "hi-gateway",     "tier": "HIGH",     "intent_id": "hi-approval-0088"},
]


# ---------------------------------------------------------------------------
#  Live state aggregation
# ---------------------------------------------------------------------------

_FR_CACHE_LOCK = Lock()
_FR_CACHE: dict = {"ts": 0.0, "events": [], "by_intent": {}, "by_action_id": {}}
_FR_CACHE_TTL_S = 1.5  # short TTL — keeps us responsive but avoids hammering FR


def _refresh_fr_cache(force: bool = False, limit: int = 500) -> dict:
    now = time.time()
    with _FR_CACHE_LOCK:
        if not force and (now - _FR_CACHE["ts"] < _FR_CACHE_TTL_S) and _FR_CACHE["events"]:
            return _FR_CACHE
        try:
            r = requests.get(f"{FR_URL}/replay", params={"limit": limit}, timeout=4)
            events = r.json() if r.ok else []
        except Exception:
            events = []
        # Index by intent_id and action_id for fast cross-references
        by_intent: dict[str, list] = {}
        by_action_id: dict[str, dict] = {}
        for ev in events:
            iid = (ev.get("evidence") or {}).get("intent_id") or ev.get("intent_id")
            if iid:
                by_intent.setdefault(iid, []).append(ev)
            aid = (ev.get("evidence") or {}).get("action_id")
            if aid:
                by_action_id[aid] = ev
        _FR_CACHE.update({"ts": now, "events": events, "by_intent": by_intent, "by_action_id": by_action_id})
        return _FR_CACHE


_INTERFACE_LAST_OK = False

def _interface_was_reachable() -> bool:
    return _INTERFACE_LAST_OK

def _live_pending() -> list:
    global _INTERFACE_LAST_OK
    try:
        r = requests.get(f"{INTERFACE_URL}/pending", timeout=4)
        body = r.json() if r.ok else {}
        _INTERFACE_LAST_OK = r.ok
    except Exception:
        body = {}
        _INTERFACE_LAST_OK = False
    queue = body.get("queue") or {}
    out = []
    for iid, entry in queue.items():
        p = entry.get("packet") or {}
        dims = p.get("score_breakdown") or p.get("dimensions") or {}
        out.append({
            "intent_id": iid,
            "queued_at": entry.get("queued_at"),
            "owning_director": p.get("owning_director", "ceo"),
            "tier": (p.get("tier") or "HIGH").upper(),
            "score": p.get("score", p.get("composite", 0)),
            "summary": (p.get("intent") or {}).get("desired_outcomes", [{}])[0].get("description", ""),
            "raw_text": (p.get("intent") or {}).get("desired_outcomes", [{}])[0].get("description", ""),
            "dimensions": dims,
            "non_idempotent": bool(p.get("non_idempotent")),
            "triggered_by": p.get("triggered_by", []),
            "alternatives": p.get("alternatives", []),
            "recommendation": p.get("recommendation", "review"),
            "confidence_pct": p.get("confidence_pct", 0),
            "time_sensitivity_hours": p.get("time_sensitivity_hours", 24),
        })
    return out


_INTENT_DECISION_EVENT_TYPES = {
    "intent_decision_approve",
    "intent_decision_reject",
    "intent_decision_defer",
    "intent_resolved",
    "intent_archived",
}

_FR_CHAIN_PATH_CACHE = None

def _resolve_fr_chain_path() -> str:
    """Same path-resolution strategy used by dashboard_views: prefer FR_CHAIN_PATH
    env var, then the FR's hot named-volume mount, then the bind-mount snapshot,
    then the source-tree default. This lets the dashboard read the chain
    directly when running in container or in tests."""
    global _FR_CHAIN_PATH_CACHE
    if _FR_CHAIN_PATH_CACHE is not None:
        return _FR_CHAIN_PATH_CACHE
    candidates = []
    env = os.environ.get("FR_CHAIN_PATH")
    if env: candidates.append(env)
    candidates.append("/var/lib/adam/chain/chain.sqlite")
    candidates.append("/data/adam/flight_recorder/chain.sqlite")
    here = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.normpath(os.path.join(here, "..", "..", "flight_recorder", "chain.sqlite")))
    for c in candidates:
        try:
            if os.path.exists(c) and os.path.getsize(c) > 0:
                _FR_CHAIN_PATH_CACHE = c
                return c
        except Exception:
            pass
    _FR_CHAIN_PATH_CACHE = candidates[0] if candidates else ""
    return _FR_CHAIN_PATH_CACHE


def _live_queue_from_chain(cache: dict) -> list:
    """Derive a director approval queue directly from chain.sqlite.

    Going to disk (read-only, immutable) instead of relying on the FR /replay
    cache means we see ALL intent_received events, not just the last 500
    events that the cache holds. With 60k+ self_audit_run events dominating
    a typical chain, intent_received events fall out of the cache window
    almost immediately — and that's the bug operators saw as "live queue
    is empty even though intents exist".
    """
    chain_path = _resolve_fr_chain_path()
    if not chain_path or not os.path.exists(chain_path):
        return []
    try:
        cx = sqlite3.connect(f"file:{chain_path}?mode=ro&immutable=1", uri=True)
    except Exception:
        return []
    try:
        # 1. Find all intent_ids that have a terminal decision event.
        decided = {r[0] for r in cx.execute(
            "SELECT DISTINCT intent_id FROM entries "
            "WHERE intent_id IS NOT NULL AND event_type IN "
            "('intent_decision_approve','intent_decision_reject','intent_decision_defer',"
            " 'intent_resolved','intent_archived')"
        ).fetchall()}
        # 2. For each intent_id with intent_received events, take the earliest
        #    one (smallest seq) as the queue entry; that's "when it queued".
        rows = cx.execute(
            "SELECT seq, timestamp, intent_id, evidence_json FROM entries "
            "WHERE event_type = 'intent_received' AND intent_id IS NOT NULL "
            "ORDER BY seq ASC"
        ).fetchall()
        # 3. Pull the latest boss_scored event per intent_id so the queue
        #    surfaces the actual computed tier + score + dimensions.
        boss_rows = cx.execute(
            "SELECT intent_id, evidence_json FROM entries "
            "WHERE event_type = 'boss_scored' AND intent_id IS NOT NULL "
            "ORDER BY seq DESC"
        ).fetchall()
    except Exception:
        cx.close()
        return []
    cx.close()
    boss_by_intent: dict = {}
    for iid, ev_json in boss_rows:
        if iid in boss_by_intent:
            continue
        try:
            boss_by_intent[iid] = json.loads(ev_json) if ev_json else {}
        except Exception:
            boss_by_intent[iid] = {}
    received_by: dict = {}
    for seq, ts, iid, ev_json in rows:
        if iid in received_by:
            continue
        try:
            evid = json.loads(ev_json) if ev_json else {}
        except Exception:
            evid = {}
        # Merge BOSS scoring evidence on top of the intent_received evidence
        # so tier / score / dimensions populate from the latest boss_scored.
        boss = boss_by_intent.get(iid) or {}
        merged = dict(evid)
        for k in ("score", "tier", "dimensions", "score_breakdown",
                  "non_idempotent", "triggered_by", "alternatives",
                  "recommendation", "owning_director", "confidence_pct",
                  "time_sensitivity_hours"):
            if boss.get(k) is not None:
                merged[k] = boss[k]
        received_by[iid] = {"ts": ts, "evidence": merged, "seq": seq}
    out = []
    for iid, info in received_by.items():
        if iid in decided:
            continue
        evid = info["evidence"] or {}
        intent = evid.get("intent") or {}
        score = evid.get("score")
        if isinstance(score, dict):
            tier = score.get("routing_tier")
            # composite_score is the Park-Miller-weighted result. composite is the
            # legacy key. Fall back to raw_weighted if neither present.
            score_val = score.get("composite_score") or score.get("composite") or score.get("raw_weighted")
            dims = score.get("dimensions") or {}
        else:
            tier = evid.get("tier")
            score_val = score
            dims = evid.get("dimensions") or evid.get("score_breakdown") or {}
        summary = (
            evid.get("summary")
            or evid.get("intent_summary")
            or evid.get("comment")
            or (intent.get("desired_outcomes") or [{}])[0].get("description")
            or "intent_received"
        )
        out.append({
            "intent_id": iid,
            "queued_at": info["ts"],
            "owning_director": evid.get("owning_director", intent.get("owning_director", "ceo")),
            "tier": (tier or "HIGH").upper(),
            "score": score_val or 0,
            "summary": (summary or "")[:280],
            "raw_text": summary or "",
            "dimensions": dims,
            "non_idempotent": bool(evid.get("non_idempotent")),
            "triggered_by": evid.get("triggered_by") or [],
            "alternatives": evid.get("alternatives") or [],
            "recommendation": evid.get("recommendation") or "review",
            "confidence_pct": evid.get("confidence_pct") or 0,
            "time_sensitivity_hours": evid.get("time_sensitivity_hours") or 24,
        })
    out.sort(key=lambda q: q.get("queued_at") or "", reverse=True)
    return out


def _live_state() -> dict:
    cache = _refresh_fr_cache()
    pending = _live_pending()
    chain_queue = _live_queue_from_chain(cache)
    fr_reachable = bool(cache.get("events"))
    iface_reachable = bool(pending) or _interface_was_reachable()
    routing = {"soap": 0, "moderate": 0, "elevated": 0, "high": 0, "ohshat": 0}
    for ev in cache["events"]:
        evid = ev.get("evidence") or {}
        score = (evid.get("score") or {}).get("routing_tier") if isinstance(evid.get("score"), dict) else None
        tier = (score or evid.get("tier") or "").lower()
        if tier in routing:
            routing[tier] += 1
    fr_tail = []
    for ev in cache["events"][:50]:
        evid = ev.get("evidence") or {}
        fr_tail.append({
            "seq": ev.get("seq"),
            "ts": ev.get("timestamp"),
            "event_type": ev.get("event_type"),
            "agent_id": ev.get("agent_id"),
            "tier": (evid.get("tier") or evid.get("score", {}).get("routing_tier") if isinstance(evid.get("score"), dict) else evid.get("tier")) or "—",
            "intent_id": evid.get("intent_id") or "—",
        })
    state = _demo_state()  # baseline shape (BOSS, agent classes, agent_state, directors)
    # In live mode the queue is sourced ONLY from live data:
    #   1. interface-agents /pending (most authoritative — this is what the
    #      router has actually queued for director review),
    #   2. else the chain (intents with intent_received events that have no
    #      decision event yet),
    #   3. else empty.
    # We never silently fall back to demo data in live mode — that was the
    # bug operators reported: the queue looked identical between modes.
    if pending:
        state["queue"] = pending
        queue_source = "interface_pending"
    elif chain_queue:
        state["queue"] = chain_queue
        queue_source = "chain_derived"
    else:
        state["queue"] = []
        queue_source = "empty"
    # The FR tail is the live chain tail (last 50 events) when FR is reachable,
    # else explicitly empty. No demo overlay in live mode.
    state["flight_recorder"] = fr_tail if fr_tail else []
    if any(routing.values()):
        state["routing_24h"] = routing
    state["meta"]["mode"] = "live"
    state["meta"]["fr_reachable"] = fr_reachable
    state["meta"]["interface_reachable"] = iface_reachable
    state["meta"]["fr_event_count"] = len(cache.get("events") or [])
    state["meta"]["queue_source"] = queue_source
    state["meta"]["queue_count"] = len(state["queue"])
    if not fr_reachable:
        state["meta"]["live_warning"] = "FR /replay returned no events; chain may be unreachable. Live queue+tail are empty."
    elif queue_source == "empty":
        state["meta"]["live_warning"] = "No pending intents in interface-agents queue and no undecided intent_received events on the chain. Empty queue is correct."
    return state


# ---------------------------------------------------------------------------
#  Idempotency
# ---------------------------------------------------------------------------

def _deterministic_action_id(*parts: str) -> str:
    """UUIDv5 over the concatenated string parts — stable across retries."""
    NS = uuid.UUID("d59ec49f-7040-45c7-9324-835626f87525")  # ADAM dashboard namespace
    return str(uuid.uuid5(NS, "|".join(p or "" for p in parts)))


def _previous_action(action_id: str) -> dict | None:
    cache = _refresh_fr_cache(force=True)  # always fresh on a write
    return cache["by_action_id"].get(action_id)


def _fr_append(**kw) -> dict:
    try:
        r = requests.post(f"{FR_URL}/append", json=kw, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ---------------------------------------------------------------------------
#  Blueprint
# ---------------------------------------------------------------------------

dashboard_bp = Blueprint("dashboard", __name__)


def _initialise_caches():
    """Best-effort load of registry + boss + directors from disk."""
    global _DEFAULT_AGENT_CLASSES, _DEFAULT_BOSS, _DEFAULT_DIRECTORS
    reg = _load_first("agents")
    if reg:
        ac = _build_agent_classes_from_registry(reg)
        if ac:
            _DEFAULT_AGENT_CLASSES = ac
    boss = _load_first("boss")
    if boss:
        _DEFAULT_BOSS = {
            "dimensions":         boss.get("dimensions", _DEFAULT_BOSS["dimensions"]),
            "routing_thresholds": boss.get("routing_thresholds", _DEFAULT_BOSS["routing_thresholds"]),
            "composite_formula":  boss.get("composite_formula"),
            "priority_tiers":     boss.get("priority_tiers"),
        }
    dirs_doc = _load_first("directors")
    if dirs_doc and dirs_doc.get("directors"):
        merged = []
        for did, d in (dirs_doc.get("directors") or {}).items():
            merged.append({
                "id": did,
                "title": d.get("title"),
                "name": d.get("real_seat_holder_test"),
                "domain": d.get("domain"),
                "boss_dims": d.get("boss_dim_owned", []),
                "cap_usd": d.get("delegation_cap_per_txn_test_usd"),
                "emergency_override": bool(d.get("emergency_override_authority", False)),
                "active": True,
                "edit_all": did in ("ceo", "ciso"),
            })
        for did, d in (dirs_doc.get("optional_directors") or {}).items():
            merged.append({
                "id": did,
                "title": d.get("title"),
                "name": d.get("real_seat_holder_test", "Michael Lamb (acting)"),
                "domain": d.get("domain", "Optional director"),
                "boss_dims": d.get("boss_dim_owned", []),
                "cap_usd": d.get("delegation_cap_per_txn_test_usd"),
                "emergency_override": False,
                "active": True,  # The user explicitly wants both CPO and CTO active
                "edit_all": False,
            })
        if merged:
            _DEFAULT_DIRECTORS = merged


_initialise_caches()
# Re-build the synthetic state now the agent classes are populated.
_DEMO_AGENT_STATE_CACHE = _synthetic_agent_state()


@dashboard_bp.get("/api/dashboard/health")
def health():
    return jsonify({
        "ok": True,
        "service": "directors-dashboard-api",
        "version": "0.2",
        "doctrine_version": DOCTRINE_VERSION,
        "fr": FR_URL,
        "interface": INTERFACE_URL,
        "boss": BOSS_URL,
        "agent_classes_loaded": list(_DEFAULT_AGENT_CLASSES.keys()),
        "directors_loaded": [d["id"] for d in _DEFAULT_DIRECTORS],
    })


@dashboard_bp.get("/api/dashboard/bootstrap")
def bootstrap():
    return jsonify({
        "ok": True,
        "doctrine_version": DOCTRINE_VERSION,
        "directors": _DEFAULT_DIRECTORS,
        "agent_classes": _DEFAULT_AGENT_CLASSES,
        "boss": _DEFAULT_BOSS,
        "scopes": _DIRECTOR_SCOPES,
        "modes": ["live", "demo"],
        "test_proxy_mode": True,
        "natural_signer": "Michael Lamb",
    })


@dashboard_bp.get("/api/dashboard/state")
def state():
    mode = (request.args.get("mode") or "live").lower()
    if mode == "demo":
        out = _demo_state()
    else:
        try:
            out = _live_state()
        except Exception as e:
            out = _demo_state()
            out["meta"]["mode"] = "demo"
            out["meta"]["live_error"] = str(e)[:200]
    return jsonify(out)


@dashboard_bp.get("/api/dashboard/agents")
def all_agents():
    out = []
    for cls_key, cls in _DEFAULT_AGENT_CLASSES.items():
        for a in cls.get("agents", []):
            out.append({**a, "class": cls_key})
    return jsonify({"ok": True, "count": len(out), "agents": out})


@dashboard_bp.get("/api/dashboard/director/<did>/scope")
def director_scope(did):
    rules = _DIRECTOR_SCOPES.get(did) or {}
    visible: list = []
    for cls_key, cls in _DEFAULT_AGENT_CLASSES.items():
        for a in cls.get("agents", []):
            if _agent_in_scope(a["id"], did):
                visible.append(a["id"])
    return jsonify({"ok": True, "director": did, "rules": rules, "visible_agents": visible, "count": len(visible)})


# ---------------------------------------------------------------------------
#  Agent Card
# ---------------------------------------------------------------------------

@dashboard_bp.get("/api/dashboard/agent/<agent_id>")
def agent_card(agent_id):
    mode = (request.args.get("mode") or "live").lower()
    if mode == "live":
        cache = _refresh_fr_cache()
        # Direct emitter match (agent acting) + indirect match (agent_control_*
        # events emitted by hi-gateway against this agent_id as the target).
        def _is_for_this_agent(ev):
            if ev.get("agent_id") == agent_id:
                return True
            evd = ev.get("evidence") or {}
            return evd.get("agent_id") == agent_id and (
                ev.get("event_type", "").startswith("agent_control_")
                or evd.get("agent_target") == agent_id
            )
        events = [ev for ev in cache["events"] if _is_for_this_agent(ev)][:50]
    else:
        events = [e for e in _DEMO_FR_TAIL if e["agent_id"] == agent_id]
    a = None
    cls_key = None
    for k, cls in _DEFAULT_AGENT_CLASSES.items():
        for cand in cls.get("agents", []):
            if cand["id"] == agent_id:
                a = cand
                cls_key = k
                break
        if a:
            break
    state = (_DEMO_AGENT_STATE_CACHE.get(agent_id) if mode == "demo" else _live_agent_state(agent_id, events)) or {
        "id": agent_id, "status": "unknown", "current_step": "—", "cpu_pct": 0, "mem_pct": 0, "queue_depth": 0,
        "inflight": 0, "last_event": None,
    }
    return jsonify({
        "ok": True,
        "agent_id": agent_id,
        "agent": a or {"id": agent_id, "name": agent_id, "class": cls_key},
        "class": cls_key,
        "state": state,
        "events": events,
        "controls_supported": ["start", "restart", "diagnose", "safe_mode"],
        "doctrine_version": DOCTRINE_VERSION,
    })


_CONTROL_TO_STATUS = {
    "agent_control_start":     ("autonomous", "started by director"),
    "agent_control_restart":   ("autonomous", "restarted by director"),
    "agent_control_diagnose":  ("autonomous", "diagnostic complete"),
    "agent_control_safe_mode": ("safe_mode",  "in safe mode (limited authority, awaiting director release)"),
}


def _agent_state_from_demo_with_overrides(agent_id: str, control_events: list) -> dict:
    """Take the synthetic demo state but override status/current_step using
    the most-recent agent_control_* event for this agent. This means clicking
    Start on a 'down' agent actually changes its status — and the change is
    auditable via the chain entry that backs it.
    """
    base = dict(_DEMO_AGENT_STATE_CACHE.get(agent_id, {
        "id": agent_id, "status": "unknown", "current_step": "-",
        "cpu_pct": 0, "mem_pct": 0, "queue_depth": 0, "inflight": 0, "last_event": None,
    }))
    if not control_events:
        return base
    # control_events[0] is most recent (FR /replay returns DESC by seq).
    ev = control_events[0]
    override = _CONTROL_TO_STATUS.get(ev.get("event_type"))
    if override:
        new_status, step = override
        base["status"] = new_status
        base["current_step"] = step
        base["last_event"] = ev.get("timestamp")
    return base


def _live_agent_state(agent_id: str, events: list) -> dict | None:
    # Sort agent_control_* events to the front when finding "the latest control".
    control_events = [e for e in events if e.get("event_type", "").startswith("agent_control_")]
    if not events:
        # No FR events at all for this agent — use demo cache, but still apply
        # any control events the cache might know about (it does not yet, so
        # this currently returns plain demo state for unknown agents).
        return _DEMO_AGENT_STATE_CACHE.get(agent_id)
    last = events[0]
    evid = last.get("evidence") or {}
    # Any control action overrides the inferred status from a self-audit run.
    if control_events:
        return _agent_state_from_demo_with_overrides(agent_id, control_events)
    return {
        "id": agent_id,
        "status": evid.get("status", "autonomous"),
        "current_step": evid.get("current_step", last.get("event_type", "-")),
        "cpu_pct": evid.get("cpu_pct", 0),
        "mem_pct": evid.get("mem_pct", 0),
        "queue_depth": evid.get("queue_depth", 0),
        "inflight": evid.get("inflight", 0),
        "last_event": last.get("timestamp"),
    }


@dashboard_bp.post("/api/dashboard/agent/<agent_id>/control")
def agent_control(agent_id):
    body = request.get_json(force=True, silent=True) or {}
    action = (body.get("action") or "").lower()
    director = body.get("director_id") or "ceo"
    comment = body.get("comment") or ""
    if action not in ("start", "restart", "diagnose", "safe_mode"):
        return jsonify({"ok": False, "error": "invalid_action"}), 400
    # Authority gate
    if not _agent_in_scope(agent_id, director):
        return jsonify({"ok": False, "error": "out_of_scope_for_director"}), 403
    if not _can_edit(director, director):
        return jsonify({"ok": False, "error": "director_cannot_edit"}), 403
    action_id = body.get("action_id") or _deterministic_action_id(
        agent_id, action, director, body.get("idempotency_key", "")
    )
    prior = _previous_action(action_id)
    if prior:
        return jsonify({"ok": True, "idempotent": True, "action_id": action_id, "prior_event": prior})
    fr_evidence = {
        "intent_id": None,
        "action_id": action_id,
        "agent_id": agent_id,
        "control": action,
        "director": director,
        "acting_person": "michael.lamb",
        "test_proxy_mode": True,
        "comment": comment[:1000],
    }
    appended = _fr_append(
        event_type=f"agent_control_{action}",
        agent_id="hi-gateway",
        agent_class="human_interface_agents",
        evidence=fr_evidence,
        doctrine_version=DOCTRINE_VERSION,
    )
    _fr_append(
        event_type="director_proxy_acting",
        agent_id="hi-gateway",
        agent_class="human_interface_agents",
        evidence={"role_proxied": director, "natural_person": "michael.lamb",
                  "action_id": action_id, "agent_target": agent_id, "control": action},
        doctrine_version=DOCTRINE_VERSION,
    )
    return jsonify({"ok": True, "idempotent": False, "action_id": action_id, "fr": appended})


# ---------------------------------------------------------------------------
#  Intent Object Card
# ---------------------------------------------------------------------------

@dashboard_bp.get("/api/dashboard/intent/<intent_id>")
def intent_card(intent_id):
    mode = (request.args.get("mode") or "live").lower()
    if mode == "live":
        try:
            r = requests.get(f"{FR_URL}/replay", params={"intent_id": intent_id}, timeout=5)
            events = r.json() if r.ok else []
        except Exception:
            events = []
        intent_packet = None
        for q in _live_pending():
            if q["intent_id"] == intent_id:
                intent_packet = q
                break
        if intent_packet is None:
            for q in _DEMO_QUEUE:
                if q["intent_id"] == intent_id:
                    intent_packet = q
                    break
    else:
        events = []
        intent_packet = None
        for q in _DEMO_QUEUE:
            if q["intent_id"] == intent_id:
                intent_packet = q
                break
    if not intent_packet:
        return jsonify({"ok": False, "error": "intent_not_found", "intent_id": intent_id}), 404
    composite = _composite(intent_packet.get("dimensions", {}), intent_packet.get("non_idempotent"))
    return jsonify({
        "ok": True,
        "intent_id": intent_id,
        "intent": intent_packet,
        "composite": composite,
        "events": events,
        "decisions": _decisions_for(intent_id, events),
        "doctrine_version": DOCTRINE_VERSION,
    })


def _composite(dims: dict, non_idem: bool) -> dict:
    weights = _DEFAULT_BOSS["dimensions"]
    wsum = sum(weights.values()) or 24.0
    base = sum((dims.get(k, 0) or 0) * w for k, w in weights.items()) / wsum
    max_dim = max(list(dims.values()) or [0])
    if max_dim > 75:
        base = max(base, max_dim - 10)
    if non_idem:
        base += 15
    base = min(100, round(base))
    tier = (
        "OHSHAT"   if base >= 76 else
        "HIGH"     if base >= 51 else
        "ELEVATED" if base >= 31 else
        "MODERATE" if base >= 11 else
        "SOAP"
    )
    return {"score": base, "tier": tier, "weights": weights}


def _decisions_for(intent_id: str, events: list) -> list:
    out = []
    for ev in events:
        et = ev.get("event_type", "")
        if et.startswith("director_") and et != "director_proxy_acting":
            evid = ev.get("evidence") or {}
            out.append({
                "decision": et.replace("director_", ""),
                "director": evid.get("director"),
                "acting_person": evid.get("acting_person"),
                "comment": evid.get("comment"),
                "action_id": evid.get("action_id"),
                "ts": ev.get("timestamp"),
                "seq": ev.get("seq"),
            })
    return out


@dashboard_bp.get("/api/dashboard/intents")
def all_intents():
    cache = _refresh_fr_cache()
    intents = {}
    for ev in cache["events"]:
        evid = ev.get("evidence") or {}
        iid = evid.get("intent_id") or ev.get("intent_id")
        if not iid:
            continue
        if iid not in intents:
            intents[iid] = {"intent_id": iid, "first_seen": ev["timestamp"],
                            "last_event_type": ev["event_type"], "events": 1}
        else:
            intents[iid]["events"] += 1
            intents[iid]["last_event_type"] = ev["event_type"]
    for q in _live_pending():
        intents.setdefault(q["intent_id"], {"intent_id": q["intent_id"], "first_seen": q.get("queued_at"),
                                             "last_event_type": "queued", "events": 0})
        intents[q["intent_id"]].update({"summary": q.get("summary"), "tier": q.get("tier"),
                                        "owning_director": q.get("owning_director"), "score": q.get("score")})
    return jsonify({"ok": True, "count": len(intents), "intents": list(intents.values())})


@dashboard_bp.post("/api/dashboard/intent/<intent_id>/decision")
def intent_decision(intent_id):
    body = request.get_json(force=True, silent=True) or {}
    decision = (body.get("decision") or "").lower()
    director = body.get("director_id") or "ceo"
    comment = body.get("comment") or ""
    what_if = body.get("what_if")
    modifications = body.get("modifications") or {}
    if decision not in ("approve", "reject", "modify", "deny", "comment", "defer"):
        return jsonify({"ok": False, "error": "invalid_decision"}), 400
    target_director = body.get("owning_director") or director
    if not _can_edit(director, target_director):
        return jsonify({"ok": False, "error": "director_cannot_edit_other"}), 403

    action_id = body.get("action_id") or _deterministic_action_id(
        intent_id, decision, director, body.get("idempotency_key", "")
    )
    prior = _previous_action(action_id)
    if prior:
        return jsonify({"ok": True, "idempotent": True, "action_id": action_id, "prior_event": prior})

    cascade = None
    if decision in ("approve", "reject"):
        try:
            path = "/approve/" if decision == "approve" else "/reject/"
            r = requests.post(f"{INTERFACE_URL}{path}{intent_id}", timeout=5,
                              headers={"X-Director-Email": "michael.lamb@netstreamx.local",
                                       "X-Director-Id": director,
                                       "X-Action-Id": action_id})
            cascade = r.json() if r.ok else {"ok": False, "status": r.status_code}
        except Exception as e:
            cascade = {"ok": False, "error": str(e)}

    fr_evidence = {
        "intent_id": intent_id,
        "action_id": action_id,
        "director": director,
        "acting_person": "michael.lamb",
        "test_proxy_mode": True,
        "decision": decision,
        "comment": comment[:1000],
        "modifications": modifications,
        "what_if": what_if,
    }
    event_type = {
        "approve": "director_approval",
        "reject":  "director_rejection",
        "modify":  "director_modified",
        "deny":    "director_denied",
        "comment": "director_comment",
        "defer":   "director_deferred",
    }[decision]
    appended = _fr_append(
        event_type=event_type,
        agent_id="hi-gateway",
        agent_class="human_interface_agents",
        evidence=fr_evidence,
        intent_id=intent_id,
        doctrine_version=DOCTRINE_VERSION,
    )
    _fr_append(
        event_type="director_proxy_acting",
        agent_id="hi-gateway",
        agent_class="human_interface_agents",
        evidence={"role_proxied": target_director, "natural_person": "michael.lamb",
                  "action_id": action_id, "intent_id": intent_id, "decision": decision},
        intent_id=intent_id,
        doctrine_version=DOCTRINE_VERSION,
    )
    return jsonify({"ok": True, "idempotent": False, "action_id": action_id,
                    "fr": appended, "cascade": cascade, "decision": decision})


@dashboard_bp.post("/api/dashboard/intent/<intent_id>/what_if")
def intent_what_if(intent_id):
    body = request.get_json(force=True, silent=True) or {}
    overrides = body.get("dimension_overrides") or {}
    non_idem = body.get("non_idempotent")
    base_intent = None
    for q in _DEMO_QUEUE + _live_pending():
        if q["intent_id"] == intent_id:
            base_intent = q
            break
    if not base_intent:
        return jsonify({"ok": False, "error": "intent_not_found"}), 404
    dims = dict(base_intent.get("dimensions") or {})
    dims.update({k: int(v) for k, v in overrides.items() if k in dims})
    if non_idem is None:
        non_idem = base_intent.get("non_idempotent", False)
    return jsonify({
        "ok": True,
        "intent_id": intent_id,
        "base": _composite(base_intent.get("dimensions", {}), base_intent.get("non_idempotent", False)),
        "modified": _composite(dims, non_idem),
        "modified_dimensions": dims,
        "non_idempotent": bool(non_idem),
    })


def register(app):
    """Convenience helper used by netstreamx_app to mount this blueprint."""
    app.register_blueprint(dashboard_bp)


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps({"ok": True,
                      "directors": [d["id"] for d in _DEFAULT_DIRECTORS],
                      "classes": list(_DEFAULT_AGENT_CLASSES.keys())}, indent=2))
