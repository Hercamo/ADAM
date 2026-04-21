# ADAM — AGT Full Implementation Plugin

**Version 1.1 | April 2026 | Aligned with ADAM book v1.4 (BOSS v3.2 canonical; 81+ Agent Mesh reference count 81 across seven canonical classes; 5-Director Constitution; 5 canonical Governor Agents)**

This directory contains technical configuration and schema artefacts for the
**ADAM — AGT Full Implementation Plugin**, which deploys the complete
Microsoft Agent Governance Toolkit (AGT; MIT-licensed) as ADAM's Runtime
Governance Interface (RGI) substrate for all five RGI domains.

> **Companion plugin:** The **AGT Light Plugin** (separate folder) deploys a
> reduced AGT footprint for lower-complexity integrations. This Full Plugin
> deploys *all seven* AGT packages and wires them into every ADAM blueprint
> layer.

---

## Overview

The ADAM — AGT Full Implementation Plugin bridges two systems:

- **ADAM** (Autonomy Doctrine & Architecture Model) v1.4: enterprise autonomy
  framework with the CORE Engine, **BOSS Score v3.2** (canonical 7 dimensions,
  weight-sum 24.0), Exception Economy, Flight Recorder, the 5-Director
  Constitution (CEO, CFO, Legal Director, Market Director, CISO), and the
  **81+ Agent Mesh** (reference count 81 across seven canonical classes).
- **AGT** (Agent Governance Toolkit): Microsoft's open-source 7-package agent
  runtime providing policy enforcement, cryptographic identity, execution
  containment, SRE observability, regulatory mapping, marketplace signing, and
  reinforcement-learning governance.

ADAM is the **governance framework** (doctrine, BOSS Score, Exception Economy,
Flight Recorder, Constitution). AGT is the **runtime substrate** satisfying
all five RGI domains (RGI-01…RGI-05). ADAM's sovereign constructs are never
overwritten by AGT.

---

## File Structure

### Configuration (`config/`)

| File | Purpose |
|---|---|
| `adam-agt-plugin-manifest.json` | Plugin definition, AGT package dependencies, deployment targets, integration points |
| `agt-policy-engine-config.yaml` | Agent OS integration with ADAM Policy & Risk Plane; BOSS composite thresholds; <0.1ms p99 target |
| `agt-agent-mesh-config.yaml` | Agent Mesh integration with ADAM 81+ Agent topology; DIDs, Ed25519, IATP 0-1000 trust score |
| `agt-runtime-config.yaml` | Agent Runtime with ADAM orchestration; 4-ring execution containment; saga compensation; OHSHAT kill switch |
| `agt-sre-config.yaml` | Agent SRE for 81+ Agent Mesh: SLOs per agent class, error budgets, circuit breakers, chaos scenarios |
| `agt-compliance-config.yaml` | Agent Compliance mapping for EU AI Act, DORA, NIS2, CMMC, HIPAA, SOC2 — feeds BOSS Regulatory Impact |

### Schemas (`schemas/`)

| File | Purpose |
|---|---|
| `adam-agt-trust-score-schema.json` | Two-Dimensional Trust surface: Agent Trust (0-1000, AGT Agent Mesh IATP) × BOSS Score v3.2 (0-100, ADAM-sovereign) |
| `adam-agt-policy-contract-schema.json` | Policy contracts bridging AGT Agent OS with ADAM invocation contracts; BOSS thresholds; 4 enforcement hooks |
| `adam-agt-evidence-record-schema.json` | Evidence records from AGT enforcement actions feeding Flight Recorder; WORM markers; hash-chained |

### Integration (`integration/`)

Python integration modules binding AGT packages to ADAM sovereign components.
See `integration/*.py` for module-level docstrings. Submodules correspond one
to one with AGT packages.

### Deployment (`deployment/`)

Helm chart and environment values. `azure-aks/` for production Azure; `azure-local/` for on-prem Azure Local; `k8s-generic/` for vendor-neutral Kubernetes.

---

## Canonical BOSS Score Integration (v3.2)

The BOSS Score v3.2 is **ADAM-sovereign** and is computed by the CORE Engine.
The Full Plugin supplies inputs to each dimension from AGT telemetry.

| Dimension | Weight | Priority Tier | AGT Input Source |
|---|---|---|---|
| Security Impact | 5.0 | Top | Agent Mesh trust deltas, Agent OS deny events, Agent SRE circuit-breaker state |
| Sovereignty Action | 4.0 | Very High | Agent OS policy evaluations against doctrine hard-rules |
| Financial Exposure | 4.0 | Very High | Agent OS policy inputs (financial_amount vs. max_financial_authority) |
| Regulatory Impact | 3.0 | High | Agent Compliance framework classifications |
| Reputational Risk | 3.0 | High | Agent SRE user-facing incident metrics |
| Rights Certainty | 3.0 | High | Agent Compliance entitlement/rights checks |
| Doctrinal Alignment | 2.0 | Medium | CORE Engine doctrine compliance from Agent OS policy runs |

