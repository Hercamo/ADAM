<p align="center">
  <img src="../ADAM%20-%20Graphics/ADAM%20Top%20Graphic.png" alt="ADAM — AGT Full Implementation Plugin" width="100%">
</p>

<h1 align="center">ADAM — AGT Full Implementation Plugin</h1>

<p align="center">
  <em>All seven AGT packages wired into every ADAM blueprint layer.</em>
</p>

<p align="center">
  <strong>ADAM sets doctrine. &nbsp; AGT runs the machinery. &nbsp; The RGI keeps them separable.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/ADAM-v1.6-1E3A8A?style=for-the-badge" alt="ADAM v1.6">
  <img src="https://img.shields.io/badge/Plugin-v1.1-047857?style=for-the-badge" alt="Plugin v1.1">
  <img src="https://img.shields.io/badge/AGT-7_Packages-6B46C1?style=for-the-badge" alt="AGT 7 Packages">
  <img src="https://img.shields.io/badge/BOSS-v3.2_Canonical-B45309?style=for-the-badge" alt="BOSS v3.2">
  <img src="https://img.shields.io/badge/April-2026-0D9488?style=for-the-badge" alt="April 2026">
  <br>
  <img src="https://img.shields.io/badge/RGI_01→05-All_Domains-1E3A8A?style=for-the-badge" alt="RGI 1-5">
  <img src="https://img.shields.io/badge/81-Agent_Mesh-1E3A8A?style=for-the-badge" alt="81 Agents">
  <img src="https://img.shields.io/badge/5-Director_Constitution-B91C1C?style=for-the-badge" alt="5 Directors">
  <img src="https://img.shields.io/badge/Azure_AKS-Ready-0078D4?style=for-the-badge&logo=microsoftazure&logoColor=white" alt="AKS">
  <img src="https://img.shields.io/badge/Azure_Local-Ready-0078D4?style=for-the-badge&logo=microsoftazure&logoColor=white" alt="Azure Local">
</p>

<p align="center">
  Aligned to <strong>ADAM v1.6</strong> — BOSS v3.2 canonical (7 dimensions · weight-sum 24.0), 81+ Agent Mesh (reference count 81 · seven canonical classes), 5-Director Constitution, 5 canonical Governor Agents.
</p>

---

## <img src="https://img.shields.io/badge/01-What_This_Is-B91C1C?style=for-the-badge" alt="01"> The Maximal AGT Integration

> The **AGT Light** plugin gives you the *minimal* RGI surface.
> This **Full** plugin deploys *all seven* AGT packages and wires them into every ADAM blueprint layer.

This directory contains the technical configuration and schema artefacts for the complete **ADAM — AGT Full Implementation Plugin**, which deploys the entire Microsoft Agent Governance Toolkit (AGT; MIT-licensed) as ADAM's Runtime Governance Interface (RGI) substrate across all five RGI domains.

| Choose This Plugin If… | Choose [AGT Light](../ADAM%20-%20AGT%20LIGHT%20Plugin%20v1.1/) Instead If… |
|:---|:---|
| You want the full AGT surface area wired end-to-end | You want a reduced AGT footprint for lower-complexity integrations |
| You need Agent Lightning for RL-training governance | You don't do online learning |
| You want Agent Marketplace signing of all tools | Your tool inventory is small and static |
| You're deploying to Azure AKS / Azure Local at scale | You're validating an integration pattern before committing |

---

## <img src="https://img.shields.io/badge/02-Sovereignty_Boundary-1E3A8A?style=for-the-badge" alt="02"> ADAM Sovereign · AGT Runtime

ADAM's CORE Engine, BOSS Score v3.2, Exception Economy, 5-Director Constitution, and 81+ Agent Mesh topology are **sovereign** — they are never overwritten by AGT. AGT provides the runtime substrate for ADAM's five RGI domains; ADAM provides the doctrine AGT enforces.

| RGI Domain | AGT Component | What It Gives You |
|:---|:---|:---|
| **RGI-01** Policy Enforcement | Agent OS | `<0.1 ms` p99 invocation-boundary evaluation (YAML · Rego · Cedar) |
| **RGI-02** Agent Identity | Agent Mesh | Cryptographic, non-forgeable, revocable (DIDs + Ed25519) |
| **RGI-03** Execution Containment | Agent Runtime | 4-ring model · saga compensation · OHSHAT kill switch |
| **RGI-04** Telemetry Emission | Agent SRE + Agent OS | OpenTelemetry · SLOs · error budgets · circuit breakers · chaos |
| **RGI-05** Tool/Plugin Governance | Agent Marketplace | Signed manifest registry · attestation · revocation |
| *(feeds BOSS Regulatory)* | Agent Compliance | EU AI Act · DORA · NIS2 · CMMC · HIPAA · SOC 2 classification |
| *(bounds RL training)* | Agent Lightning | CORE-Engine-gated online-learning updates |

