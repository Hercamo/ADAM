# ADAM Protocols — Inter-Agent Communication & Dynamic Action Cards (v0.3, Day-1 PQC)

Add-on Build Card category. Where the per-agent cards under
`ADAM Agent Definitions/` describe **what** an agent does, and the per-system
cards under `ADAM Integration Adapters/` describe **what an adapter speaks**,
the cards in this directory describe **how agents talk to each other and to
ADAM-controlled tools** — the wire-protocols, identity primitives, and
governance-bound action primitives that bind every agent invocation in the
ADAM mesh.

These cards are doctrine-binding. Every Agent Definition Card and every
Adapter Card references this category for its protocol surface. New
protocols may not be introduced into ADAM without a card here.

## Cards in this category

* `baseline-mcp-a2a__Baseline_MCP_A2A_and_Dynamic_Agent_Actions.md`
  (`proto-mcp-a2a`) — MCP as the primary hub-spoke orchestration / tool-call
  control plane; A2A as the workgroup-level peer-to-peer coordination
  plane; the dual-signed Day-1 PQC agent identity that secures both;
  collaborative-flow vs. strict-agentic-flow classification per agent;
  governance gating (BOSS, Exception Economy, CORE, AGT, Vault) on every
  inbound and outbound call; integration matrix for open-source and
  product-specific implementations (incl. Microsoft Azure AI Foundry).

## Doctrinal anchors common to every card in this directory

* ADAM Book New v0.3 (authoritative SpecPack — wins on contention with
  legacy `ADAM Book/`).
* RGI v1.1 — five contracts (Policy Enforcement, Agent Identity, Execution
  Containment, Telemetry Emission, Tool/Plugin Governance).
* BOSS Score v3.2 — 7 dimensions, weight-sum 24.0, five tiers
  (`SOAP | MODERATE | ELEVATED | HIGH | OHSHAT`), critical-dimension
  override at raw > 75, +15 additive non-idempotent penalty.
* Flight Recorder schema v2.1 — append-only, WORM-enforced, hash-chained,
  dual-signed Ed25519 + ML-DSA-65, SLH-DSA long-term anchored.
* Intent Object v1.1 — every governed action originates from or anchors
  to a versioned, schema-validated Intent Object with `is_non_idempotent`
  and `replay_marker`.
* 5+2 Director Constitution (CEO, CFO, Legal, Market, CISO + optional
  CPO/CTO).
* Day-1 PQC: `Ed25519 + ML-DSA-65 + ML-KEM-768`; `SLH-DSA` long-term
  anchor (NIST FIPS 203/204/205). CMSA 2.0 conformant from Day-1.
* Software-HSM only. NO blockchain. NO smart contracts. NO DAO.
* Doctrine never self-amends.

## Status

Build-ready, advanced-AI-feed. QA: structural (`qa_all`), cross-mesh
(`qa_360`), and three-pass deep (`qa_pass3`/`qa_pass4`/`qa_pass5`)
exercise every card in this directory. Definition of Done in every card
requires 100/100 on each harness plus a clean `views_smoke` pass.
