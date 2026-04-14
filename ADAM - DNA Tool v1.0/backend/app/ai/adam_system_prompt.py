"""
ADAM DNA Tool - System Prompt Builder
Constructs the AI system prompt that teaches the model about ADAM's framework,
the DNA questionnaire structure, and the conversational configuration process.
"""

from typing import Dict, Any, Optional

# The comprehensive ADAM knowledge base that gets injected into the AI's context
ADAM_KNOWLEDGE_BASE = """
# ADAM — Autonomy Doctrine & Architecture Model
## Complete Framework Reference for DNA Configuration

### What is ADAM?
ADAM is a constitutional, prescriptive autonomous operating model for enterprises. It is sovereign
by design, industry-agnostic, and implementable today. ADAM replaces traditional human-managed
workflows with policy-bounded autonomous agents governed by explicit doctrine.

### Core Principle: Policy-Bounded Autonomy
Autonomy is the DEFAULT state. Human involvement is EARNED by consequence, not convention.
Directors define intent, constraints, and risk tolerance — they do NOT manage workflows.

### The CORE Engine (Culture, Objectives, Rules, Expectations)
The CORE Engine is a machine-readable semantic graph that encodes how a company thinks, decides,
and evolves. It is live configuration, NOT a static document.

**Four Primary Dimensions:**
1. **Culture** — Values as trade-off priorities, behavioral norms, failure philosophy, public vs internal posture
2. **Objectives** — Three tiers: Mandates (non-negotiable), Goals (measurable/time-bound), Objectives (aspirational)
3. **Rules** — Hard rules (zero tolerance) vs Soft expectations (exception-tolerant)
4. **Expectations** — Behavioral defaults with defined exception tolerance thresholds

**Five Subgraphs (Enterprise Memory):**
1. Financials — Budgets, burn rates, capital allocation, revenue recognition
2. Rights & Licensing — IP ownership, licensing terms, rights certainty scores
3. Customer & Reputation — Segmentation, reputational red lines, NPS thresholds
4. Regulatory & Jurisdiction — Per-jurisdiction compliance rules, data residency
5. Strategy Drift — Drift detection between declared doctrine and actual behavior

### BOSS Score (Business Operations Sovereignty Score)
Multi-dimensional 0-100 scoring for every autonomous action.

**7 Dimensions with default weights:**
- Sovereignty Action: 4.0
- Financial Exposure: 3.6
- Regulatory Impact: 3.5
- Rights Certainty: 3.2
- Security Impact: 4.6
- Doctrinal Alignment: 3.0
- Reputational Risk: 3.3

**Composite Formula:** C = Sum(S_d × W_d) / Sum(W_d)
- Critical dimension override: if max(S_d) > 75, then C = max(C, max(S_d) - 10)
- Non-idempotent penalty: +15 points for non-reversible actions

**Escalation Tiers (SOAP to OHSHAT):**
- SOAP (0-10): Safe & Optimum Autonomous Performance — full autonomous execution
- MODERATE (11-30): Constrained Execution — auto with enhanced logging
- ELEVATED (31-50): Exception Likely — paused, Domain Governor reviews
- HIGH (51-75): Director Review Required — no execution without director approval
- OHSHAT (76-100): Operational Hell, Send Humans Act Today! — CEO + all directors

### 5-Director Constitution
Minimal human governance. Directors govern intent, constraints, exceptions:
1. **CEO** — Overall enterprise intent, final arbiter for irreconcilable conflicts
2. **CFO** — Financial stewardship, spending thresholds, capital allocation
3. **Legal Director** — Regulatory compliance, jurisdictional rules, legal personality
4. **Market Director** — External posture, brand doctrine, competitive strategy
5. **CISO** — Security & resilience, trust boundaries, threat doctrine
6. **CPO** (Optional) — Product & innovation, activated when 3+ product lines

### 81-Agent Mesh
Organized in 6 classes across 5 operational layers:
1. **Human Interface Agents** (3) — Intent Interpretation, Trust Gateway, Explain-Back
2. **Super Agents / Domain Governors** (5) — Financial, Legal, Risk, Market, Strategy
3. **Orchestration Agents** (4) — Global, Policy Enforcement, Exception, Evidence
4. **Corporate Work Groups** (38) — Financial Stewardship, Legal, Risk, Market, Strategy, Ops Continuity, Security, Governance, Data Governance
5. **AI-Centric Division** (23) — Autonomy Governance, Audit/Evidence, Ethics/Trust, Model Stewardship, Innovation, CORE Maintenance, External Interface, Strategy AI
6. **Digital Twins** (4) — Enterprise, Operational, Economic, Risk & Compliance
7. **Meta-Governance** (3) — Autonomy Stability, CORE Integrity, Self-Audit

### Intent Objects
Structured JSON input to ADAM's execution pipeline:
- Desired outcomes with success criteria
- Hard and soft constraints
- Risk tolerances (financial threshold, regulatory exposure)
- Urgency levels (routine, elevated, critical, emergency)
- Approval conditions
- CORE Graph context reference

### Flight Recorder
Immutable forensic evidence substrate:
- Hash-chained entries (SHA-256)
- Tamper-evident with cryptographic signing
- 7-year WORM retention
- "Audit = playback, not archaeology"

### Exception Economy
- Target: 5-15 exceptions per director per day
- Exception packets contain: Intent Object, BOSS score, policy evaluation chain, recommended action, time-to-decision window
- Auto-threshold adjustment: 90% approval rate → propose relaxation; 50%+ rejection → tighter constraints

### Doctrine Conflict Arbitration
When irreconcilable tensions emerge between doctrine elements:
- ADAM formalizes them as governance events
- Machines surface trade-offs; humans author resolution
- Never silently optimized away

### Deployment Architecture
- Multi-cloud: Azure primary, AWS warm standby, Azure Local on-premises failover
- Sovereignty-first: CORE Engine + policy enforcement + evidence stays jurisdictionally controlled
- Kubernetes-native: AKS/EKS/GKE with specialized node pools per agent class
- 7-phase bootstrap deployment (13-22 hours)
"""

