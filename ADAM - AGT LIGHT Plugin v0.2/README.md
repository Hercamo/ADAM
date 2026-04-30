# ADAM — AGT Light Plugin

**Autonomy Doctrine & Architecture Model**  
**Runtime Governance Implementation Plugin — Microsoft Agent Governance Toolkit (AGT Light)**

Version 1.1 | April 2026 — aligned with ADAM book v1.4 (BOSS v3.2 canonical 7 dimensions, weight-sum 24.0; 5-Director Constitution — CEO, CFO, Legal Director, Market Director, CISO; 81+ Agent Mesh reference count 81 across seven canonical classes)

---

## What This Is

This directory contains the complete AGT Light plugin for ADAM — the Autonomy Doctrine & Architecture Model. It positions Microsoft's Agent Governance Toolkit (AGT) as ADAM's **recommended runtime enforcement layer** using a strategic integration approach (Option B from the ADAM × AGT Integration Analysis, April 2026).

AGT is **not** ADAM's architecture. ADAM's doctrine layer — the CORE Engine, BOSS Score v3.2, Exception Economy, 5-Director Constitution, and 81+ Agent Mesh — is sovereign intellectual property that does not depend on any single toolkit. AGT is the current reference runtime implementation. It can be replaced by any implementation that satisfies ADAM's Runtime Governance Interface (RGI) without changing a line of ADAM doctrine.

---

## Directory Structure

```
ADAM - AGT LIGHT Plugin/
├── README.md                                     ← This file (AI feed entry point)
├── ADAM - AGT Light Integration Plugin.docx      ← Main Word document (ADAM book section)
├── ADAM - AGT Light Deployment Specification.docx ← Complete deployment spec v2.0
│
├── schemas/
│   ├── agt-light-rgi.json                        ← Runtime Governance Interface schema
│   ├── flight-recorder-event-v2.json             ← Flight Recorder event schema (AGT-enriched)
│   ├── agt-agent-trust-profile.json              ← AGT agent trust score schema
│   └── owasp-adam-agt-mapping.json               ← OWASP AA01-AA10 coverage mapping
│
├── deployment/
│   ├── agt-light-helm-values.yaml                ← Helm values (all 7 AGT packages)
│   ├── agent-ring-assignments.yaml               ← Execution ring → ADAM agent class mapping
│   ├── agent-slo-config.yaml                     ← Agent SRE SLO definitions
│   ├── exception-economy-config.yaml             ← Exception Economy + AGT trust thresholds
│   └── terraform-agt-module-spec.tf              ← Terraform module outline for AGT infra
│
├── config/
│   ├── agent-os-policy-template.rego             ← Agent OS Rego policy template
│   ├── agt-integration-config.yaml               ← Master AGT integration configuration
│   └── owasp-posture-config.yaml                 ← OWASP AA01-AA10 enforcement configuration
│
└── docs/
    ├── rgi-compliance-checklist.md               ← RGI compliance checklist for alternatives
    └── agt-adam-disambiguation.md                ← Terminology disambiguation reference
```

---

## AI Feed Instructions

This directory is structured as an AI-readable feed. An AI build agent, implementation assistant, or ADAM DNA Deployment Tool can consume this directory to:

1. **Understand the AGT integration posture** — Read `ADAM - AGT Light Integration Plugin.docx` or the JSON schemas in `schemas/` for machine-readable coverage
2. **Deploy AGT Light infrastructure** — Use `deployment/agt-light-helm-values.yaml` as the Helm values source; refer to the Deployment Specification for context
3. **Configure policy enforcement** — Use `config/agent-os-policy-template.rego` as the Agent OS policy template; policy rules are exported from the CORE Engine Rego export
4. **Validate OWASP posture** — Consult `schemas/owasp-adam-agt-mapping.json` for machine-readable OWASP AA01-AA10 coverage claims
5. **Configure Exception Economy with trust thresholds** — Use `deployment/exception-economy-config.yaml`

### Key Architectural Boundaries (for AI consumption)

```json
{
  "adam_sovereign_components": [
    "CORE Engine (doctrine graph)",
    "BOSS Score v3.2 (canonical 7 dimensions, 0-100, weight-sum 24.0, SOAP → MODERATE → ELEVATED → HIGH → OHSHAT, Critical Dimension Override, non-idempotent penalty = +15 additive)",
    "Exception Economy (autonomy budgets, non-idempotent penalties = +15 additive)",
    "5-Director Constitution (CEO, CFO, Legal Director, Market Director, CISO; optional CPO/CTO add-ons)",
    "81+ Agent Mesh topology (reference count 81 across seven canonical classes — 5 Domain Governors, 4 Orchestration, 3 Human Interface, 39 Corporate Work Groups, 23 AI-Centric Division, 4 Digital Twin, 3 Meta-Governance)",
    "Flight Recorder (hash-chained, WORM, 7-year, cryptographically signed)",
    "Cryptographic Authorization Vault",
    "Sovereignty Architecture"
  ],
  "agt_provides": [
    "Agent OS: policy enforcement sidecar (<0.1ms p99, YAML/Rego/Cedar)",
    "Agent Mesh: cryptographic identity (DIDs + Ed25519) + inter-agent trust (0-1000)",
    "Agent Runtime: execution rings (0-3) + kill switch + saga orchestration",
    "Agent SRE: SLOs, error budgets, circuit breakers, chaos engineering",
    "Agent Compliance: automated EU AI Act / HIPAA / SOC2 classification",
    "Agent Marketplace: plugin Ed25519 signing + attestation + revocation",
    "Agent Lightning: RL training governance (optional)"
  ],
  "runtime_governance_interface": {
    "RGI-01": "Policy Enforcement — <0.1ms p99 invocation boundary evaluation",
    "RGI-02": "Agent Identity — cryptographic, non-forgeable, revocable",
    "RGI-03": "Execution Containment — privilege boundaries, emergency shutdown",
    "RGI-04": "Telemetry Emission — OpenTelemetry-compatible, Flight Recorder adapter required",
    "RGI-05": "Tool/Plugin Governance — signed manifest registry, revocation"
  },
  "modularity_principle": "AGT satisfies the RGI. Any compliant runtime may substitute AGT without changing ADAM doctrine, BOSS Score, or governance model."
}
```