---

## <img src="https://img.shields.io/badge/03-BOSS_v3.2_Integration-B45309?style=for-the-badge" alt="03"> AGT Inputs per Dimension

The BOSS Score v3.2 is **ADAM-sovereign** and is computed by the CORE Engine. This Full Plugin supplies inputs to each dimension from AGT telemetry.

| # | Dimension | Weight | Tier | AGT Input Source |
|:---:|:---|:---:|:---|:---|
| 1 | **Security** | 5.0 | Top | Agent Mesh trust deltas · Agent OS deny events · Agent SRE circuit-breaker state |
| 2 | **Sovereignty** | 4.0 | Very High | Agent OS policy evaluations against doctrine hard-rules |
| 3 | **Financial** | 4.0 | Very High | Agent OS policy inputs (`financial_amount` vs `max_financial_authority`) |
| 4 | **Regulatory** | 3.0 | High | Agent Compliance framework classifications |
| 5 | **Reputational** | 3.0 | High | Agent SRE user-facing incident metrics |
| 6 | **Rights** | 3.0 | High | Agent Compliance entitlement/rights checks |
| 7 | **Doctrinal** | 2.0 | Medium | CORE Engine doctrine compliance from Agent OS policy runs |

**Weight sum: 24.0.** Composite = `Σ(raw × weight) / 24`.

### Tier Boundaries

| Tier | Range | Routing |
|:---|:---:|:---|
| 🟢 **SOAP** (Safe & Optimum Autonomous Performance) | 0–10 | Autonomous execution · trust_score ≥ 700 required |
| 🟡 **MODERATE** | 11–30 | Constrained execution · enhanced logging |
| 🟠 **ELEVATED** | 31–50 | Governor Agent review |
| 🔴 **HIGH** | 51–75 | Director escalation · 2-person rule |
| ⚫ **OHSHAT** (Operational Hell, Send Humans Act Today!) | 76–100 | Kill switch · 5-Director Constitution |

### Modifiers

| Modifier | Rule |
|:---|:---|
| **Critical Dimension Override** | If any single dimension raw score > 75: `composite = max(composite, raw_max − 10)`. A single catastrophic dimension cannot be averaged away. |
| **Non-Idempotent Penalty** | Non-idempotent actions incur a **+15 flat additive** penalty on the composite (ADAM v1.6 / BOSS v3.2). **Not a multiplier.** |

---

## <img src="https://img.shields.io/badge/04-Agent_Mesh_Topology-0D9488?style=for-the-badge" alt="04"> 81 Agents Across Seven Classes

The reference topology totals **81 agents** across **seven canonical classes**. The mesh is notated "**81+**" because implementing enterprises may add domain-specific agents — the `+` signals extensibility.

| Class | Execution Ring | Count | Role |
|:---|:---:|:---:|:---|
| Meta-Governance | 0 | 5 | Doctrine write · self-audit · schema registry |
| Governor Agents | 1 | 5 | Financial · Legal & Compliance · Security & Trust · Market & Ecosystem · Operations & Delivery |
| Orchestration | 2 | 4 | Enterprise · Resource · Cross-domain · Temporal orchestration |
| Human Interface | 2 | 3 | Intent-to-Action · Director Interface · Stakeholder Reporting |
| Digital Twin | 2 | 4 | Operational · Risk & Compliance · Economic · AI Creativity |
| Corporate Work Group | 3 | 39 | Domain-specific task execution |
| AI-Centric Division | 3 | 23 | AI strategy · AI product · AI research · AI ethics |
| **Total** | — | **81** | |

---

## <img src="https://img.shields.io/badge/05-Governor_to_Director-6B46C1?style=for-the-badge" alt="05"> The 5-Director Constitution

Each canonical Governor Agent is paired with its peer human Director.

| Governor Agent (AI) | Peer Director (Human) |
|:---|:---|
| Financial Governor Agent | **CFO** |
| Legal & Compliance Governor Agent | **Legal Director** |
| Security & Trust Governor Agent | **CISO** |
| Market & Ecosystem Governor Agent | **Market Director** |
| Operations & Delivery Governor Agent | **CEO** |

Optional extensions: CPO (People) · CTO (Technology) — plugged in via `exception-economy-config.yaml` escalation paths.

---

