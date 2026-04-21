# ADAM × AGT Terminology Disambiguation Reference

**ADAM — Autonomy Doctrine & Architecture Model**  
**AGT — Agent Governance Toolkit (Microsoft, MIT License)**

Version 1.1 | April 2026 | ADAM AGT Light Plugin — aligned with ADAM book v1.4 (BOSS v3.2 canonical; 81+ Agent Mesh seven canonical classes)

---

## Purpose

When ADAM and AGT are deployed together, both frameworks use similar terminology for different concepts. Careless use of shared terms is a primary source of confusion in documentation, implementation, and governance communication. This reference provides unambiguous definitions for every shared term, with mandatory naming rules enforced in all ADAM AGT Light documentation and code.

The rules in this document are reflected in the code-level configuration at `config/agt-integration-config.yaml` (terminology_rules section).

---

## The Fundamental Principle

> ADAM defines **what** must be governed. AGT provides one implementation of **how** governance is enforced at runtime.

Any confusion between ADAM concepts and AGT concepts is architecturally significant — it implies that ADAM doctrine is being conflated with a specific runtime implementation. That conflation is the error this document prevents.

---

## Disambiguation Table

### 1. Agent Mesh / 81+ Agent Mesh

| Attribute | AGT Context | ADAM Context |
|---|---|---|
| **Term** | Agent Mesh | 81+ Agent Mesh (or: ADAM Agent Mesh) |
| **What it is** | A runtime communication protocol. Provides W3C DID-based cryptographic identity and IATP (Inter-Agent Trust Protocol) trust scoring (0-1000) for individual agents. | An enterprise topology of 81+ named agents across seven canonical classes (5 Domain Governors, 4 Orchestration, 3 Human Interface, 39 Corporate Work Groups, 23 AI-Centric Division, 4 Digital Twin, 3 Meta-Governance). Defines authority flows, domain boundaries, and agent relationships. |
| **Scope** | Technical — identity, transport security, trust scoring | Organizational — governance structure, authority hierarchy, agent responsibilities |
| **Defined by** | AGT (Microsoft open-source, MIT license) | ADAM (sovereign architecture, organization-specific) |

**Rule**: Never use bare "agent mesh" without a qualifier in ADAM contexts. Always specify either "AGT Agent Mesh" (the identity/communication protocol) or "ADAM's 81+ Agent Mesh" / "ADAM's agent topology" (the governance structure).

**Correct usage examples**:
- "The AGT Agent Mesh issues a DID to each agent in ADAM's 81+ Agent Mesh."
- "ADAM's 81+ Agent Mesh defines 5 Governor Agents; the AGT Agent Mesh assigns each a W3C DID."

**Incorrect usage examples**:
- ❌ "The agent mesh ensures agents are properly governed." *(Which mesh? What aspect?)*
- ❌ "Configure the agent mesh topology." *(Agent Mesh has no topology — the 81+ Agent Mesh does.)*

---

### 2. Policy Engine / CORE Engine

| Attribute | AGT Context | ADAM Context |
|---|---|---|
| **Term** | Policy Engine | CORE Engine |
| **What it is** | AGT Agent OS: a stateless policy enforcement sidecar that intercepts agent invocations and evaluates them against loaded policies in <0.1ms p99. It enforces rules. | The Culture / Objectives / Rules / Expectations graph — a queryable knowledge graph (Azure Cosmos DB Gremlin) encoding organizational values, doctrine, authority scope, and hard rules. It defines the meaning of governance. |
| **Technology** | OPA/Rego (or YAML/Cedar) evaluation engine | Cosmos DB Gremlin graph, queryable by all governance agents |
| **Direction of authority** | Agent OS reads from the CORE Engine policy export. It cannot write to it. | CORE Engine is the source of all governance truth. It cannot be modified by AGT. |

**Rule**: CORE Engine is ADAM's policy engine. Agent OS is AGT's enforcement tool. These are different things at different layers. "Policy Engine" without qualification is ambiguous and should not appear in ADAM documentation.

**Correct usage examples**:
- "The CORE Engine exports Rego policies; Agent OS loads and enforces them at the invocation boundary."
- "Agent OS evaluates actions against CORE Engine policy exports in under 0.1 milliseconds."

**Incorrect usage examples**:
- ❌ "The policy engine governs all agent actions." *(Does this mean CORE Engine or Agent OS?)*
- ❌ "Configure the policy engine to allow financial actions." *(Agent OS enforces; CORE Engine defines.)*

---

### 3. Trust Score / BOSS Score