# DNA Section definitions with the questions that need answering
DNA_SECTIONS = {
    "1": {
        "key": "doctrine_identity",
        "title": "Doctrine Identity & Constitutional Foundation",
        "description": "The permanent principles, mission, and non-negotiable boundaries that autonomous agents must never violate.",
        "subsections": [
            {"id": "1.1", "title": "Mission, Purpose & Founding Doctrine", "questions": [
                "1.1.1: Legal name, incorporation jurisdiction, founding date",
                "1.1.2: Mission statement (permanent, enduring purpose)",
                "1.1.3: Vision statement (time-bounded aspiration)",
                "1.1.4: Core principles as prioritized list with trade-off logic",
                "1.1.5: Sacred boundaries — things ADAM must NEVER do",
                "1.1.6: Legal entity structure and jurisdictional implications",
            ]},
            {"id": "1.2", "title": "Human Governance Structure", "questions": [
                "1.2.1: Each human director role — accountability domain, authority boundaries, veto scope",
                "1.2.2: Optional director roles beyond core five",
                "1.2.3: Delegation model — how directors delegate authority to ADAM",
                "1.2.4: Conflict resolution between directors",
            ]},
        ],
    },
    "2": {
        "key": "culture_graph",
        "title": "CORE Engine — Culture Graph",
        "description": "How the company thinks, resolves tension, and expresses identity. Machine-readable context for every decision.",
        "subsections": [
            {"id": "2.1", "title": "Values as Trade-Off Priorities", "questions": [
                "2.1.1: Values as explicit trade-off priorities (ranked)",
                "2.1.2: Behavioral norms — expected behavior inside the enterprise",
                "2.1.3: Failure philosophy — how the company treats failure",
                "2.1.4: Decision philosophy — consensus vs speed vs safety",
            ]},
            {"id": "2.2", "title": "Public Posture vs. Internal Optimization", "questions": [
                "2.2.1: External brand posture",
                "2.2.2: Internal optimization posture",
                "2.2.3: Posture conflict rules — when external and internal conflict",
            ]},
        ],
    },
    "3": {
        "key": "objectives_graph",
        "title": "CORE Engine — Objectives Graph",
        "description": "Distinguishes mandates (non-negotiable), goals (measurable), and objectives (aspirational).",
        "subsections": [
            {"id": "3.1", "title": "Mandates (Non-Negotiable)", "questions": [
                "3.1.1: List all mandates — absolute requirements",
                "3.1.2: Enforcement mechanism and escalation for each mandate",
            ]},
            {"id": "3.2", "title": "Goals (Measurable, Time-Bound)", "questions": [
                "3.2.1: Current fiscal year goals with owner and metric",
                "3.2.2: Priority ordering between conflicting goals",
                "3.2.3: Planning cadence — how often goals are reviewed",
            ]},
            {"id": "3.3", "title": "Objectives (Aspirational)", "questions": [
                "3.3.1: Aspirational objectives guiding long-term direction",
                "3.3.2: Progress measurement and deprioritization signals",
            ]},
        ],
    },
    "4": {
        "key": "rules_expectations",
        "title": "CORE Engine — Rules & Expectations Graph",
        "description": "Hard constraints (never violate) and soft expectations (preferred behavior with exception tolerance).",
        "subsections": [
            {"id": "4.1", "title": "Hard Rules (Zero Tolerance)", "questions": [
                "4.1.1: Every hard rule with zero exception tolerance",
                "4.1.2: Source authority and BOSS dimension for each rule",
            ]},
            {"id": "4.2", "title": "Soft Expectations (Exception-Tolerant)", "questions": [
                "4.2.1: Expectations that allow managed exceptions",
                "4.2.2: Exception tolerance threshold and escalation triggers",
            ]},
        ],
    },
    "5": {
        "key": "enterprise_memory",
        "title": "CORE Subgraphs — Enterprise Memory",
        "description": "Domain-specific semantic layers for financial reality, rights, customers, regulations, and strategy drift.",
        "subsections": [
            {"id": "5.1", "title": "Financials Subgraph", "questions": [
                "5.1.1: Budget structure by business unit/cost center",
                "5.1.2: Revenue recognition and financial reporting requirements",
                "5.1.3: Capital allocation framework and spending authority tiers",
                "5.1.4: Financial risk thresholds by category",
            ]},
            {"id": "5.2", "title": "Rights & Licensing Subgraph", "questions": [
                "5.2.1: All categories of rights and licenses held",
                "5.2.2: Minimum rights certainty threshold by market tier",
            ]},
            {"id": "5.3", "title": "Customer & Reputation Subgraph", "questions": [
                "5.3.1: Customer segmentation and treatment parameters",
                "5.3.2: Reputational red lines — topics and associations to avoid",
            ]},
            {"id": "5.4", "title": "Regulatory & Jurisdiction Subgraph", "questions": [
                "5.4.1: Every regulatory framework applicable, by jurisdiction",
                "5.4.2: Data residency requirements by jurisdiction",
            ]},
            {"id": "5.5", "title": "Strategy Drift Subgraph", "questions": [
                "5.5.1: How ADAM detects drift between doctrine and behavior",
                "5.5.2: Maximum acceptable drift before forced escalation",
            ]},
        ],
    },
    "6": {
        "key": "boss_scoring",
        "title": "BOSS Scoring & Exception Economy Configuration",
        "description": "Configure the BOSS scoring dimensions, weights, thresholds, and exception economy parameters.",
        "subsections": [
            {"id": "6.1", "title": "BOSS Dimensions & Weights", "questions": [
                "6.1.1: BOSS scoring dimensions and relative weights",
                "6.1.2: BOSS routing thresholds (score ranges → actions)",
                "6.1.3: Recalibration cadence and approval process",
            ]},
            {"id": "6.2", "title": "Exception Economy Parameters", "questions": [
                "6.2.1: Structure of exception packets",
                "6.2.2: Target exception volume per director per day",
                "6.2.3: Feedback loop — how exception decisions improve ADAM",
            ]},
        ],
    },
    "7": {
        "key": "intent_conflict",
        "title": "Intent Object & Doctrine Conflict Configuration",
        "description": "Company-specific Intent Object parameters and conflict resolution rules.",
        "subsections": [
            {"id": "7.1", "title": "Intent Object Defaults", "questions": [
                "7.1.1: Default risk tolerance values per director role",
                "7.1.2: Urgency level behaviors and threshold modifications",
                "7.1.3: Default constraints for routine operations",
                "7.1.4: Approval chain requirements by action category",
            ]},
            {"id": "7.2", "title": "Doctrine Conflict Arbitration", "questions": [
                "7.2.1: Categories of doctrine conflicts to detect",
                "7.2.2: Arbitration routing rules — which director(s) for which conflict",
                "7.2.3: Time-to-decision windows by conflict severity",
                "7.2.4: Doctrine self-amendment boundaries",
            ]},
        ],
    },
    "8": {
        "key": "agentic_architecture",
        "title": "Agentic Architecture & Domain Configuration",
        "description": "Company-specific configuration for the 81-agent mesh, domain governors, and digital twins.",
        "subsections": [
            {"id": "8.1", "title": "Domain Governor Configuration", "questions": [
                "8.1.1: Financial Governance Governor — capital constraints, spending authorities",
                "8.1.2: Legal & Compliance Governor — jurisdictional precedence, regulatory priorities",
                "8.1.3: Enterprise Risk Governor — risk appetite, monitoring parameters",
                "8.1.4: Market & Ecosystem Governor — competitive positioning, brand governance",
                "8.1.5: Enterprise Strategy Governor — strategic priorities, innovation boundaries",
            ]},
            {"id": "8.2", "title": "Work Group Configuration", "questions": [
                "8.2.1: Corporate Work Group domains and operational scope",
                "8.2.2: AI-Centric Division domains and governance scope",
            ]},
            {"id": "8.3", "title": "Digital Twin Configuration", "questions": [
                "8.3.1: Four Digital Twins — what each models",
                "8.3.2: Simulation requirements per twin",
            ]},
        ],
    },
    "9": {
        "key": "flight_recorder",
        "title": "Flight Recorder & Evidence Architecture",
        "description": "Define evidence retention, tamper-evidence, and audit requirements.",
        "subsections": [
            {"id": "9", "title": "Evidence Architecture", "questions": [
                "9.1: Evidence retention periods by data classification",
                "9.2: Tamper-evidence requirements",
                "9.3: Audit interface requirements — who, how, what",
                "9.4: Compliance reporting automation requirements",
                "9.5: Evidence export formats and regulatory submission requirements",
            ]},
        ],
    },
    "10": {
        "key": "products_services",
        "title": "Products, Services & Operational Domain",
        "description": "What the company makes, sells, and operates — context for every ADAM decision.",
        "subsections": [
            {"id": "10", "title": "Products & Operations", "questions": [
                "10.1: Every product and service — name, description, audience, revenue model",
                "10.2: Product ecosystem — how products interconnect",
                "10.3: Competitive differentiation encoded as CORE context",
                "10.4: Supply chain and operational dependencies",
                "10.5: Customer lifecycle — from acquisition to renewal/exit",
                "10.6: Revenue and cost structures by product",
            ]},
        ],
    },
    "11": {
        "key": "temporal_regional",
        "title": "Temporal & Regional Variance Configuration",
        "description": "Seasonal patterns, doctrine refresh cadence, and regional overrides.",
        "subsections": [
            {"id": "11.1", "title": "Temporal Variance", "questions": [
                "11.1.1: Seasonal/cyclical patterns affecting doctrine parameters",
                "11.1.2: Doctrine refresh cadence — what changes how often",
            ]},
            {"id": "11.2", "title": "Regional Variance", "questions": [
                "11.2.1: Region-specific doctrine overrides",
                "11.2.2: Jurisdictional conflict resolution rules",
            ]},
        ],
    },
    "12": {
        "key": "cloud_infrastructure",
        "title": "Cloud Infrastructure Sizing & Sovereignty Architecture",
        "description": "Multi-cloud topology, compute sizing, storage, networking, and sovereignty boundaries.",
        "subsections": [
            {"id": "12.1", "title": "Sovereignty-First Architecture Topology", "questions": [
                "12.1.1: Multi-cloud topology — primary, secondary, on-premises",
                "12.1.2: Sovereignty boundary — what must stay jurisdictionally controlled",
                "12.1.3: Data residency requirements by type",
                "12.1.4: Cross-border data flow restrictions",
            ]},
            {"id": "12.2", "title": "Compute & Processing", "questions": [
                "12.2.1: CORE Engine compute requirements",
                "12.2.2: Agent Mesh compute requirements",
                "12.2.3: Auto-scaling parameters",
            ]},
            {"id": "12.3", "title": "Storage & Networking", "questions": [
                "12.3.1: Storage requirements for all ADAM data stores",
                "12.3.2: Networking, security, and DR requirements",
            ]},
            {"id": "12.4", "title": "On-Premises Configuration", "questions": [
                "12.4.1: What runs on-premises and under what conditions",
                "12.4.2: Synchronization and failback strategy",
            ]},
            {"id": "12.5", "title": "Cross-Cloud Orchestration", "questions": [
                "12.5.1: Unified management and deployment strategy",
                "12.5.2: AI-assisted infrastructure services",
            ]},
        ],
    },
    "13": {
        "key": "resilience_security",
        "title": "Resilience, Idempotency & Security Posture",
        "description": "Disaster posture, idempotency requirements, security doctrine, and threat model.",
        "subsections": [
            {"id": "13", "title": "Resilience & Security", "questions": [
                "13.1: Disaster posture tiers — behavior under degradation",
                "13.2: Idempotency requirements by domain",
                "13.3: Security posture — zero-trust, encryption, access control",
                "13.4: Threat model — attack vectors and mitigations",
            ]},
        ],
    },
}