---

## BOSS Score v3.2 Integration Points

Canonical BOSS v3.2 weights (Priority Tiers): Top 5.0 · Very High 4.0 · High 3.0 · Medium 2.0. Denominator = 24.0.

| BOSS Dimension | Weight | Priority Tier | AGT Input | AGT Package |
|---|---|---|---|---|
| Security Impact | 5.0 | Top | OWASP AA01-AA10 coverage signals | Agent OS + Agent Mesh |
| Sovereignty Action | 4.0 | Very High | Execution ring enforcement, cross-ring violation detection | Agent Runtime |
| Financial Exposure | 4.0 | Very High | No direct input (ADAM Financial Governor Agent primary) | — |
| Regulatory Impact | 3.0 | High | Automated EU AI Act / HIPAA / SOC2 classification | Agent Compliance |
| Reputational Risk | 3.0 | High | No direct input (ADAM Market & Ecosystem Governor Agent primary) | — |
| Rights Certainty | 3.0 | High | Plugin manifest verification, signed tool invocations | Agent Marketplace |
| Doctrinal Alignment | 2.0 | Medium | Intent semantic classification, goal hijacking detection | Agent OS |

---

## Two-Dimensional Trust Model

ADAM + AGT Light creates a two-dimensional trust model for autonomous execution:

```
                    AGT Agent Trust Score (0-1000)
                    ↑
         Verified   │ ██████████████████████ AUTONOMOUS ZONE
         (900+)     │ BOSS SOAP (0-10) + Trust Score > 700
                    │
         Trusted    │ ██████████████  CONSTRAINED ZONE
         (700-899)  │ BOSS MODERATE + Trust Score > 500
                    │
         Standard   │ ████████  GOVERNOR REVIEW ZONE
         (500-699)  │
                    │
         Probationary│ ████ DIRECTOR APPROVAL ZONE
         (300-499)  │
                    │
         Untrusted  │ ██ SUSPENDED ZONE
         (<300)     └────────────────────────────────────────→
                                        BOSS Score (0-100) →
                                   SOAP   MOD  ELEV  HIGH  OHSHAT
```

**Rule**: Both dimensions must satisfy their threshold for the lower-restriction execution path. A perfectly trusted agent (score 950) executing a HIGH-BOSS-score action still requires Director approval.

---

## Naming Disambiguation Quick Reference

| Term | In AGT | In ADAM |
|---|---|---|
| Agent Mesh | Communication protocol with crypto identity | 81+ Agent Mesh: reference count 81 across seven canonical classes |
| Policy Engine | Agent OS: <0.1ms stateless interceptor | CORE Engine: executable doctrine graph |
| Trust Score | 0-1000 per-agent behavioral rating | BOSS Score v3.2: 0-100 per-action consequence rating |
| Kill Switch | Emergency runtime agent termination | OHSHAT tier: constitutional full-stop event |
| Governor | (no equivalent) | Domain Governor Agent: 5 canonical Governor Agents (Financial, Legal & Compliance, Security & Trust, Market & Ecosystem, Operations & Delivery) |

---

## Regulatory Frameworks Covered

**ADAM Architecture** (BOSS Regulatory Impact dimension):
EU AI Act, DORA, NIS2, Singapore IMDA, ISO 42001, TOGAF, NIST

**AGT Agent Compliance** (automated classification inputs):
EU AI Act, HIPAA, SOC2

**Combined posture**: ADAM architecture covers the full regulatory governance framework; AGT automates classification for the highest-priority frameworks.

---

## Version History

| Version | Date | Changes |
|---|---|---|
| 1.0 | April 2026 | Initial release. Strategic Integration (Option B) approach. Externalised from main ADAM book as modular plugin. |
| 1.1 | April 2026 | Aligned with ADAM book v1.4: BOSS v3.2 canonical 7 dimensions with Priority Tier weights (Top 5.0, Very High 4.0, High 3.0, Medium 2.0; weight-sum 24.0); Critical Dimension Override; non-idempotent penalty = +15 additive (not a 1.5× multiplier); 81+ Agent Mesh with reference count 81 across seven canonical classes; 5 canonical Governor Agents (Financial, Legal & Compliance, Security & Trust, Market & Ecosystem, Operations & Delivery); Flight Recorder event schema v2.1. |

---

*ADAM — Autonomy Doctrine & Architecture Model*  
*AGT Light Plugin — Runtime Governance Implementation*