| Attribute | AGT Context | ADAM Context |
|---|---|---|
| **Term** | Trust Score | BOSS Score |
| **What it measures** | Whether an **agent** is trustworthy, based on its behavioral history across interactions. | Whether an **action** is safe to execute, based on 7 weighted dimensions of consequence. |
| **Scale** | 0 to 1000 (higher = more trusted) | 0 to 100 (higher = more risky) |
| **Unit of measurement** | Per agent | Per action |
| **Who computes it** | AGT Agent Mesh (IATP protocol) | ADAM BOSS Engine (ADAM-sovereign formula) |
| **Dimensions** | Single behavioral rating | 7 canonical dimensions (BOSS v3.2; Priority Tier weights sum to 24.0): Security Impact (5.0 — Top), Sovereignty Action (4.0 — Very High), Financial Exposure (4.0 — Very High), Regulatory Impact (3.0 — High), Reputational Risk (3.0 — High), Rights Certainty (3.0 — High), Doctrinal Alignment (2.0 — Medium) |
| **Escalation model** | Tier thresholds (700 for autonomous, 500 for constrained, 300 for review, 100 for suspension) | SOAP (0-10) → MODERATE (11-30) → ELEVATED (31-50) → HIGH (51-75) → OHSHAT (76-100) |

**Rule**: Always qualify which score is being referenced. "Trust score" = agent-level behavioral rating (AGT). "BOSS Score" = action-level consequence rating (ADAM). Never use "trust score" to mean BOSS Score or vice versa.

**Rule**: When documenting the Two-Dimensional Trust Model, always state both: "BOSS Score (action risk) AND AGT trust score (agent trustworthiness)."

**Correct usage examples**:
- "An agent with a trust score of 750 (Trusted tier) executing an action with a BOSS Score of 8 (SOAP tier) is authorized for autonomous execution."
- "The AGT trust score dropped to 280, triggering a +15 adjustment to the BOSS Security Impact dimension."

**Incorrect usage examples**:
- ❌ "The trust score of 72 requires Director approval." *(A score of 72 on the 0-100 BOSS scale = HIGH tier. The AGT trust score is 0-1000.)*
- ❌ "Use the BOSS Score to evaluate agent behavior." *(BOSS scores actions, not agents.)*

---

### 4. Kill Switch / OHSHAT Protocol

| Attribute | AGT Context | ADAM Context |
|---|---|---|
| **Term** | Kill Switch | OHSHAT Protocol |
| **What it does** | AGT Agent Runtime provides an emergency termination capability for individual agents or agent groups. It is a technical mechanism. | OHSHAT (Operational Hell, Send Humans Act Today) is a constitutional governance event. It is not merely technical stoppage — it triggers Director notification, safe mode, Flight Recorder emergency retention, and mandatory CEO + CISO co-authority for resolution. |
| **Who triggers it** | Any authorized operator; automated on BOSS threshold crossing | All 5 Directors notified; CEO has co-authority; CISO leads resolution |
| **Scope** | Agent runtime termination | Full operational governance event with evidence, human escalation, and safe mode |

**Rule**: Use "OHSHAT protocol" for ADAM governance escalation events. "Kill switch" may be used when specifically discussing AGT's emergency termination mechanism. Never use "kill switch" to describe ADAM's OHSHAT tier.

**Correct usage examples**:
- "AGT Agent Runtime provides a kill switch that OHSHAT protocol activation invokes as one component of the full-stop response."
- "An OHSHAT-tier BOSS Score triggers the OHSHAT protocol, which includes activating the AGT kill switch and notifying all Directors."

**Incorrect usage examples**:
- ❌ "The kill switch handles all governance emergencies." *(OHSHAT is a governance event, not a kill switch.)*
- ❌ "Configure the kill switch for Director approval." *(The OHSHAT protocol requires Director involvement — kill switch is just the technical mechanism.)*

---

### 5. Governor / Governor Agent

| Attribute | AGT Context | ADAM Context |
|---|---|---|
| **Term** | (No AGT equivalent) | Governor Agent |
| **What it is** | AGT has no concept of a governance authority within the agent hierarchy. | 5 named Domain Governor Agents, each with domain enforcement authority over a specific governance domain: Financial, Legal & Compliance, Security & Trust, Market & Ecosystem, Operations & Delivery. |
| **Authority level** | Not applicable | Ring 1 (second-highest privilege). Cross-domain delegation requires both Governors' approval. |
| **Election / appointment** | Not applicable | Defined in ADAM DNA Questionnaire; encoded as Ring 1 vertices in CORE Graph |

**Rule**: Never describe any AGT component as a "governor." AGT has no governors. "Governor" in ADAM always means a named Domain Governor Agent with Ring 1 authority. When discussing AGT Agent OS or Agent Mesh in a governance context, always clarify that they enforce governance rules but do not make governance decisions.

**Correct usage examples**:
- "The Financial Governor Agent adjudicates exceptions at the ELEVATED BOSS tier. Agent OS enforces the resulting policy decision."
- "Governor Agent approval is required for cross-domain delegation; AGT Agent Mesh validates the approval token cryptographically."

**Incorrect usage examples**:
- ❌ "Agent OS governs policy decisions." *(Agent OS enforces; Governor Agents decide.)*
- ❌ "Configure the AGT governor for financial exceptions." *(AGT has no governors.)*

---

### 6. Execution Rings / ADAM Authority Levels