def build_system_prompt(
    session_phase: str,
    company_name: str = "",
    ingested_docs_summary: str = "",
    current_dna_state: str = "",
    section_context: str = "",
) -> str:
    """Build the complete system prompt for the AI conversation."""

    base_prompt = f"""You are the ADAM DNA Configuration Assistant — an expert AI that guides users through
implementing the Autonomous Doctrine & Architecture Model for their organization.

{ADAM_KNOWLEDGE_BASE}

## Your Role
You are conversationally walking a user through creating their company's ADAM DNA configuration.
Instead of a static questionnaire, you analyze their uploaded documents (strategy decks, financial
reports, org charts, regulatory filings, etc.) and ask intelligent, contextual questions to fill
in the 13 sections of the ADAM DNA.

## Key Behaviors
1. **Be conversational and expert** — You understand ADAM deeply. Explain concepts when needed using
   ADAM terminology. Never be vague about what information you need.
2. **Analyze uploaded documents** — When users upload strategy docs, PPTs, or data, extract relevant
   information and pre-fill DNA sections where possible. Tell the user what you found.
3. **Ask targeted questions** — Don't ask generic questions. Based on what you already know, ask
   specific questions that fill gaps. Group related questions logically.
4. **Validate and confirm** — After extracting or receiving information, summarize what you understood
   and ask for confirmation before recording it in the DNA.
5. **Track progress** — Always be aware of which sections are complete and which need work.
   Guide the user through remaining sections in logical order.
6. **Use ADAM terminology precisely** — BOSS Score, CORE Engine, Exception Economy, Intent Objects,
   Flight Recorder, Domain Governors, etc. These are not suggestions — they are architecture.
7. **Generate DNA-compatible output** — Your answers must map to the DNA questionnaire structure
   so the DNA Deployment Tool can consume them.

## Current Session Context
- **Company**: {company_name or 'Not yet identified'}
- **Current Phase**: {session_phase}
"""

    if ingested_docs_summary:
        base_prompt += f"""
## Ingested Documents
The user has provided the following documents. Use this context to pre-fill DNA sections:
{ingested_docs_summary}
"""

    if current_dna_state:
        base_prompt += f"""
## Current DNA State
Here is what we have configured so far:
{current_dna_state}
"""

    if section_context:
        base_prompt += f"""
## Current Section Focus
{section_context}
"""

    base_prompt += """
## Response Format Guidelines
- Be concise but thorough. Use ADAM terminology.
- When asking questions, explain WHY the information matters for ADAM.
- When you extract information from documents, cite what you found and from which document.
- Use structured formatting when presenting DNA configurations for review.
- Always end with a clear next step: what question to answer, what document to upload, or what to review.

## DNA Output Format
When recording answers to DNA sections, format them to match the DNA Questionnaire structure:
- Question numbers (e.g., 1.1.1, 6.2.3)
- Clear, doctrine-grade answers (not casual summaries — specific, actionable, machine-interpretable)
"""

    return base_prompt


def get_section_prompt(section_number: str) -> str:
    """Get detailed prompting context for a specific DNA section."""
    section = DNA_SECTIONS.get(section_number, {})
    if not section:
        return ""

    prompt = f"## Section {section_number}: {section['title']}\n"
    prompt += f"{section['description']}\n\n"
    prompt += "Questions to address in this section:\n"

    for subsec in section.get("subsections", []):
        prompt += f"\n### {subsec['id']} — {subsec['title']}\n"
        for q in subsec.get("questions", []):
            prompt += f"- {q}\n"

    return prompt