**Weight sum: 24.0.** Composite = Σ(raw × weight) / 24.

### BOSS Score v3.2 Tier Boundaries

| Tier | Range | Routing |
|---|---|---|
| SOAP | 0–10 | Autonomous execution (trust_score ≥ 700 required) |
| MODERATE | 11–30 | Constrained execution; enhanced logging |
| ELEVATED | 31–50 | Governor Agent review |
| HIGH | 51–75 | Director escalation; 2-person rule |
| OHSHAT | 76–100 | Kill switch, 5-Director Constitution |

**SOAP** = Safe & Optimum Autonomous Performance.
**OHSHAT** = Operational Hell, Send Humans Act Today!

### Modifiers

- **Critical Dimension Override** — if any single dimension raw score > 75,
  composite = max(composite, raw_max − 10). Ensures a single catastrophic
  dimension cannot be averaged away.
- **Non-Idempotent Penalty** — non-idempotent actions incur a **+15 flat
  additive** penalty on the composite (ADAM v1.4 / BOSS v3.2). **Not a
  multiplier.**

---

## 81+ Agent Mesh Topology (Reference Count 81)

The reference topology totals 81 agents across seven canonical classes. The
mesh is **81+** because implementing enterprises may add domain-specific
agents; the "+" indicates extensibility.

| Class | Ring | Count | Role |
|---|---|---|---|
| Meta-Governance | 0 | 5 | Doctrine write, self-audit, schema registry |
| Governor Agents | 1 | 5 | Financial, Legal & Compliance, Security & Trust, Market & Ecosystem, Operations & Delivery |
| Orchestration | 2 | 4 | Enterprise/Resource/Cross-domain/Temporal orchestration |
| Human Interface | 2 | 3 | Intent-to-Action, Director Interface, Stakeholder Reporting |
| Digital Twin | 2 | 4 | Operational / Risk & Compliance / Economic / AI Creativity twins |
| Corporate Work Group | 3 | 39 | Domain-specific task execution |
| AI-Centric Division | 3 | 23 | AI strategy, AI product, AI research, AI ethics |
| **Total** | | **81** | |

---

## 5-Director Constitution (Human) ↔ 5 Governor Agents (AI)

Each canonical Governor Agent is paired with its human peer Director.

| Governor Agent (AI) | Peer Director (Human) |
|---|---|
| Financial Governor Agent | CFO |
| Legal & Compliance Governor Agent | Legal Director |
| Security & Trust Governor Agent | CISO |
| Market & Ecosystem Governor Agent | Market Director |
| Operations & Delivery Governor Agent | CEO |

Optional extensions: CPO (People), CTO (Technology) — plugged in via
`exception-economy-config.yaml` escalation paths.

---

## ADAM ↔ AGT Sovereignty Boundary

ADAM's CORE Engine, BOSS Score v3.2, Exception Economy, 5-Director
Constitution, and 81+ Agent Mesh topology are **sovereign** — never overwritten
by AGT.

AGT provides the runtime substrate for ADAM's RGI:

| RGI Domain | AGT Component |
|---|---|
| RGI-01 Policy Enforcement | Agent OS |
| RGI-02 Agent Identity | Agent Mesh (DIDs + Ed25519) |
| RGI-03 Execution Containment | Agent Runtime (4-ring model) |
| RGI-04 Telemetry Emission | Agent SRE + Agent OS |
| RGI-05 Tool/Plugin Governance | Agent Marketplace |

Agent Compliance feeds BOSS Regulatory Impact. Agent Lightning bounds RL
training for any ADAM agent that uses online learning; updates are gated by
the CORE Engine hard-rules.

---

## Version History

| Version | Date | Notes |
|---|---|---|
| 1.0 | March 2026 | Initial release; aligned with ADAM book v0.9 draft |
| **1.1** | **April 2026** | **Aligned with ADAM book v1.4. BOSS v3.2 canonical (7 dimensions, weight-sum 24.0). 81+ Agent Mesh nomenclature. 5 canonical Governor Agents named. Non-idempotent penalty changed from 1.5× multiplier to +15 additive. Removed legacy "Super Agent" aliases, "CRITICAL" tier, and "12 Governor Agent" counts. Tier boundaries corrected to canonical SOAP(0-10) / MODERATE(11-30) / ELEVATED(31-50) / HIGH(51-75) / OHSHAT(76-100).** |

---

## Related Documentation

- ADAM book v1.4 (source of truth for sovereign constructs)
- AGT Package Documentation (7 packages, MIT-licensed)
- `ADAM - AGT LIGHT Plugin v1.1/` (companion reduced-footprint plugin)
- NetStreamX case study examples in `ADAM Book/`