| Attribute | AGT Context | ADAM Context |
|---|---|---|
| **Term** | Execution Rings (Ring 0-3) | Authority Levels (Constitutional, Domain Governance, Orchestration Authority, Task Execution) |
| **What they are** | A CPU-privilege-inspired containment model enforced by AGT Agent Runtime. Ring 0 = highest privilege (doctrine write), Ring 3 = lowest (task execution). | ADAM's conceptual authority model based on an agent's role and accountability within the governance hierarchy. |
| **Relationship** | AGT execution rings map to ADAM authority levels. Rings are the technical implementation; authority levels are the governance design. | ADAM authority levels define the governance intent; rings enforce it technically. |

**Rule**: Use "Ring [0-3]" when discussing AGT Agent Runtime enforcement specifics. Use "authority level" or "ADAM agent class" when discussing the governance design. The mapping is defined in `deployment/agent-ring-assignments.yaml`.

**Correct usage examples**:
- "Governor Agents operate at Ring 1 (Domain Governance authority level)."
- "Cross-ring invocation without authorization is blocked by AGT Agent Runtime's admission controller, regardless of the agent's ADAM authority level claim."

**Incorrect usage examples**:
- ❌ "Ring 0 agents are the most important." *(Meta-Governance agents have highest privilege, but importance is a governance concept, not a ring concept.)*

---

### 7. Agent Compliance / ADAM Regulatory Governance

| Attribute | AGT Context | ADAM Context |
|---|---|---|
| **Term** | Agent Compliance | Regulatory Governance / BOSS Regulatory Impact |
| **What it does** | AGT Agent Compliance is a classification service that automatically classifies agent actions against EU AI Act, HIPAA, and SOC2 frameworks. It produces classification signals. | ADAM's Regulatory Governance is the full set of controls ensuring regulatory conformance: Legal & Compliance Governor Agent, BOSS Regulatory Impact dimension (weight 3.0, Priority Tier: High), Legal Director escalation, and DORA/NIS2/Singapore IMDA/ISO 42001 alignment. |
| **Scope** | EU AI Act, HIPAA, SOC2 classification only | Full regulatory framework including DORA, NIS2, Singapore IMDA, ISO 42001, NIST, TOGAF |
| **Who consumes it** | AGT feeds Regulatory Impact dimension inputs to ADAM's BOSS Engine | BOSS Engine computes Regulatory Impact dimension (weight 3.0, Priority Tier: High); Legal Director governs compliance decisions |

**Rule**: "Agent Compliance" (with capital A and C) refers specifically to the AGT package. "Regulatory governance" or "regulatory compliance" refers to the ADAM governance model. AGT Agent Compliance feeds BOSS Regulatory Impact inputs — it does not replace ADAM's regulatory governance model.

**Correct usage examples**:
- "AGT Agent Compliance classifies the action as EU AI Act limited risk; this signal feeds the BOSS Regulatory Impact dimension."
- "ADAM's regulatory governance covers DORA and NIS2; AGT Agent Compliance covers EU AI Act, HIPAA, and SOC2."

**Incorrect usage examples**:
- ❌ "Agent Compliance ensures DORA conformance." *(DORA is covered by ADAM's architecture, not AGT Agent Compliance.)*
- ❌ "Configure Agent Compliance for all regulatory requirements." *(AGT Agent Compliance covers a subset only.)*

---

## Quick Reference Card

| If you mean... | Say... | Not... |
|---|---|---|
| AGT communication and identity layer | "AGT Agent Mesh" | "agent mesh" |
| ADAM's 81+ agent governance structure | "ADAM's 81+ Agent Mesh" or "ADAM's agent topology" | "agent mesh" |
| The AGT enforcement sidecar | "Agent OS" or "AGT Agent OS" | "policy engine" |
| ADAM's governance knowledge graph | "CORE Engine" | "policy engine" |
| Per-action risk score (0-100) | "BOSS Score" | "trust score" |
| Per-agent behavioral rating (0-1000) | "AGT trust score" or "IATP trust score" | "BOSS Score" |
| Full governance emergency event | "OHSHAT protocol" | "kill switch" |
| AGT's technical agent termination | "AGT kill switch" | "OHSHAT" |
| Domain governance authority (ADAM) | "Governor Agent" | "governor", "super agent" |
| Privilege containment layer (AGT) | "execution ring [0-3]" | "authority level" |
| ADAM governance authority concept | "authority level" or "agent class" | "execution ring" |
| AGT regulatory classification package | "AGT Agent Compliance" | "regulatory compliance" |
| ADAM's regulatory governance | "regulatory governance", "BOSS Regulatory Impact" | "Agent Compliance" |

---

## Enforcement

These naming conventions are enforced in all ADAM AGT Light plugin content:

- **YAML/JSON**: The `config/agt-integration-config.yaml` terminology_rules section encodes these rules as machine-readable constraints for AI build agents
- **Word documents**: The integration plugin document (Part 6) and deployment specification include disambiguation tables
- **Code**: The Agent OS Rego policy template uses ADAM-canonical names; comments explicitly flag where AGT terms appear

Any documentation, pull request, or communication that violates these conventions should be flagged as a terminology defect before review approval.

---

*ADAM — Autonomy Doctrine & Architecture Model*  
*AGT Light Plugin — Terminology Disambiguation Reference*
