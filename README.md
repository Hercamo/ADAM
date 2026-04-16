# ADAM — Autonomy Doctrine & Architecture Model

### The ADAM Doctrine & Specification Package (ADAM SpecPack)

> **Humans Define Intent. Machines Execute. Evidence Proves Everything.**

A constitutional operating model for autonomous enterprises — industry-agnostic, sovereign by design, and machine-deployable. This repository is the companion specification package to the book *ADAM — Autonomy Doctrine & Architecture Model v1.0*.

---

## What This Repository Is

This repository contains the **ADAM Doctrine & Specification Package** — referred to throughout as the **ADAM SpecPack**. It is the complete, AI-ready set of documents, schemas, configurations, and tools that an organization (or an AI build agent) needs to design, configure, and deploy a working ADAM instance.

The ADAM SpecPack is intentionally structured so that every file in this repository — Word documents, JSON schemas, Rego policies, YAML configuration, Terraform modules, Helm charts, draw.io diagrams, and Python source — can be fed directly into modern AI systems to generate a customized, defensible, and production-ready autonomous enterprise blueprint for any industry or cloud target.

### What Is Included Here

Everything required to *understand*, *configure*, and *deploy* ADAM:

- Supporting specifications for every major ADAM component (BOSS, CORE, Flight Recorder, Intent Objects, Governance Charter, Legal & Arbitration, Glossary, Industry Services, Agent Org Chart)
- Two runtime plugin packages (AGT Light and Full AGT Integration) for Microsoft's Agent Governance Toolkit
- The **ADAM DNA Deployment Tool** — a working Python CLI that compiles a filled company DNA into Infrastructure-as-Code
- The **ADAM DNA Tool** — a working FastAPI + React conversational web app that replaces the manual questionnaire with an AI-driven setup experience
- 9 draw.io reference architecture diagrams (AWS, Azure, GCP, Kubernetes, Azure Local, On-Prem, and multi-cloud combinations)
- The **Story Deck** presentation
- A complete, worked example (NetStreamX) showing generated artifacts across all 5 deployment targets

### What Is NOT in This Repository

The main book manuscript — **"ADAM — Autonomy Doctrine & Architecture Model v1.0"** — is **not** distributed here. It is the authoritative narrative, rationale, and doctrine document, and is available for purchase on Amazon and other paid book retailers. The SpecPack in this repository is deliberately designed to be inert without the book: the book provides the reasoning, context, and full doctrine text that makes the schemas, configurations, and tools coherent and defensible.

**To fully implement ADAM, you will need the book.** The SpecPack is comprehensive for machine consumption, but the human-facing doctrine, worked-through rationale, chapter-level guidance, and complete explanatory text live in the published manuscript.

---

## Who This Is For

ADAM is written for both audiences that have to coexist inside every modern enterprise:

**For executives, directors, and boards** — ADAM is a governance operating model. It gives you a defensible, evidence-first way to run an AI-heavy business without expanding headcount linearly with complexity, and without signing over liability to software. It is compatible with the EU AI Act, DORA, NIS2, ISO/IEC 42001, the OECD AI Principles, and the Council of Europe AI Framework by design.

**For architects, platform engineers, and security leads** — ADAM is a reference architecture with real schemas, real Rego policy templates, real Terraform modules, and a deterministic runtime governance interface (RGI). Nothing is hand-waved. Every component maps to concrete services (Cosmos DB Gremlin / Neptune, OPA, Azure Confidential Ledger, LangGraph, Service Bus, Azure Key Vault HSM) and every BOSS dimension maps to a published framework every auditor already recognizes.

**For AI build teams** — the SpecPack is a machine feed. It is structured so that an AI implementation assistant can ingest this repository end-to-end and produce a customized ADAM instance for a named company.

---

## The Core Thesis

Modern enterprises have outgrown human coordination capacity. Automation solved repetition. ADAM solves the next layer: **governed autonomy** — the explicit, scoped, revocable, and auditable delegation of decision-making authority from humans to machines.

Autonomy is not abdication. Directors define intent, constraints, and risk tolerance. Machines execute within doctrine. Every decision produces cryptographically anchored evidence by construction. Audit becomes playback, not archaeology.

ADAM is not a chatbot, not a DAO, not a legal person, not a liability shield, and not a bypass of regulation. It is a constitutional operating model that keeps accountability attached to identifiable humans while letting machines do the work machines should do.

---

## Major Features

### 1. The CORE Engine