## <img src="https://img.shields.io/badge/06-File_Structure-047857?style=for-the-badge" alt="06"> What's Shipped

### Configuration (`config/`)

| File | Purpose |
|:---|:---|
| `adam-agt-plugin-manifest.json` | Plugin definition · AGT package dependencies · deployment targets · integration points |
| `agt-policy-engine-config.yaml` | Agent OS with ADAM Policy & Risk Plane · BOSS composite thresholds · `<0.1 ms` p99 target |
| `agt-agent-mesh-config.yaml` | Agent Mesh with ADAM 81+ topology · DIDs · Ed25519 · IATP 0–1000 |
| `agt-runtime-config.yaml` | Agent Runtime with ADAM orchestration · 4-ring containment · saga compensation · OHSHAT kill switch |
| `agt-sre-config.yaml` | Agent SRE for 81+ Agent Mesh · SLOs per agent class · error budgets · circuit breakers · chaos |
| `agt-compliance-config.yaml` | Agent Compliance mapping for EU AI Act · DORA · NIS2 · CMMC · HIPAA · SOC 2 → feeds BOSS Regulatory |

### Schemas (`schemas/`)

| File | Purpose |
|:---|:---|
| `adam-agt-trust-score-schema.json` | Two-Dimensional Trust: Agent Trust (0–1000 · AGT IATP) × BOSS Score v3.2 (0–100 · ADAM-sovereign) |
| `adam-agt-policy-contract-schema.json` | Policy contracts bridging AGT Agent OS with ADAM invocation contracts · BOSS thresholds · 4 enforcement hooks |
| `adam-agt-evidence-record-schema.json` | Evidence records from AGT enforcement feeding Flight Recorder · WORM markers · hash-chained |

### Integration (`integration/`)

Python integration modules binding AGT packages to ADAM sovereign components. See `integration/*.py` for module-level docstrings — submodules correspond one-to-one with AGT packages.

### Deployment (`deployment/`)

Helm charts and environment values.

| Target | Directory |
|:---|:---|
| Production Azure | `azure-aks/` |
| On-prem Azure Local | `azure-local/` |
| Vendor-neutral Kubernetes | `k8s-generic/` |

---

## <img src="https://img.shields.io/badge/07-Version_History-B45309?style=for-the-badge" alt="07"> Changelog

| Version | Date | Notes |
|:---:|:---|:---|
| **1.0** | March 2026 | Initial release; aligned with ADAM book v0.9 draft. |
| **1.1** | April 2026 | Aligned with **ADAM v1.6**. BOSS v3.2 canonical (7 dimensions · weight-sum 24.0). 81+ Agent Mesh nomenclature. 5 canonical Governor Agents named. **Non-idempotent penalty changed from 1.5× multiplier to +15 additive.** Removed legacy "Super Agent" aliases, "CRITICAL" tier, and "12 Governor Agent" counts. Tier boundaries corrected to canonical SOAP(0–10) · MODERATE(11–30) · ELEVATED(31–50) · HIGH(51–75) · OHSHAT(76–100). |

---

## <img src="https://img.shields.io/badge/08-Related_Components-1E3A8A?style=for-the-badge" alt="08"> Where This Fits

| Component | Relationship |
|:---|:---|
| [ADAM SpecPack](../README.md) | Authoritative parent — doctrine, architecture, worked examples |
| [BOSS Engine](../ADAM%20-%20BOSS%20Governance%20and%20Scoring%20Engine%20-%20Stand%20Alone/) | The scoring substrate; AGT satisfies its RGI |
| [AGT Light Plugin](../ADAM%20-%20AGT%20LIGHT%20Plugin%20v1.1/) | Companion — reduced-footprint alternative |
| [DNA Deployment Tool](../ADAM%20-%20DNA%20Deployment%20Tool%20v1.1/) | Renders this plugin's Helm values + Rego policies from DNA JSON |
| [Sovereignty Connector](../ADAM%20Sovereignty%20Connector%201.1/) | Single-exe deployer for end-to-end ADAM on Azure Local / k3d |
| *NetStreamX case study* | Worked examples in `ADAM Book/` |

---

## <img src="https://img.shields.io/badge/09-License-B45309?style=for-the-badge" alt="09"> License

ADAM — Autonomy Doctrine & Architecture Model · AGT Full Implementation Plugin. AGT is MIT-licensed (Microsoft). See the [ADAM SpecPack root](../README.md) for ADAM licensing terms.

---

<p align="center">
  <a href="../README.md"><img src="https://img.shields.io/badge/⬅_Back_to_ADAM_SpecPack-047857?style=for-the-badge" alt="Back"></a>
</p>
