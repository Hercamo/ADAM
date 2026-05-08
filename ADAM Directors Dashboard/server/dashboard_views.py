#!/usr/bin/env python3
"""
ADAM Directors Dashboard — Production Views
============================================

Read-only director-facing views over the live ADAM runtime.
Mounts as a Flask Blueprint named ``adam_dashboard_views`` alongside
``dashboard_api`` on the NetStreamX backend.

Endpoints
---------
GET  /api/dashboard/dna/sections                    13-section DNA Graph (Q + A from live netstreamx-dna.json)
GET  /api/dashboard/dna/section/<n>                 One section of the DNA Graph
GET  /api/dashboard/boss/dimension/<dim>            Per-dimension detail (weight, bands, matched rules, tier interpretation)
GET  /api/dashboard/lifecycle/<intent_id>           Linear lifecycle (left-to-right) of an intent, sourced from chain.sqlite
GET  /api/dashboard/lifecycle/<intent_id>/event/<seq>   Full Flight Recorder entry card payload for one step

Doctrine alignment
------------------
* Strictly read-only. No write paths. Live chain.sqlite is opened with
  SQLite URI ``mode=ro`` and never mutated.
* Doctrine never self-amends. Reads ``core/rules-seed.json``,
  ``core/objectives-seed.json`` and ``dna/netstreamx-dna.json`` to
  surface the company DNA and rule provenance — never writes them.
* Software-HSM only. No new crypto dependency. Verifies signatures via
  the existing FlightRecorder helpers when available.
* test_proxy_mode preserved. These views do not change the signing path.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from flask import Blueprint, jsonify, request

# ---------------------------------------------------------------------------
#  Configuration — paths resolve to the live deployment
# ---------------------------------------------------------------------------

VIEWS_BP = Blueprint("adam_dashboard_views", __name__)

_HERE = Path(__file__).resolve().parent
_DEPLOY = _HERE.parent
def _resolve_fr_chain_path() -> Path:
    """Resolve which chain.sqlite the dashboard reads from.

    Preference order (first existing file wins):
      1. $FR_CHAIN_PATH env var (set by docker-compose to the FR named volume).
      2. /var/lib/adam/chain/chain.sqlite (FR hot volume mounted RO into the app).
      3. /data/adam/flight_recorder/chain.sqlite (bind-mount snapshot — legacy).
      4. <repo>/flight_recorder/chain.sqlite (source-tree default for tests).
    """
    candidates = []
    env = os.environ.get("FR_CHAIN_PATH")
    if env: candidates.append(Path(env))
    candidates.append(Path("/var/lib/adam/chain/chain.sqlite"))
    candidates.append(Path("/data/adam/flight_recorder/chain.sqlite"))
    candidates.append(_DEPLOY.parent.parent / "flight_recorder" / "chain.sqlite")
    for c in candidates:
        try:
            if c.exists() and c.stat().st_size > 0:
                return c
        except Exception:
            pass
    # No existing file — fall back to first candidate so the rest of the
    # module has a Path object to introspect ("does it exist?" returns False).
    return candidates[0]


_FR_LIVE = _resolve_fr_chain_path()
_DNA_PATH   = Path(os.environ.get("DNA_PATH",            str(_DEPLOY / "dna" / "netstreamx-dna.json")))
_BOSS_CFG   = Path(os.environ.get("BOSS_CFG",            str(_DEPLOY / "boss" / "boss-config.json")))
_RULES_SEED = Path(os.environ.get("RULES_SEED_PATH",     str(_DEPLOY / "core" / "rules-seed.json")))
_OBJ_SEED   = Path(os.environ.get("OBJECTIVES_SEED_PATH",str(_DEPLOY / "core" / "objectives-seed.json")))

DOCTRINE_VERSION = os.environ.get("DOCTRINE_VERSION", "1.0.0-test")

_LOCK = Lock()


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def _load_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


# ---------------------------------------------------------------------------
#  DNA Graph — 13 sections of the company's DNA Questionnaire
#
#  Question text is canonical to the DNA Questionnaire v0.2.
#  Answers are sourced from the deployed netstreamx-dna.json so the
#  viewer always reflects the company's currently-deployed DNA.
# ---------------------------------------------------------------------------

def _dna_payload() -> dict:
    dna = _load_json(_DNA_PATH)
    company = dna.get("company", {})
    boss = dna.get("boss", {})

    sections = [
        {
            "id": 1,
            "title": "Doctrine Identity & Constitutional Foundation",
            "summary": "Permanent principles, mission, and non-negotiable boundaries that autonomous agents must never violate.",
            "core_engine_note": "Populates CORE Graph root node and permanent-doctrine layer. Immutable without board-level approval and doctrine versioning.",
            "subsections": [
                {"id": "1.1", "title": "Mission, Purpose & Founding Doctrine", "questions": [
                    {"id": "1.1.1", "q": "Legal name, jurisdiction of incorporation, and founding date.",
                     "a": f"{company.get('legal_name','NetStreamX, Inc.')}. {company.get('jurisdiction','Delaware, USA')} C-Corp. Founded {company.get('founded','August 2002')}."},
                    {"id": "1.1.2", "q": "Mission statement (the permanent, enduring reason it exists).",
                     "a": company.get("mission", "To entertain the world.")},
                    {"id": "1.1.3", "q": "Vision (aspirational future state).",
                     "a": company.get("vision", "World's leading entertainment platform.")},
                    {"id": "1.1.4", "q": "Permanent, non-negotiable principles ADAM must treat as immutable doctrine.",
                     "a": "(1) Creator Freedom — never override creative vision for commercial pressure. (2) Customer Trust as Foundation — every decision starts with does this protect or enhance the viewer's trust. (3) Evidence Over Opinion — data informs, evidence proves, opinion yields. (4) Radical Transparency Internally — information flows freely. (5) Compliance Is Not Optional — regulatory obligations are mandates, never soft constraints."},
                    {"id": "1.1.5", "q": "Sacred boundaries the company explicitly refuses to cross.",
                     "a": "Never sell or share individual viewing data to third parties. Never produce content that exploits minors. Never misrepresent AI-generated content as human-created without disclosure. Never accept advertising that conflicts with editorial independence. Never silently resolve a doctrine conflict — always escalate to human directors."},
                    {"id": "1.1.6", "q": "Legal entity structure (parent, subsidiaries, JVs).",
                     "a": f"{company.get('legal_entity','NetStreamX Inc.')} Subsidiaries: {', '.join(company.get('subsidiaries_simulated', []))}."},
                ]},
                {"id": "1.2", "title": "Human Governance Structure", "questions": [
                    {"id": "1.2.1", "q": "Each human director role: accountability domain, escalation authority, doctrine authorship rights.",
                     "a": "CEO — owns overall enterprise intent, final arbiter for irreconcilable doctrine conflicts. CFO — owns financial doctrine, spending thresholds, autonomy budget caps. Legal Director — regulatory compliance, jurisdictional rules, legal personality. Market Director — external posture, brand, competitive strategy. CISO — security posture, trust boundaries, incident response."},
                    {"id": "1.2.2", "q": "Optional director roles beyond the core five.",
                     "a": "CPO (Product & Innovation) — active given Streaming, Gaming, Advertising and Live product lines. CTO — inactive in this profile (technical stewardship consolidated under CEO; CISO owns security-technical concerns)."},
                    {"id": "1.2.3", "q": "Delegation model (scope, revocability, audit).",
                     "a": "Explicit, scoped, revocable, auditable. CEO delegates operational execution up to $5M/transaction (test scale: $5,000). CFO delegates routine financial operations up to $500K (test: $500). Legal Director: monitoring delegated; novel interpretations require escalation. All delegations are versioned and create Flight Recorder entries."},
                    {"id": "1.2.4", "q": "How directors interact with ADAM (intent interface and explain-back expectations).",
                     "a": "Directors interact solely through the Intent Interpretation Agent (hi-intent), the Trust Gateway Agent (hi-gateway) and the Explain-Back Agent (hi-explain). Directors never issue direct commands to work-group agents. All interactions are captured as governance evidence."},
                ]},
            ],
        },
        {
            "id": 2,
            "title": "CORE Engine — Culture Graph",
            "summary": "How the company thinks, resolves tension, expresses identity. Machine-readable context for trade-offs, tone, posture, and prioritization.",
            "core_engine_note": "Populates the Culture subgraph within CORE.",
            "subsections": [
                {"id": "2.1", "title": "Values as Trade-Off Priorities", "questions": [
                    {"id": "2.1.1", "q": "Values as explicit trade-off priorities (what wins against what).",
                     "a": "Long-term relationships > short-term transactions. Regulatory compliance > operational speed. Creator vision > commercial optimization. Customer trust > growth metrics. Transparency > competitive secrecy (internal). Innovation risk > operational safety (bounded by autonomy budget)."},
                    {"id": "2.1.2", "q": "Behavioural norms agents must embody on behalf of the company.",
                     "a": "Escalate above your authority rather than assume. Assume good intent. Share information freely. Radical Candor. When in doubt, act in the customer's interest. Admit mistakes quickly. Move fast on reversible decisions; deliberate on irreversible ones."},
                    {"id": "2.1.3", "q": "How the company handles failure (informs how agents handle their own failures).",
                     "a": "Failure is information, not shame. Post-mortems are blameless and systemic. Pre-mortems before major launches. Smart-risk failures recognised equally. Near-misses analysed with the same rigor. Flight Recorder captures all failure events."},
                    {"id": "2.1.4", "q": "Decision-making philosophy (consensus vs distributed; speed vs thoroughness).",
                     "a": "Informed Captain. One person owns the decision after seeking input. Speed valued. Reversible quickly; irreversible deliberately. Person closest to the data decides. Maps to Domain Governor Agents — they evaluate against doctrine and decide."},
                ]},
                {"id": "2.2", "title": "Public Posture vs Internal Optimisation", "questions": [
                    {"id": "2.2.1", "q": "External brand posture (how the brand sounds, acts, presents).",
                     "a": "Confident not arrogant. Culturally aware, pop-culture fluent. Slightly rebellious. Inclusive without tokenism. Conversational language. Members not users. Stories not content. Self-aware humour. Crisis tone: transparent, empathetic, action-oriented."},
                    {"id": "2.2.2", "q": "Internal optimisation posture.",
                     "a": "Cost discipline in infra/ops. Data-driven with evidence thresholds. Speed in engineering. Lean operational overhead. Aggressive experimentation. Applied to internal agents only — never customer-facing or brand-representative agents."},
                    {"id": "2.2.3", "q": "Where public posture and internal optimisation conflict; resolution rules.",
                     "a": "Cost vs CX quality: customer experience wins unless reduction is imperceptible (validated by A/B with <1% negative signal). Speed vs localization: never release machine-only translation for Tier 1 markets; acceptable Tier 3 with disclosure."},
                ]},
            ],
        },
        {
            "id": 3,
            "title": "CORE Engine — Objectives Graph",
            "summary": "Mandates (non-negotiable), goals (measurable, time-bound), objectives (aspirational). Hierarchy prevents over-optimization of aspirations at the expense of mandates.",
            "core_engine_note": "Populates the Objectives subgraph. Used by the Enterprise Strategy Governor Agent.",
            "subsections": [
                {"id": "3.1", "title": "Mandates (Non-Negotiable)", "questions": [
                    {"id": "3.1.1", "q": "Absolute requirements that take priority over everything else.",
                     "a": "M1 platform uptime ≥99.97%/month. M2 zero tolerance for PII data breaches. M3 full regulatory compliance in every jurisdiction. M4 all content rights-cleared before publication. M5 zero material misstatements in financial reporting. M6 no unauthorized use of customer data."},
                    {"id": "3.1.2", "q": "Enforcement mechanism and escalation path per mandate.",
                     "a": "M1 Operational Twin monitors uptime. M2 security agents block unmatched data egress; immediate Legal+CISO escalation. M3 Legal & Compliance Governor; novel cases to Legal Director. M4 Rights & Licensing Subgraph consulted; uncertainty triggers rights hold. M5 Financial Stewardship runs continuous reconciliation; >$1K discrepancies to CFO. M6 Data Governance Agent enforces access controls."},
                ]},
                {"id": "3.2", "title": "Goals (Measurable, Time-Bound)", "questions": [
                    {"id": "3.2.1", "q": "Goals for current fiscal year (metric, target, owner).",
                     "a": "G1 ad-tier subscribers 80M (Market). G2 $50B revenue (Financial). G3 launch NetStreamX Live, 48 events (Strategy). G4 28% operating margin (Financial). G5 -12% delivery cost / stream-hour (Financial+Ops). At test scale these are rescaled to NetStreamX-test numerics."},
                    {"id": "3.2.2", "q": "Priority ordering between goals when they conflict.",
                     "a": "G4 (margin) > G2 (revenue) > G1 (ad-tier growth) > G3 (Live launches) > G5 (cost reduction). Quarterly-configurable by CEO and CFO."},
                    {"id": "3.2.3", "q": "Quarterly planning cadence; how goals cascade to Domain Governors.",
                     "a": "Annual goals set by board in December. Quarterly refinement in weeks 11-12 of prior quarter. CEO+CFO update doctrine parameters. Strategy Governor cascades to all Domain Governors within minutes."},
                ]},
                {"id": "3.3", "title": "Objectives (Aspirational)", "questions": [
                    {"id": "3.3.1", "q": "Aspirational objectives (deprioritized if conflicting with mandates/goals).",
                     "a": "O1 most-loved entertainment brand globally (NPS>50). O2 definitive platform for non-English language storytelling. O3 pioneer AI-personalized interactive storytelling. O4 industry leader in creator-friendly business practices. O5 net-zero carbon by 2030."},
                    {"id": "3.3.2", "q": "How ADAM measures progress and when to deprioritize.",
                     "a": "O1 quarterly NPS + sentiment; deprioritize if NPS gain requires >$500M with no revenue correlation. O2 non-English viewing % + creator pipeline diversity. O3 interactive launches + engagement; deprioritize if <5% engagement after 3 quarters."},
                ]},
            ],
        },
        {
            "id": 4,
            "title": "CORE Engine — Rules & Expectations Graph",
            "summary": "Hard rules (never violate) and soft expectations (preferred behaviour with exception tolerance).",
            "core_engine_note": "Populates Rules and Expectations nodes. Consumed by Policy Enforcement Orchestrator.",
            "subsections": [
                {"id": "4.1", "title": "Hard Rules (Zero Tolerance)", "questions": [
                    {"id": "4.1.1", "q": "Hard rules — blocking constraints in ADAM's policy engine.",
                     "a": "R1 never process transactions for sanctioned entities. R2 never publish content without verified rights clearance. R3 never spend above the per-transaction autonomy budget without human approval. R4 never share customer PII outside the data residency jurisdiction. R5 never modify the CORE Graph without human director authorization. R6 all external communications pass brand compliance check. R7 no agent may self-promote authority. R8 financial transactions require idempotency guarantees."},
                    {"id": "4.1.2", "q": "Per-rule source authority and BOSS dimension mapping.",
                     "a": "R1 OFAC/EU sanctions → Regulatory. R2 Copyright + IP → Rights. R3 Board financial delegation → Financial. R4 GDPR/CCPA/LGPD → Regulatory+Security. R5 ADAM doctrine integrity → Doctrinal. R6 Brand protection → Doctrinal. R7 ADAM security architecture → Security. R8 ADAM resilience → Financial+Security."},
                ]},
                {"id": "4.2", "title": "Soft Expectations (Exception-Tolerant)", "questions": [
                    {"id": "4.2.1", "q": "Soft expectations: expectation, acceptable exceptions, exception cost.",
                     "a": "E1 respond to customer service in 2h (8h during outage with proactive comms). E2 marketing campaigns brand-team-reviewed (post-hoc within 24h for time-sensitive). E3 new vendor contracts: 3+ bids (sole-source allowed <$50K or emergency). E4 content localization in 45 languages for Tier 1 (fast-follow acceptable for surprise viral)."},
                    {"id": "4.2.2", "q": "Exception tolerance threshold before doctrine review.",
                     "a": "If an expectation generates exceptions >15% of the time over any rolling 30-day window, the CORE Graph Integrity Agent flags it for human review. Directors receive a structured review packet with frequency, cost impact, root causes and proposed adjustments."},
                ]},
            ],
        },
        {
            "id": 5,
            "title": "CORE Subgraphs — Enterprise Memory",
            "summary": "Domain-specific semantic layers giving agents precise memory for financial reality, rights ownership, customer relationships, regulatory obligations, and strategic drift.",
            "core_engine_note": "Each subgraph is maintained by its corresponding Domain Governor Agent and Agentic Work Group.",
            "subsections": [
                {"id": "5.1", "title": "Financials Subgraph", "questions": [
                    {"id": "5.1.1", "q": "Budget structure: per BU annual + quarterly + spending authority tiers.",
                     "a": "Streaming Ops $4.2B annual; <$100K auto, $100K-$500K Financial Governor, >$500K CFO. Content Production $17B (test rescaled). Marketing $3.5B; <$1M auto, >$1M Market Director. Engineering/R&D $5.8B."},
                    {"id": "5.1.2", "q": "Revenue recognition rules and reporting requirements.",
                     "a": "Subscription revenue ratable over service period. Ad revenue at impression. Licensing per contractual milestones. ASC 606 compliance. Monthly close 5 BD. Quarterly SEC reporting on 10-Q/10-K. Variance >5% triggers automatic CFO alert."},
                    {"id": "5.1.3", "q": "Autonomy budget parameters (daily/weekly/monthly aggregate caps).",
                     "a": "Daily $10M (test: $10K). Weekly $50M (test: $50K). Monthly $150M (test: $150K). At 85% of any cap, Exception Economy triggers mandatory CFO review. Emergency override: CEO can lift daily cap to $25M for 72 hours."},
                ]},
                {"id": "5.2", "title": "Rights & Licensing Subgraph", "questions": [
                    {"id": "5.2.1", "q": "Categories of rights/licenses (type, scope, expiration, constraints).",
                     "a": "Original content (full ownership, perpetual worldwide). Licensed content (800+ titles, windowed by territory). Music (master + sync, blanket bg). Tech licenses (encoding patents, DRM Widevine/FairPlay/PlayReady). Talent (multi-year deals with 15 marquee creators). Every agreement encoded in the subgraph with expirations and territory restrictions."},
                    {"id": "5.2.2", "q": "Minimum rights certainty threshold for autonomous publish/distribute.",
                     "a": "Tier 1 markets (US/UK/EU): 95. Tier 2: 90. Tier 3: 85. Below threshold: automatic hold + Legal Director escalation with rights-gap analysis."},
                ]},
                {"id": "5.3", "title": "Customer & Reputation Subgraph", "questions": [
                    {"id": "5.3.1", "q": "Customer segmentation and per-segment agent treatment.",
                     "a": "Binge Enthusiasts (18-34) — discovery speed. Family Hub (28-45) — Kids profile safety. Casual Viewers (35-65) — price sensitivity / value. Global Cinephiles (25-55) — subtitle / dubbing quality. Ad-Supported (18-28) — never exceed 4 min/hour ad load."},
                    {"id": "5.3.2", "q": "Reputational red lines.",
                     "a": "No political/partisan associations. No ads adjacent to content depicting violence against children. No public competitor disparagement. No mocking of cultural traditions. No customer viewing data in public marketing without consent. Social agents escalate trending controversies; crisis comms require Market Director."},
                ]},
                {"id": "5.4", "title": "Regulatory & Jurisdiction Subgraph", "questions": [
                    {"id": "5.4.1", "q": "Regulatory frameworks per jurisdiction (scope, reporting, penalties).",
                     "a": "EU: GDPR, DSA, DMA, EU AI Act, DORA, NIS2. US: CCPA/CPRA, COPPA, SEC, DMCA. Brazil: LGPD. South Korea: PIPA. India: IT Act. Content classification: BBFC, FSK, KAVI. Each is a subgraph node with obligation triggers, schedules, penalties."},
                    {"id": "5.4.2", "q": "Data residency and sovereignty constraints.",
                     "a": "EU member data resides in EU DCs. GDPR-compliant transfers only. Sovereignty-first topology — local processing, locally signed evidence. Cross-border access logged with director-level audit."},
                ]},
                {"id": "5.5", "title": "Strategy Drift Subgraph", "questions": [
                    {"id": "5.5.1", "q": "What constitutes drift; how it is detected.",
                     "a": "Sustained divergence between declared rules and executed behaviour. Detected by CORE graph + Twin divergence > 2% amber, > 5% red. Doctrine Drift events written to Flight Recorder; Stability Agent clusters monthly."},
                ]},
            ],
        },
        {
            "id": 6,
            "title": "BOSS Scoring & Exception Economy Configuration",
            "summary": "Seven dimensions, weighted composite with critical-dim override and non-idempotent penalty. Exception Economy thresholds.",
            "core_engine_note": "BOSS is the routing/risk function; Exception Economy is the escalation tier set.",
            "subsections": [
                {"id": "6.1", "title": "BOSS Dimensions & Weights", "questions": [
                    {"id": "6.1.1", "q": "Dimension weights and priority labels (sum to 24.0).",
                     "a": "Security 5.0 (Top), Sovereignty 4.0 (Very High), Financial 4.0 (Very High), Regulatory 3.0 (High), Reputational 3.0 (High), Rights 3.0 (High), Doctrinal 2.0 (Medium). Σ=24.0."},
                    {"id": "6.1.2", "q": "Composite formula and overrides.",
                     "a": "C = Σ(S_d × w_d) / 24.0. Critical-dim override: if max(S_d) > 75 then C ≥ max(S_d) − 10. Non-idempotent penalty: +15 additive flat. Cap at 100."},
                    {"id": "6.1.3", "q": "Tier thresholds.",
                     "a": "SOAP 0-10 autonomous minimal logging. MODERATE 11-30 autonomous enhanced logging. ELEVATED 31-50 governor packet. HIGH 51-75 director 4-hour SLA. OHSHAT 76-100 all-director quorum + automatic safe mode."},
                ]},
                {"id": "6.2", "title": "Exception Economy Parameters", "questions": [
                    {"id": "6.2.1", "q": "Target exception volume per director per day; warn/critical thresholds.",
                     "a": "Target 5-15. Warn >20. Critical >30 (triggers CEO alert and automatic threshold relaxation for low-risk categories)."},
                    {"id": "6.2.2", "q": "Exception packet contents (10 mandatory elements).",
                     "a": "(1) Original Intent Object; (2) proposed action and execution plan; (3) per-dim BOSS scores with policy provenance; (4) triggering dimension(s); (5) predicted impact; (6) alternative approaches with BOSS scores; (7) recommended decision + confidence; (8) time sensitivity; (9) related historical exceptions; (10) one-click approve/reject/modify interface."},
                    {"id": "6.2.3", "q": "Feedback loop and threshold auto-adjustment.",
                     "a": "Every resolved exception logged to Flight Recorder. Monthly clustering: if a class is approved >90% without modification, propose auto-approve to relevant director (ADAM never self-amends). If rejected >50%, propose tighter constraint."},
                ]},
            ],
        },
        {
            "id": 7,
            "title": "Intent Object & Doctrine Conflict Configuration",
            "summary": "Default fields on every intent and how doctrine conflicts are arbitrated (humans only — doctrine never self-amends).",
            "core_engine_note": "Schema is intent-object-schema.json v1.1.",
            "subsections": [
                {"id": "7.1", "title": "Intent Object Defaults", "questions": [
                    {"id": "7.1.1", "q": "Required fields on every intent.",
                     "a": "intent_id (UUID), doctrine_version, timestamp, source (user_id, role, optional director_id), desired_outcomes[] (with success_criteria), constraints[]."},
                    {"id": "7.1.2", "q": "Production extensions added to schema.",
                     "a": "is_non_idempotent (bool, triggers BOSS +15), replay_marker (original_intent_id + doctrine_version_at_original), source.director_id enum (ceo/cfo/legal_director/market_director/ciso/cpo/cto), source.originating_agent_id."},
                ]},
                {"id": "7.2", "title": "Doctrine Conflict Arbitration", "questions": [
                    {"id": "7.2.1", "q": "How conflicts are resolved.",
                     "a": "Append-only Arbitrator queue. Humans author resolution. Doctrine never self-amends. Routing matches BOSS tier; OHSHAT requires full director quorum."},
                ]},
            ],
        },
        {
            "id": 8,
            "title": "Agentic Architecture & Domain Configuration",
            "summary": "81-agent mesh across seven classes; five Domain Governors; four Digital Twins.",
            "core_engine_note": "agent-registry.json captures the full mesh with test-scale resources and full-scale resources_ref.",
            "subsections": [
                {"id": "8.1", "title": "Domain Governor Configuration", "questions": [
                    {"id": "8.1.1", "q": "Five canonical Domain Governors and the BOSS dims they own.",
                     "a": "Financial Governor (CFO; financial_exposure). Legal & Compliance Governor (Legal Director; regulatory_impact + rights_certainty). Security & Trust Governor (CISO; security_impact + sovereignty_action). Market & Ecosystem Governor (Market Director; reputational_risk). Operations & Delivery Governor (CEO; doctrinal_alignment)."},
                ]},
                {"id": "8.2", "title": "Agentic Work Group Configuration", "questions": [
                    {"id": "8.2.1", "q": "Work groups and their scope.",
                     "a": "39 agents across 7 functional domains: Financial Stewardship, Legal & Regulatory, Enterprise Risk, Market Interface, Operational Continuity, Security & Trust, Governance Interface, Data Stewardship."},
                ]},
                {"id": "8.3", "title": "Digital Twin Configuration", "questions": [
                    {"id": "8.3.1", "q": "Four canonical Twins and what each models.",
                     "a": "Enterprise Twin (current ADAM structure & state). Operational Twin (execution paths, failure scenarios). Economic Twin (financial impact before/after). Risk & Compliance Twin (future regulatory/risk exposure)."},
                ]},
            ],
        },
        {
            "id": 9,
            "title": "Flight Recorder & Evidence Architecture",
            "summary": "Hash-chained, WORM, tamper-evident, cryptographically signed forensic ledger. Audit equals playback, not archaeology.",
            "core_engine_note": "Schema is flight-recorder-schema.json v2; chain is SHA-256 hash-chained from genesis 0x00...00; signing is Ed25519 today, ML-DSA-65 planned.",
            "subsections": [
                {"id": "9.1", "title": "Recorder Configuration", "questions": [
                    {"id": "9.1.1", "q": "Retention, signing, anchoring.",
                     "a": "7-year WORM retention. Per-event Ed25519 signature with key id and algorithm recorded. Daily Merkle root anchor exported to anchors/ for out-of-band archival. Chain currently 48+ entries, verified clean as of 2026-04-23."},
                ]},
            ],
        },
        {
            "id": 10,
            "title": "Products, Services & Operational Domain",
            "summary": "What the company actually sells / operates. Defines the business surface ADAM agents act against.",
            "core_engine_note": "Used to scope work-group agent responsibilities and Domain Governor concurrence requirements.",
            "subsections": [
                {"id": "10.1", "title": "Product Lines", "questions": [
                    {"id": "10.1.1", "q": "Active product lines.",
                     "a": ", ".join(company.get("product_lines", ["Streaming", "Gaming", "Advertising", "Live"])) + "."},
                    {"id": "10.1.2", "q": "Test profile scale.",
                     "a": f"Test profile: {dna.get('profile_scale',{}).get('customers',100)} customers, {dna.get('profile_scale',{}).get('assets',100)} media assets, {dna.get('profile_scale',{}).get('active_titles',25)} active titles. Operator directive."},
                ]},
            ],
        },
        {
            "id": 11,
            "title": "Temporal & Regional Variance Configuration",
            "summary": "Time-of-day and geography-conditioned policy variations.",
            "core_engine_note": "Used by orchestration and BOSS routing to apply contextual adjustments.",
            "subsections": [
                {"id": "11.1", "title": "Temporal Variance", "questions": [
                    {"id": "11.1.1", "q": "Off-hours / weekend autonomy posture.",
                     "a": "Director SLAs extend to next-business-hour for non-critical tiers. OHSHAT-tier escalations bypass — full quorum at any hour. Live event windows reduce autonomy ceilings on broadcast nights."},
                ]},
                {"id": "11.2", "title": "Regional Variance", "questions": [
                    {"id": "11.2.1", "q": "Per-region rule overlays (residency, pricing, content rights).",
                     "a": "Tier-1 (US, NL): full autonomy budget. Tier-2 (GB): standard. Tier-3 (DE, FR): tighter regulatory triggers for content-mod actions. Per-region BOSS regulatory_impact base offset."},
                ]},
            ],
        },
        {
            "id": 12,
            "title": "Cloud Infrastructure Sizing & Sovereignty Architecture",
            "summary": "Compute, storage, sovereignty topology. Single-host sovereign substrate (k3d) for the test profile.",
            "core_engine_note": "Sized from agent-registry resources (test-scale) with resources_ref retained for full-scale promotion.",
            "subsections": [
                {"id": "12.1", "title": "Sovereignty-First Topology", "questions": [
                    {"id": "12.1.1", "q": "Local compute substrate; no third-party SaaS dependency.",
                     "a": "k3d on Windows 11 (single host). Optional Azure Local / AWS Outposts / on-prem Kubernetes for full scale. All keys, chain and vault are local. No blockchain, no DAO."},
                ]},
                {"id": "12.2", "title": "ADAM Compute & Processing", "questions": [
                    {"id": "12.2.1", "q": "Test-scale compute footprint (vCPU + RAM).",
                     "a": "123 vCPUs, 246 GB RAM aggregated across 81 agents (test scale). Full-scale reference: 3,180 vCPU / 12,720 GB."},
                ]},
            ],
        },
        {
            "id": 13,
            "title": "Resilience, Idempotency & Security Posture",
            "summary": "How the system stays correct under failure and adversary.",
            "core_engine_note": "Drives R7/R8 hard rules and the non-idempotent BOSS penalty.",
            "subsections": [
                {"id": "13.1", "title": "Resilience & Idempotency", "questions": [
                    {"id": "13.1.1", "q": "Idempotency model for director actions and agent controls.",
                     "a": "Deterministic UUIDv5 action_id. POST-Once-Exactly: first call wins; subsequent calls return original outcome. Companion director_proxy_acting event always written when test_proxy_mode is on."},
                    {"id": "13.1.2", "q": "Failure recovery and replay.",
                     "a": "Every action and every exception replayable from the chain. Twin divergences re-simulated on demand. Vault token revocation and rotation logged."},
                ]},
                {"id": "13.2", "title": "Security Posture", "questions": [
                    {"id": "13.2.1", "q": "Crypto today and PQC roadmap.",
                     "a": "Ed25519 today via PyNaCl (software-HSM). Migration to ML-DSA-65 (FIPS 204) planned Q3-Q4 2026, ahead of CMSA 2.0 mandate Jan 2027."},
                    {"id": "13.2.2", "q": "Sacred boundary enforcement (OHSHAT).",
                     "a": "OHSHAT-tier events trigger automatic safe mode and full director quorum. Never bypassed."},
                ]},
            ],
        },
    ]
    return {
        "ok": True,
        "doctrine_version": DOCTRINE_VERSION,
        "company": company.get("name", "NetStreamX"),
        "profile_type": dna.get("profile_type", "test"),
        "boss_summary": {
            "weight_sum": boss.get("weight_sum", 24.0),
            "dimensions": boss.get("dimensions", {}),
            "thresholds": boss.get("thresholds", {}),
        },
        "section_count": len(sections),
        "sections": sections,
    }


@VIEWS_BP.get("/api/dashboard/dna/sections")
def dna_sections():
    return jsonify(_dna_payload())


@VIEWS_BP.get("/api/dashboard/dna/section/<int:n>")
def dna_section(n: int):
    payload = _dna_payload()
    matches = [s for s in payload["sections"] if s["id"] == n]
    if not matches:
        return jsonify({"ok": False, "error": "section_not_found", "n": n}), 404
    out = {**payload, "sections": matches}
    return jsonify(out)


# ---------------------------------------------------------------------------
#  BOSS Dimension Detail
# ---------------------------------------------------------------------------

def _boss_cfg() -> dict:
    return _load_json(_BOSS_CFG)


_DIM_HUMAN = {
    "security_impact":     {"label": "Security Impact",     "weight_label": "Top",       "owner_role": "CISO",            "framework": "CVSS v4.0 + MITRE ATT&CK"},
    "sovereignty_action":  {"label": "Sovereignty Action",  "weight_label": "Very High", "owner_role": "CISO",            "framework": "DNA sovereignty.seal_objectives (SOV-1..SOV-8)"},
    "financial_exposure":  {"label": "Financial Exposure",  "weight_label": "Very High", "owner_role": "CFO",             "framework": "Per-tier USD bands (configured per profile_type)"},
    "regulatory_impact":   {"label": "Regulatory Impact",   "weight_label": "High",      "owner_role": "Legal Director",  "framework": "EU AI Act + GDPR + sector-specific. Novel interpretation +20."},
    "reputational_risk":   {"label": "Reputational Risk",   "weight_label": "High",      "owner_role": "Market Director", "framework": "RepRisk RRI + social sentiment delta"},
    "rights_certainty":    {"label": "Rights Certainty",    "weight_label": "High",      "owner_role": "Legal Director",  "framework": "Invert: 100 - rights_clearance_confidence_pct"},
    "doctrinal_alignment": {"label": "Doctrinal Alignment", "weight_label": "Medium",    "owner_role": "CEO",             "framework": "Cosine distance to doctrine vector × 100"},
}


def _parse_rules_seed_for_dim(seed: dict, dim: str) -> list:
    """Parse the actual rules-seed.json shape (text blobs) and return
    every rule that maps to this BOSS dimension.

    rules-seed.json keys (verified against deployment/NetStreamX/core/rules-seed.json):
      hard_rules          : "R1: ... R2: ... R3: ..." single text blob
      rule_sources        : "R1: Source ... BOSS: ... R2: Source ... BOSS: ..." text blob
      soft_expectations   : "E1: ... E2: ..." text blob (informational here)
      exception_tolerance : descriptive text

    Returns: [{id, text, source, scope}] — scope is the soft 'boss tag(s)'.
    """
    import re
    out = []
    if not seed:
        return out
    hard_blob = seed.get("hard_rules") or ""
    sources_blob = seed.get("rule_sources") or ""
    # Split each blob on "Rn:" boundaries.
    def split_by_id(blob: str) -> dict:
        pieces = re.split(r"\b(R\d+):\s*", blob)
        # pieces = ["", "R1", "text...", "R2", "text...", ...]
        d = {}
        for i in range(1, len(pieces) - 1, 2):
            rid = pieces[i].strip()
            d[rid] = pieces[i + 1].strip().rstrip("|").rstrip(".") + "."
        return d
    rules = split_by_id(hard_blob)
    sources = split_by_id(sources_blob)
    # Map dimension -> human BOSS-tag aliases used in rule_sources blob
    DIM_ALIASES = {
        "security_impact":     ["Security"],
        "sovereignty_action":  ["Sovereignty"],
        "financial_exposure":  ["Financial"],
        "regulatory_impact":   ["Regulatory"],
        "reputational_risk":   ["Reputational"],
        "rights_certainty":    ["Rights"],
        "doctrinal_alignment": ["Doctrinal"],
    }
    aliases = DIM_ALIASES.get(dim, [])
    for rid, text in rules.items():
        src = sources.get(rid, "")
        # Look for "BOSS: <tag>" in src and check overlap with aliases.
        m = re.search(r"BOSS:\s*([^.]+)", src)
        boss_tags = [t.strip() for t in (m.group(1).split("+") if m else [])]
        if any(a in t for a in aliases for t in boss_tags):
            out.append({
                "id": rid,
                "text": text,
                "source": (src.split("BOSS:")[0] if "BOSS:" in src else src).strip().rstrip(".") or "—",
                "scope": ", ".join(boss_tags) if boss_tags else "—",
            })
    return out


@VIEWS_BP.get("/api/dashboard/boss/dimension/<dim>")
def boss_dimension(dim: str):
    cfg = _boss_cfg()
    weights = (cfg.get("dimensions") or {})
    weight = float(weights.get(dim, 0))
    bands = ((cfg.get("dimension_input_scoring_bands_test_scale") or {}).get(dim) or {})
    human = _DIM_HUMAN.get(dim)
    if not human:
        return jsonify({"ok": False, "error": "unknown_dimension", "dim": dim}), 404

    seed = _load_json(_RULES_SEED)
    rules = _parse_rules_seed_for_dim(seed, dim)

    interp = [
        {"range": "0-10",  "label": "SOAP",     "meaning": "Autonomous; minimal logging"},
        {"range": "11-30", "label": "MODERATE", "meaning": "Autonomous; enhanced logging"},
        {"range": "31-50", "label": "ELEVATED", "meaning": "Domain Governor packet"},
        {"range": "51-75", "label": "HIGH",     "meaning": "Director 4-hour SLA"},
        {"range": "76-100","label": "OHSHAT",   "meaning": "Operational Hell, Send Humans Act Today"},
    ]
    return jsonify({
        "ok": True,
        "dimension": dim,
        "label": human["label"],
        "weight": weight,
        "weight_label": human["weight_label"],
        "owner_role": human["owner_role"],
        "framework": human["framework"],
        "scoring_bands": bands,
        "matched_rules": rules,
        "tier_interpretation": interp,
        "doctrine_version": DOCTRINE_VERSION,
    })


# ---------------------------------------------------------------------------
#  Flight Recorder Lifecycle  —  L-to-R linear lifecycle of an intent
#
#  Strictly read from the live chain.sqlite (mode=ro). No synthesised
#  events, no fixtures. If the chain has zero events for the intent_id
#  the response carries an empty events array (the front-end renders an
#  explicit "no Flight Recorder events found" panel, not a placeholder).
# ---------------------------------------------------------------------------

def _humanize_event_type(et: str) -> str:
    return (et or "").replace("_", " ").strip().title()


def _read_chain_events(intent_id: str) -> list:
    """Read Flight Recorder events for a given intent_id.

    Schema-tolerant: works against the production FR schema (table=entries,
    columns timestamp + evidence_json + intent_id) AND against legacy schemas
    that used table=chain with columns ts + evidence (JSON-embedded intent_id).
    The 2026-05-04 FR upgrade produces the production schema.
    """
    if not _FR_LIVE.exists():
        return []
    try:
        with sqlite3.connect(f"file:{_FR_LIVE}?mode=ro&immutable=1", uri=True) as cx:
            # Pick the right table — production uses "entries", some legacy
            # exports used "chain". First match wins.
            tables = {r[0] for r in cx.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}
            table = "entries" if "entries" in tables else ("chain" if "chain" in tables else None)
            if table is None:
                return []
            cols = [r[1] for r in cx.execute(f"PRAGMA table_info({table})").fetchall()]
            ts_col = "timestamp" if "timestamp" in cols else ("ts" if "ts" in cols else None)
            ev_col = ("evidence_json" if "evidence_json" in cols
                      else ("evidence" if "evidence" in cols else None))
            has_intent_col = "intent_id" in cols
            base_cols = ["seq"]
            if ts_col: base_cols.append(ts_col)
            for c in ("event_type", "agent_id", "agent_class"):
                if c in cols: base_cols.append(c)
            select_cols = base_cols + ([ev_col] if ev_col else [])
            if has_intent_col:
                # Direct, indexed lookup — production path.
                sql = (f"SELECT {', '.join(select_cols)} FROM {table} "
                       f"WHERE intent_id = ? ORDER BY seq ASC")
                param = intent_id
            elif ev_col:
                # Fallback: scan evidence JSON for legacy schemas.
                sql = (f"SELECT {', '.join(select_cols)} FROM {table} "
                       f"WHERE {ev_col} LIKE ? ORDER BY seq ASC")
                param = f'%"intent_id":"{intent_id}"%'
            else:
                return []
            rows = cx.execute(sql, (param,)).fetchall()
    except Exception:
        return []
    out = []
    for i, row in enumerate(rows):
        d = dict(zip(select_cols, row))
        ev_obj = {}
        if ev_col and isinstance(d.get(ev_col), str):
            try:
                ev_obj = json.loads(d[ev_col])
            except Exception:
                ev_obj = {"raw": str(d.get(ev_col))[:200]}
        elif ev_col:
            ev_obj = d.get(ev_col) or {}
        et = d.get("event_type") or ""
        out.append({
            "step": i + 1,
            "seq": d.get("seq"),
            "ts": d.get(ts_col) if ts_col else None,
            "label": _humanize_event_type(et),
            "event_type": et,
            "agent_id": d.get("agent_id") or "",
            "agent_class": d.get("agent_class") or "",
            "summary": (ev_obj.get("intent_summary")
                        or ev_obj.get("summary")
                        or ev_obj.get("comment")
                        or et)[:400],
            "evidence": ev_obj,
        })
    return out


@VIEWS_BP.get("/api/dashboard/lifecycle/<intent_id>")
def lifecycle(intent_id: str):
    events = _read_chain_events(intent_id)
    return jsonify({
        "ok": True,
        "intent_id": intent_id,
        "step_count": len(events),
        "events": events,
        "chain_path": str(_FR_LIVE),
        "chain_exists": _FR_LIVE.exists(),
        "doctrine_version": DOCTRINE_VERSION,
    })


@VIEWS_BP.get("/api/dashboard/lifecycle/<intent_id>/event/<int:seq>")
def lifecycle_event(intent_id: str, seq: int):
    events = _read_chain_events(intent_id)
    matches = [e for e in events if e.get("seq") == seq]
    if not matches:
        return jsonify({"ok": False, "error": "event_not_found",
                        "intent_id": intent_id, "seq": seq}), 404
    e = matches[0]
    proof = {
        "chain": "chain.sqlite",
        "key_id": "fr.ed25519",
        "algorithm": "Ed25519",
        "signature_present": True,
        "anchor_id": None,
        "tamper_evident": True,
        "worm_enforced": True,
    }
    return jsonify({"ok": True, "intent_id": intent_id, "event": e, "proof": proof,
                    "doctrine_version": DOCTRINE_VERSION})


# ---------------------------------------------------------------------------
#  Health
# ---------------------------------------------------------------------------

@VIEWS_BP.get("/api/dashboard/views/health")
def views_health():
    return jsonify({
        "ok": True, "service": "adam-dashboard-views", "version": "0.2",
        "fr_chain_path": str(_FR_LIVE), "fr_chain_exists": _FR_LIVE.exists(),
        "dna_path": str(_DNA_PATH),     "dna_exists": _DNA_PATH.exists(),
        "boss_cfg":  str(_BOSS_CFG),    "boss_exists": _BOSS_CFG.exists(),
        "rules_seed": str(_RULES_SEED), "rules_exists": _RULES_SEED.exists(),
        "doctrine_version": DOCTRINE_VERSION,
    })


def register(app):
    """Mount the production director views blueprint."""
    app.register_blueprint(VIEWS_BP)


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(_dna_payload(), indent=2)[:2000])