The machine-readable DNA of a company: **C**ulture, **O**bjectives, **R**ules, **E**xpectations. A versioned, testable, rollbackable semantic graph (Cosmos DB Gremlin as the primary reference implementation) that teaches AI systems what "good" looks like inside *your* company — not in general. The CORE Engine includes five subgraphs: Financials, Rights & Licensing, Customer & Reputation, Regulatory & Jurisdiction, and Strategy Drift.

### 2. The BOSS Score (Business Operations Sovereignty Score)

A seven-dimension, 0–100 composite risk score attached to every autonomous action. Every dimension is anchored to a published, peer-reviewed framework:

| Dimension | Framework Basis |
|---|---|
| Sovereignty Action | EU SEAL, Eurotechguide Index |
| Security Impact | NIST CSF, MITRE ATT&CK |
| Financial Exposure | FAIR, COSO ERM |
| Regulatory Impact | EU AI Act, CMMC 2.0 |
| Reputational Risk | RepTrak, SASB Materiality |
| Rights Certainty | WIPO, Creative Commons |
| Doctrinal Alignment | ADAM CORE Graph Drift Detection |

Scores route actions through five escalation tiers — **SOAP** (safe autonomous), **MODERATE**, **ELEVATED**, **HIGH**, and **OHSHAT** (Operational Hell, Send Humans. Act Today!) — with a critical-dimension override, a non-idempotent action penalty, and per-company dimensional weights configured through the DNA Questionnaire.

### 3. The Exception Economy

Autonomy is the default. Human involvement is earned by consequence, not convention. Every action carries a cost/risk/impact estimate and a cumulative exposure trace. Directors manage exceptions and innovations — not workflows, and not routine approvals.

### 4. The 81-Agent Mesh (Reference Topology)

A five-layer agent architecture that adapts to any company's DNA:

- **Human Interface** (3 agents): Intent Interpretation, Trust Gateway, Explain-Back
- **Domain Governors** (5 agents): Financial, Legal, Risk, Market, Strategy — all must concur before execution
- **Orchestration Plane** (4 agents): Policy, Exception, Evidence, Recovery hooks
- **Agentic Work Groups** (63+ agents): 40 Corporate + 23 AI-Native single-responsibility agents
- **Digital Twins and Meta-Governance** (7 agents): Enterprise, Operational, Economic, Risk twins plus Stability, Integrity, and Self-Audit

81 agents is the reference baseline. A real deployment customizes count, scope, and structure to industry, size, and doctrine.

### 5. The 5-Director Constitution

Governance by a small, named, accountable group: **CEO, CFO, Legal Director, Market Director, CISO** — with **CPO** and/or **CTO** as optional additions when product and technology complexity demand them. No middle management. Directors define intent; they do not approve workflows. Every delegation is explicit, scoped, revocable, and auditable, and the "director of record" concept keeps legal accountability attached to identifiable natural persons.

### 6. Formal Intent Objects

A structured JSON schema for every request into ADAM: desired outcomes, hard and soft constraints, risk tolerances, urgency, approval conditions, and full context. Intent Objects are versioned, immutable, and flow through a six-stage execution pipeline.

### 7. The Flight Recorder

Cryptographically anchored, hash-chained, tamper-evident forensic evidence of every decision, every agent action, every policy evaluation, and every escalation. WORM storage, 7-year retention, hot/cool/archive tiers. Audit becomes playback: every decision is replayable with its original context, its policy evaluations, and its causal chain.

### 8. Doctrine Conflict Arbitration

Objective collisions (growth vs. risk, speed vs. compliance), drift detection (sustained divergence between declared and executed behavior), and innovation constraints (proposals not permissible under current doctrine) are surfaced as governance events, never silently optimized away. Machines surface trade-offs with full impact analysis. Humans author the resolution. Doctrine is authoritative but not self-amending.

### 9. The Four Cross-Cutting Guardrail Planes

Architectural — not procedural — planes that cannot be bypassed by agents, orchestration, or human pressure:

- **Policy & Risk Plane** — runtime constraint enforcement
- **Evidence & Audit Plane** — decision provenance and replay
- **Security & Trust Plane** — identity, trust boundaries, prompt abuse resistance
- **Stability & Drift Plane** — autonomy budgets, drift detection, doctrine alignment

### 10. The Cryptographic Authorization Vault

ADAM's built-in, open-source, hash-chained, tamper-evident authorization ledger. Generic cryptographic ledgering backed by HSM keys — no external blockchain, no smart contracts, no DAO.

### 11. Runtime Governance Interface (RGI)

A five-contract interface (policy enforcement, agent identity, execution containment, telemetry emission, tool/plugin governance) that lets *any* compliant runtime substitute for the reference implementation. AGT Light is the current reference runtime. It can be replaced without changing a line of ADAM doctrine.

---

## Major Approaches

### Doctrine-First, Not Procedure-First

ADAM encodes **why** decisions are made, not just what to do. Doctrine is a living, versioned artifact that evolves with the enterprise and is testable in the same way software is testable.

### Evidence-First Execution

Every decision produces governance-grade evidence by construction. Audit equals replay. Regulators get the same trace an incident responder gets.

### Sovereignty by Design

Vendor-neutral, jurisdiction-aware, data-sovereign. Nine reference architectures span hyperscale cloud to fully sovereign on-premises. Primary and secondary clouds, warm standbys, and on-prem failover are all first-class deployment targets.

### Framework-Grounded Scoring

Every BOSS dimension traces to a published framework that auditors already know and regulators already require. No proprietary black-box algorithms. No opinions. No vibes.

### Deployable Today

The SpecPack + the book = a complete path from narrative to running infrastructure. Fill out the DNA (manually or through the conversational DNA Tool), run the DNA Deployment Tool, and the output is deployable IaC and configuration for Azure, AWS, GCP, Kubernetes, or Azure Local.

---

## Repository Contents (ADAM SpecPack)

Everything in this repository is part of the SpecPack and is intended to be consumed by humans *and* AI systems.

### Supporting Specifications

- **ADAM — Agent Org Chart** — Full 81-agent mesh architecture, layer-by-layer, with agent classes and domains.
- **ADAM — BOSS Score Formulas v3.2** — Seven-dimension scoring methodology, composite formulas, critical-dimension override, non-idempotent penalty, and default per-tier weights.
- **ADAM — Copyright and Use Agreement** — Intellectual property terms and permitted use of the ADAM framework.
- **ADAM — DNA Deployment Specification** — Machine-executable infrastructure spec. Multi-cloud topology, AKS/EKS/GKE, data schemas, bootstrap phases.
- **ADAM — DNA Questionnaire** — The 13-section company DNA questionnaire that encodes doctrine, directors, BOSS weights, agent topology, cloud posture, and resilience posture. NetStreamX example answers included.
- **ADAM — Governance Charter and Human Directorship** — The human oversight model, director roles, and the three director interfaces (Intent Interpretation, Trust Gateway, Explain-Back).
- **ADAM — Industry Specific Services and Architecture v1.0** — Industry adaptations of ADAM's reference architecture.
- **ADAM — Intent Object Definition** — Formal Intent Object JSON schema and six-stage execution pipeline.
- **ADAM — Keyword Glossary and Complex Definitions** — Canonical terminology reference.
- **ADAM — Legal and Arbitration Sections** — Legal personality boundary, doctrine conflict arbitration, alignment to EU AI Act, DORA, NIS2, ISO/IEC 42001, the OECD AI Principles, the Council of Europe AI Framework, and the "What ADAM Is NOT" clarifications.

### Architecture Diagrams (9 draw.io files)

Editable, vendor-neutral reference topologies:

- `ADAM_Architecture_AWS_Primary.drawio`
- `ADAM_Architecture_Azure_Primary.drawio`
- `ADAM_Architecture_GCP_Primary.drawio`
- `ADAM_Architecture_OnPrem_AWS_Outposts.drawio`
- `ADAM_Architecture_OnPrem_Azure_Stack.drawio`
- `ADAM_Architecture_OpenSource_Kubernetes.drawio`
- `ADAM_Fully_Sovereign_OnPrem.drawio`
- `ADAM_MultiCloud_AWS_Primary_Azure_Standby.drawio`
- `ADAM_MultiCloud_Azure_Primary_AWS_Standby.drawio`

### AGT LIGHT Plugin — Runtime Governance Implementation

Lightweight integration with Microsoft's Agent Governance Toolkit. Includes the integration plugin document, deployment specification, Rego policy templates, Helm values, Terraform module outlines, agent ring assignments, SLO configuration, Exception Economy configuration, OWASP AA01–AA10 posture mapping, the RGI schema, the enriched Flight Recorder event schema, and the AGT agent trust profile schema.

### AGT Full Implementation Plugin

Complete Microsoft AGT integration: policy engine, agent mesh, runtime, SRE, compliance, and marketplace configuration — plus trust-score, policy-contract, and evidence-record JSON schemas that bridge AGT outputs into ADAM's Flight Recorder and BOSS pipeline.

### ADAM DNA Deployment Tool (Python CLI)

A working Python tool that reads a completed DNA Questionnaire and generates, for each selected platform:

1. A professional Word deployment specification
2. Ready-to-deploy Infrastructure-as-Code (Terraform, Bicep, CloudFormation, Helm, Kustomize)
3. A complete configuration bundle (CORE graph seed data, BOSS policies in OPA/Rego, agent registry, Intent Object schema, governance configuration)

Supported platforms: **Azure, AWS, GCP, Kubernetes, Azure Local**. A full worked example for NetStreamX — a fictional global streaming company — is included in `example-output-netstreamx/` and demonstrates the end-to-end pipeline.

### ADAM DNA Tool (Conversational Web App)

A FastAPI + React application that replaces the static questionnaire with an AI-driven conversational setup experience. Upload existing strategy, finance, HR, compliance, and org documents; the tool extracts what it can, asks targeted questions for what it cannot, validates against the ADAM schema in real time, and outputs a deployment-ready DNA JSON that feeds directly into the DNA Deployment Tool.

Stack: FastAPI (Python) + React/Vite + Tailwind + Docker Compose + Kubernetes/Helm. Document ingestion for DOCX, PPTX, PDF, CSV, XLSX, JSON, and URLs. Provider-agnostic AI layer: OpenAI, Anthropic, or Azure OpenAI.

### The Story Deck

`ADAM — The Story Deck v1.0.pptx` — the executive presentation with BOSS framework traceability, 5-Director Constitution visuals, and the end-to-end ADAM narrative.

---

## From Book to Autonomous Company

Two paths, same end state:

1. **Manual path** — read the book, fill out the DNA Questionnaire with your directors and domain experts, run the DNA Deployment Tool against the filled questionnaire, deploy the generated artifacts.

2. **Conversational path** — read the book, upload your strategy and governance documents into the DNA Tool, finish the remaining sections through AI-driven conversation, hand off the resulting DNA JSON to the DNA Deployment Tool, deploy the generated artifacts.

Either way, the output is the same: a customized, defensible, evidence-first autonomous enterprise with every decision backed by a BOSS score, every action recorded in the Flight Recorder, and every delegation attached to an identifiable human director.

---

## Regulatory Alignment

ADAM is designed to be compatible, by construction, with:

- **EU AI Act** — technical and organizational measures, human oversight, monitoring, suspension capability
- **DORA** — documented, reviewable, auditable ICT risk governance
- **NIS2** — cybersecurity as a board-level obligation
- **ISO/IEC 42001** — AI management system
- **OECD AI Principles** — accountability attached to human and organizational actors
- **Council of Europe AI Framework** — human rights, democracy, rule of law
- **Singapore IMDA** — AI governance alignment

BOSS dimensions map directly to frameworks regulators already require:

Sovereignty → EU SEAL | Financial → FAIR + COSO | Regulatory → EU AI Act + CMMC | Security → NIST + MITRE | Rights → WIPO | Reputation → RepTrak + SASB | Doctrinal → ADAM CORE Graph Drift Detection

---

## What ADAM IS and What ADAM IS NOT

**ADAM IS**

- A constitutional operating model for autonomous enterprises
- Delegated authority: explicit, scoped, revocable, and auditable
- EU AI Act, DORA, and NIS2 compatible by design
- Sovereign, vendor-neutral, product-agnostic
- Evidence-first by construction
- Industry-agnostic and adaptive per company DNA

**ADAM IS NOT**

- A legal person or legal entity
- A liability shield or regulatory bypass
- A DAO or blockchain governance scheme
- A chatbot framework or LLM wrapper
- A replacement for human accountability
- Self-amending without human approval
- Immune from the regulatory frameworks that apply to the organization running it

---

## Getting the Full Implementation

The ADAM SpecPack in this repository is comprehensive for machine consumption. Schemas, policies, configurations, diagrams, and working tools are all here. The book, however, is what turns the SpecPack into a coherent, defensible, implementable program.

The full doctrinal narrative, chapter-level rationale, worked-through governance reasoning, and complete explanatory text are available only in the published book:

**ADAM — Autonomy Doctrine & Architecture Model v1.0**
*Available on Amazon and other major book retailers.*

If you intend to actually deploy ADAM — for a real company, a real board, a real regulator — the book is not optional. It is the reasoning behind every schema in this repository, and without it the SpecPack is a set of well-formed but undefended artifacts.

---

## License and Use

Use of the ADAM framework, doctrine, and SpecPack is governed by `ADAM - Support Documents/ADAM - Copyright and Use Agreement v1.0.docx` in this repository. Please read it before incorporating ADAM into a product, service, or commercial offering.

---

**ADAM — Autonomy Doctrine & Architecture Model** | The ADAM SpecPack | 2026

*Humans Define Intent. Machines Execute. Evidence Proves Everything.*
