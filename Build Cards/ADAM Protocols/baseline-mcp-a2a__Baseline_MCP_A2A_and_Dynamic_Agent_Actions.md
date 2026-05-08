# Baseline MCP / A2A & Dynamic Agent Actions (v0.3, Doctrine-Bound, Day-1 PQC)

**Card ID:** `proto-mcp-a2a`
**Version:** v0.3 (initial issuance — add-on chapter to ADAM Book New v0.3)
**Status:** build-ready, advanced-AI-feed, production-grade (no stubs, no mocks)
**Supersedes:** none. The Day-1 baseline for the dynamic-agent-action surface.
**Card class:** Protocol Card (under `Build Cards/ADAM Protocols/`)
**Doctrine binding:** ADAM Book New v0.3 — RGI v1.1 (5 contracts), BOSS v3.2
(7 dimensions, weight-sum 24.0), Flight Recorder schema v2.1, Intent Object
v1.1, 5+2 Director Constitution, Software-HSM Authorization Vault,
Day-1 PQC (`Ed25519 + ML-DSA-65 + ML-KEM-768`; `SLH-DSA` long-term anchor).
**Cross-references (other cards):**
`_CONTRACT_SPEC` (`Build Cards/ADAM Integration Adapters/_CONTRACT_SPEC.md`),
`wg-sec-vault` (Cryptographic Authorization Vault Agent),
`orch-policy` (Policy Enforcement Orchestrator),
`orch-exception` (Exception & Escalation Orchestrator),
`orch-evidence` (Evidence-First Execution Orchestrator),
`hi-intent` (Intent Interpretation Agent),
`hi-gateway` (Human Trust Gateway Agent),
`ga-security` (Security & Trust Governor Agent),
`meta-stability` (Autonomy Stability / BOSS Calibration),
`meta-integrity` (CORE Graph Integrity / Doctrinal Drift Sentinel),
`meta-audit` (Self-Audit Readiness / Evidence Integrity Auditor).
**Used by:** every agent in `ADAM Agent Definitions/` (81 base) and
`ADAMPLUS Agent Definitions/` (34 extension), and by every adapter in
`ADAM Integration Adapters/` (20 adapters) when an MCP tool call or A2A
message crosses the ADAM bus.

**Forward-looking SpecPack extensions tracked in §28 Build Plan:**

* extends FR `event_type` enum (schema v2.1) with the dotted `proto.mcp.*`,
  `proto.a2a.*`, `proto.identity.*`, `proto.tool.*`, and `proto.session.*`
  namespaces enumerated in §22 — to be reified into FR schema v2.2 before
  code lands;
* extends Intent Object schema v1.1 with the protocol-class registry in §11
  (`intent.proto.mcp.*`, `intent.proto.a2a.*`, `intent.proto.identity.*`,
  `intent.proto.tool_catalog.*`, `intent.proto.scope_change`);
* extends FR `tamper_evident.attestations[]` to persist the SLH-DSA
  long-term anchor for every protocol-scope-change event — to be normalised
  in FR schema v2.2;
* introduces a new SpecPack schema `external-mcp-server-contract-schema.json`
  whose shape mirrors `external-adapter-contract-schema.json` (per
  `_CONTRACT_SPEC`) so external MCP servers consumed by ADAM agents bind to
  a per-server contract on the same lifecycle as adapters;
* introduces a new SpecPack schema `a2a-conversation-contract-schema.json`
  whose binding cosignatory set is `ga-security + ga-operations + ga-legal`
  for any conversation that crosses a Domain boundary;
* introduces an `agent-collab-profile-schema.json` whose canonical
  enumeration registers every agent as one of `strict-agentic-flow`,
  `collaborative`, or `mixed` (see §13).

These extensions are forward-looking: this card is authored so that as
soon as the SpecPack reifies them, the QA harness validates clean.
Until then, the dual-signature, dotted-event, protocol-class-Intent, and
collaboration-profile behaviours are described as conventions, with their
reified-schema names listed in §28.

---

## 1. Purpose

**This card is a baseline ADAM concept, not an optional add-on.** It is
the foundational protocol layer of the ADAM mesh — every existing and
future Agent Definition Card, ADAMPLUS Extension Card, and Integration
Adapter Card runs on top of it. Where `_CONTRACT_SPEC` defines the
binding pattern between ADAM and an external system, this card defines
the binding pattern between ADAM agents themselves and between ADAM
agents and the ADAM-controlled control plane. The two cards together
form the substrate on which every action in ADAM is taken. Disabling
either disables the mesh.

This card is the canonical specification for **how agents in ADAM talk to
each other and to ADAM-controlled tools**. It defines the two protocol
planes that govern every dynamic action an agent can take:

1. **MCP (Model Context Protocol)** — primary **hub-and-spoke** orchestration
   and tool-call control plane. Every dynamic, externally-callable action an
   agent can take is exposed as an MCP tool with a JSON-Schema argument
   shape, a risk tier, a vault binding, and a Pre-Action Gate. MCP is the
   protocol by which ADAM agents *invoke ADAM-controlled capabilities*.
2. **A2A (Agent-to-Agent Protocol)** — peer-to-peer coordination, collaboration,
   and innovation plane at the **workgroup** level. A2A is the protocol by
   which ADAM agents *talk to other ADAM agents* — to exchange evidence,
   coordinate on multi-agent flows, request peer review, or run innovation
   experiments — within the constraints of the doctrine.

An agent in ADAM is **inert** without a bound, currently-valid
**Agent Identity Certificate (AIC)** AND a bound, currently-valid **Collab
Profile** AND a bound, currently-valid **Tool Catalog**. It MUST refuse to
invoke any MCP tool, accept any A2A message, or emit any bus event without
all three. Refusal is a first-class behavior, recorded under
`proto.identity.*`/`proto.mcp.refused`/`proto.a2a.refused`, and surfaced to
`orch-exception`. There are no exceptions, including for healthchecks,
demos, or break-glass.

Dynamic actions in ADAM exist on a spectrum:

* **Strict-agentic-flow** — financial transactions, payroll runs, regulatory
  filings, treasury moves, takedowns. Deterministic, gated, audit-perfect,
  single-path. A2A peer conversation is **forbidden** during the flow.
  MCP tool calls only — every step is a recorded MCP invocation against a
  named tool.
* **Collaborative** — innovation portfolio, scenario planning, ethical
  alignment, creativity-bound experimentation, strategy alignment, market
  intelligence. A2A peer-to-peer conversation **encouraged** within
  workgroup conversation contracts; the workgroup converges on a proposal
  that is then submitted as an Intent Object through the canonical six-stage
  pipeline.
* **Mixed** — legal contract lifecycle, market customer interaction,
  external stakeholder. Collaborative *inside* the workgroup; strict at
  external boundaries.

**No agent — collaborative, strict, or mixed — can ever bypass governance.**
A2A conversations in ADAM are *inside* the doctrine, never around it.
Every A2A message is BOSS-pre-evaluated, every MCP tool call is
pre-action-gated, every emitted decision is anchored to the Flight
Recorder, and every protocol-scope change requires an Intent Object
co-signed by `ga-security` and the relevant Domain Governor.

This card is **prescriptive** for the production build. Where multiple
implementation choices exist, this card states the open-source reference
choice and the supported product-specific alternatives, the exact
configuration shape, and the non-negotiable constraints. The card is sized
to support a 100/100 NetStreamX test deployment AND a 1M-customer
production deployment without doctrinal change — only resource scaling.

## 2. Definitions

| Term                                | Definition                                                                                                              |
|-------------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| **MCP**                             | Model Context Protocol; JSON-RPC 2.0 over stdio / HTTP+SSE / WebSocket / TCP. Anthropic-published open spec.            |
| **MCP Tool**                        | A named, schema-bound, risk-tiered capability invocable over MCP. Every external action surface is a tool.              |
| **MCP Hub**                         | An MCP server (the *spoke target*) controlled by ADAM that publishes tools the agents (the *spoke clients*) may invoke. |
| **A2A**                             | Agent-to-Agent Protocol; gRPC + Protobuf over mTLS 1.3 with hybrid PQC handshake. Reference: AGT Agent Mesh A2A.        |
| **A2A Conversation**                | A bounded, contracted, time-limited, BOSS-pre-evaluated multi-message exchange between two or more agents.              |
| **AIC (Agent Identity Certificate)**| Per-agent dual-signed Ed25519 + ML-DSA-65 cert with embedded `did:adam:<agent_id>`. Issued by `wg-sec-vault`.            |
| **DID (`did:adam:<agent_id>`)**     | Decentralized Identifier for an agent. Method `did:adam`. Document held in software-HSM-anchored DID registry.          |
| **Tool Catalog**                    | The set of MCP tools an agent may invoke, scoped by Domain and bound to its Collab Profile.                             |
| **Collab Profile**                  | Per-agent declaration of `strict-agentic-flow | collaborative | mixed`, with an A2A peer allowlist and conversation cap. |
| **Pre-Action Gate**                 | Synchronous, in-process check that evaluates every tool call / message against contract, BOSS, and doctrine.            |
| **Conversation Contract**           | Dual-signed contract authorising a specific A2A topology between named agents for a named purpose; expires on schedule. |
| **IATP**                            | Inter-Agent Trust Protocol; AGT-derived 0-1000 trust score continuously refreshed and feeding authority levels.         |
| **Hub-Spoke**                       | Topology in which agents (spokes) talk only through a central MCP hub (Meta-Governance, Human Interface, Twins).        |
| **Mesh**                            | Topology in which agents talk peer-to-peer over A2A under a Conversation Contract (Governors, Orchestration, WGs).      |
| **Strict-Agentic-Flow**             | A flow where agent collaboration is forbidden; every step is a recorded, idempotency-keyed MCP tool call.               |
| **Collaborative Flow**              | A flow where peer-to-peer A2A conversation is permitted under a Conversation Contract, with a single converged Intent.  |
| **Sacred Boundary**                 | A doctrine-level rule that may not be crossed under any BOSS or trust posture (e.g., minor age-gate, takedown).         |

## 3. Doctrinal Anchors

This card is a **baseline** of ADAM — peer to BOSS, the Flight Recorder,
the Vault, and the Director Constitution. It is bound to and inherits
from:

* **RGI v1.1** — five contracts. This card supplies the canonical bindings
  for RGI-01 (Policy Enforcement) at the per-call surface, RGI-02 (Agent
  Identity) end-to-end, RGI-04 (Telemetry Emission) for every protocol
  event, and RGI-05 (Tool/Plugin Governance) for the MCP catalog. RGI-03
  (Execution Containment) is honored via the Pre-Action Gate, the egress
  fence, and the OHSHAT kill switch (§24).
* **BOSS Score v3.2** — every MCP tool call and every A2A message is
  pre-scored. The BOSS floor for protocol surfaces is set per-flow; the
  defaults are in §16. Sacred Boundaries trip OHSHAT regardless of score.
* **Flight Recorder schema v2.1** — every protocol event is dual-signed
  Ed25519 + ML-DSA-65 and chained. SLH-DSA long-term anchor on every
  scope-change event. (See §22.)
* **Intent Object v1.1** — every protocol scope change (new tool, new
  conversation contract, new collab profile, key rotation, agent
  re-binding, server addition) flows through `hi-intent` as a class
  enumerated in §11.
* **5+2 Director Constitution** — material protocol changes (new tool
  category, BOSS-floor reduction, residency change, key suite change)
  require Domain Governor concurrence; OHSHAT-tier changes require the
  full director quorum.
* **Software-HSM only** — NO blockchain, NO smart contracts, NO DAO. All
  credentials live at `wg-sec-vault://...`.
* **Doctrine never self-amends** — agent-authored doctrine changes are
  refused at the Pre-Action Gate, regardless of BOSS posture.

## 4. Topology — MCP Hub & Spoke

ADAM uses MCP as the primary control-plane for tool invocation. Three
canonical hub roles are defined; every other agent class is a spoke
client.

```
                    ┌────────────────────────────────────────────────┐
                    │              ADAM Bus (gRPC + Kafka)           │
                    │ Flight Recorder · BOSS · OPA · Vault · Twins   │
                    └────────────────────────────────────────────────┘
                                       ▲
                              dual-signed events
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
   ┌────┴───────────┐         ┌────────┴─────────┐         ┌─────────┴────────┐
   │ MCP HUB:       │         │ MCP HUB:         │         │ MCP HUB:         │
   │ Meta-Governance│         │ Human Interface  │         │ Digital Twins    │
   │ (3 agents)     │         │ (3 agents)       │         │ (4 agents)       │
   │ self-audit,    │         │ intent-to-action,│         │ Operational/Risk │
   │ schema, doctr. │         │ explain, gateway │         │ /Economic/Ent.   │
   └────────────────┘         └──────────────────┘         └──────────────────┘
        ▲                              ▲                              ▲
        │                              │                              │
        │                  spoke MCP clients (the 67 remaining mesh agents)
        │                              │
   ┌────┴────────────────────────────────────────────────────────────┴────┐
   │ Governor Agents (5) · Orchestration (4) · Corporate WG (39) ·       │
   │ AI-Centric Division (23) · ADAMPLUS (34) · Adapters (20)            │
   └─────────────────────────────────────────────────────────────────────┘
```

**Why hub-spoke for tools.** Three properties are mandatory and only the
hub topology delivers them simultaneously:

1. **Centralised policy enforcement.** The MCP hub holds the OPA Rego
   policy bundle that gates every call. A spoke that bypasses the hub for
   tool invocation cannot be policy-checked; therefore a spoke that
   bypasses the hub is, by definition, refused.
2. **Single tool catalog of record per Domain.** The hub publishes
   `tools/list` and is the only source of truth for tool versions, args
   shape, risk tier, and vault binding for its Domain.
3. **Append-only audit per call.** The hub writes the Pre-Action,
   Action, and Post-Action FR events with the hub's dual signature,
   the spoke's dual signature, and the BOSS score block — all in one
   transaction.

**Three canonical MCP hubs in ADAM:**

| Hub                            | Agents                                                                                    | Tool surface                                                                                                              |
|--------------------------------|-------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| **Meta-Governance Hub**        | `meta-stability`, `meta-integrity`, `meta-audit`                                          | doctrine read, schema registry, BOSS calibration tools, drift detectors, evidence-integrity tools                         |
| **Human Interface Hub**        | `hi-intent`, `hi-gateway`, `hi-explain`                                                   | intent-classification tools, explanation/replay tools, director-presentation tools, the entire **MCP-driven director console** |
| **Digital Twins Hub**          | `twin-enterprise`, `twin-operational`, `twin-economic`, `twin-risk`                       | twin simulation tools, what-if BOSS reruns, scenario-replay tools, divergence-probe tools                                 |

Each hub is a separate MCP server process (or process group) running with
the hub agent's identity. Each hub publishes only the tools its agents own.
A hub that publishes a tool whose underlying capability lives in a different
agent's domain is in violation of `meta-integrity`'s drift check and will be
suspended.

**Hub-spoke routing rule.** Every MCP tool invocation must originate from a
spoke that is allowlisted for the destination hub by the spoke's Tool
Catalog binding. The hub MUST verify the spoke's AIC, MUST verify the
spoke's Tool Catalog includes the tool, MUST verify the BOSS Pre-Action
score is ≤ the tool's tier ceiling, MUST verify the spoke's IATP authority
level meets the tool's `min_authority_level`, AND MUST emit
`proto.mcp.preaction.ok` (or `proto.mcp.preaction.refused`) before the
tool runs.

External MCP servers (e.g., Microsoft Azure AI Foundry, vendor MCP
endpoints, customer MCP endpoints) are bound to ADAM exactly like adapters
under the External-MCP-Server-Contract pattern (§9). They are **never**
hubs in their own right — ADAM's three hubs are the only hubs.

## 5. Topology — A2A Workgroup Mesh

Within a workgroup (Domain) that has been registered as `collaborative` or
`mixed`, peer-to-peer A2A is permitted under a Conversation Contract. This
is the second protocol plane.

```
                ┌─────── ADAM Bus (gRPC + Kafka) ───────┐
                │   Flight Recorder · BOSS · OPA · Vault │
                └────────────────────────────────────────┘
                                   ▲
                          dual-signed events
                                   │
        ┌──────────────────────────┴──────────────────────────┐
        │           A2A workgroup mesh (Domain-scoped)         │
        │                                                      │
        │   ┌────────────┐   ┌────────────┐   ┌────────────┐ │
        │   │ ai-innov-  │←→ │ ai-innov-  │←→ │ ai-innov-  │ │
        │   │ experiment │   │ rollout    │   │ results    │ │
        │   └─────┬──────┘   └─────┬──────┘   └─────┬──────┘ │
        │         │                │                │        │
        │   ┌─────┴────────────────┴────────────────┴──────┐ │
        │   │  Conversation Contract (id, scope, lifetime,  │ │
        │   │  BOSS floor, allowlist, transcript anchor)    │ │
        │   └───────────────────────────────────────────────┘ │
        │                                                      │
        │   ── conversation transcript hash-chained to FR ──   │
        └──────────────────────────────────────────────────────┘
```

**Why mesh inside the workgroup.** Innovation, ethics-alignment, scenario
planning, strategy alignment, and stakeholder coordination are intrinsically
multi-perspective. Forcing a star topology through a single hub for a
free-form ideation session would either over-serialize the conversation or
push the burden of judgment back onto the hub, which is not the hub's job
(the hub is a gate, not a participant). The Conversation Contract scopes
the mesh: the agents may talk freely *inside* the contract; the contract
binds them *outside* the conversation to a single converged proposal,
which is then re-submitted to the canonical six-stage Intent pipeline as a
strict-agentic-flow.

**Where mesh is forbidden.** Strict-agentic-flow agents (financial
transaction, payment run, payroll, regulatory filing, vault key issuance,
takedown) MUST NOT have an A2A mesh among themselves for the duration of
their flow. They communicate ONLY via MCP tool calls onto a canonical
orchestrator (`orch-evidence` / `orch-policy`). Attempting to open an A2A
conversation among strict agents is refused at the Pre-Action Gate with
reason `collab.profile.violation` and surfaced to `orch-exception`.

**Conversation Contract.** Defined in §10. Dual-signed, time-bounded,
allowlist-bounded, transcript-anchored, BOSS-floor-bound.

**A2A bus, not a peer fabric.** Even though the topology is mesh-like, A2A
in ADAM is implemented as gRPC over the ADAM bus — the Flight Recorder
sees and signs every A2A message just as it sees every MCP call. There is
no off-record sidechannel. Implementations that try to do off-record A2A
(e.g., direct sockets between containers) violate RGI-04 and will be
flagged by `meta-audit`.

## 6. Combined Topology (When Both Coexist)

The two planes coexist for `mixed` agents and for any flow that begins
collaboratively and ends transactionally. The canonical pattern:

```
[A2A conversation under Conversation Contract]
   │
   │   (workgroup converges on a proposal)
   │
   ▼
[hi-intent emits Intent Object of class intent.adapter.* / intent.action.*]
   │
   ▼
[BOSS scoring + Domain Governor concurrence]
   │
   ▼
[orch-policy authorizes]
   │
   ▼
[MCP tool invocation through the relevant hub] ───► Adapter / External tool
   │
   ▼
[Flight Recorder dual-signs Pre-Action, Action, Post-Action]
   │
   ▼
[orch-evidence anchors the trail; meta-audit verifies; conversation contract closes]
```

The transition from A2A to MCP is the single point at which collaboration
becomes execution. Before this transition, BOSS records reflect the
deliberation cost only (typically `SOAP`/`MODERATE`). After this
transition, BOSS records the action cost — which may be any tier up to and
including `OHSHAT`. The transition itself is logged as
`proto.session.handoff.collab_to_strict`.

## 7. Agent Identity & Cryptography (the Most Secure Surface in ADAM)

The Agent Identity Certificate (AIC) is the single most security-critical
artifact in this card. It is the credential by which every MCP tool call
and every A2A message is authenticated and authorized. Compromise of an
AIC is treated as an OHSHAT event: full-director quorum, automatic safe
mode for the affected agent, vault-side key revocation, FR-side
quarantine.

### 7.1 AIC structure

```json
{
  "aic_id": "aic-<agent_id>-<epoch>",
  "schema_version": "adam-aic-v1",
  "agent_id": "<canonical agent_id, e.g. wg-fin-txn>",
  "did": "did:adam:<agent_id>",
  "doctrine_version": "adam-book-new@v0.3",
  "issued_at": "<RFC3339>",
  "issued_by": {
    "agent_id": "wg-sec-vault",
    "co_signers": ["ga-security", "meta-integrity"]
  },
  "valid_from": "<RFC3339>",
  "valid_until": "<RFC3339>",
  "rotation_policy": "every 90 days, off-cycle on incident",
  "public_keys": {
    "ed25519": "<base64 raw 32-byte public key>",
    "ml_dsa_65": "<base64 NIST FIPS 204 public key>",
    "x25519": "<base64 raw 32-byte public key>",
    "ml_kem_768": "<base64 NIST FIPS 203 public key>"
  },
  "attestations": {
    "slh_dsa_long_term": "<base64 NIST FIPS 205 signature>",
    "slh_dsa_anchor_at": "<FR head hash>"
  },
  "collab_profile_id": "ccp-<agent_id>-<epoch>",
  "tool_catalog_id": "tcb-<agent_id>-<epoch>",
  "execution_ring": 3,
  "_execution_ring_enum": [0, 1, 2, 3],
  "min_authority_level": "TRUSTED",
  "_min_authority_level_enum": ["STANDARD", "TRUSTED", "VERIFIED"],
  "domain": "work_group",
  "_domain_enum": [
    "human_interface", "domain_governor", "orchestration",
    "work_group", "ai_centric", "digital_twin", "meta_governance"
  ],
  "scope": {
    "allowed_mcp_hubs": ["meta_governance_hub", "human_interface_hub", "digital_twins_hub"],
    "allowed_a2a_peers_did_pattern": ["did:adam:ai-innov-*", "did:adam:wg-ops-innovation"],
    "forbidden_a2a_peers": ["did:adam:wg-fin-*", "did:adam:adamplus-fin-*"],
    "egress_allowlist": ["adam-bus.adam.svc.cluster.local:7443", "fr.adam.svc.cluster.local:9443"],
    "ingress_allowlist": ["10.0.0.0/8"]
  },
  "boss_score_floor": 72,
  "fr_anchor_hash": "<sha3-512 of preceding FR head>",
  "signatures": {
    "ed25519": "<base64>",
    "ml_dsa_65": "<base64>"
  }
}
```

### 7.2 Day-1 PQC posture (per ADAM `_INDEX.md` / Build Cards)

| Surface                                                      | Algorithm                                                 |
|--------------------------------------------------------------|-----------------------------------------------------------|
| Agent → bus (every MCP/A2A event) signature                  | hybrid `Ed25519 + ML-DSA-65` (NIST FIPS 204)              |
| Agent → agent (A2A) handshake key agreement                  | hybrid `X25519 + ML-KEM-768` (NIST FIPS 203)              |
| Agent → external (MCP server) handshake                      | hybrid where the external peer supports it; classical fallback recorded |
| AIC issuance signature                                       | dual `Ed25519 + ML-DSA-65` by `wg-sec-vault`              |
| Vault at-rest key wrap                                       | `ML-KEM-1024` (longer-strength variant)                   |
| Long-term AIC anchor & FR scope-change anchor                | `SLH-DSA` (NIST FIPS 205, hash-based — durable beyond a far-horizon lattice break) |
| AIC content hash                                             | `SHA3-512`                                                |
| Conversation Contract content hash                           | `SHA3-512`                                                |

This posture is **Day-1 baseline**, not a future migration. There is no
classical-only path that ever lands in production. Where an external peer
cannot speak hybrid (e.g., older MCP server), the adapter records
`qsuite=classical-fallback` on every emitted event so audit can compute
exposure.

### 7.3 AIC issuance flow

1. `wg-sec-vault` generates a fresh keypair set (Ed25519, ML-DSA-65,
   X25519, ML-KEM-768) inside the software-HSM. Private keys never
   leave the HSM in the clear; they are wrapped under a vault master key
   that itself is wrapped with `ML-KEM-1024`.
2. `wg-sec-vault` constructs the AIC body, embedding the agent's domain,
   collab profile id, tool catalog id, scope, and BOSS floor.
3. `ga-security` co-signs the AIC after verifying the agent's Build Card
   `acceptance_criteria` against the live registry.
4. `meta-integrity` co-signs after verifying the AIC body does not declare
   a doctrine-amending capability (the agent's tool catalog must not
   include any tool whose effect is doctrine self-amendment).
5. `wg-sec-vault` dual-signs the AIC (Ed25519 + ML-DSA-65) and emits
   `proto.identity.aic.issued`. The AIC is anchored with SLH-DSA on
   issuance.
6. The agent retrieves its AIC at boot via the vault `wg-sec-vault://aic/<agent_id>/current`.
7. The agent emits `proto.identity.aic.bound` with the hub's dual signature
   and goes ACTIVE.

### 7.4 Rotation, revocation, and the OHSHAT incident path

| Trigger                               | Action                                                                                                   |
|---------------------------------------|----------------------------------------------------------------------------------------------------------|
| Scheduled rotation (90 d)             | Vault mints v+1 AIC; agent rebinds atomically on next heartbeat; v emits `aic.superseded`; v archived.   |
| Off-cycle rotation (key compromise)   | Director quorum (CISO + CEO) signs an Intent Object of class `intent.proto.identity.rotate.emergency`.   |
| Suspected key exfiltration            | Vault revokes immediately; agent moves to `SUSPENDED`; OHSHAT tier; full director quorum required.       |
| Multiple verification failures        | IATP score collapses; AIC is `restricted` administratively; investigation launched by `meta-audit`.      |
| Doctrine version bump                 | All AICs invalidated at the `valid_until`; vault re-mints; cluster goes through orderly rebind.          |
| Hub key rotation                      | Hubs rotate; spokes pull updated hub public keys via `proto.mcp.hubkey.refresh`; FR records every step.  |

### 7.5 DID document

```json
{
  "@context": [
    "https://www.w3.org/ns/did/v1",
    "https://adam-governance.io/contexts/adam-v0.3"
  ],
  "id": "did:adam:wg-fin-txn",
  "controller": "did:adam:wg-sec-vault",
  "verificationMethod": [
    { "id": "#ed25519",   "type": "Ed25519VerificationKey2020", "publicKeyMultibase": "<...>" },
    { "id": "#ml-dsa-65", "type": "MlDsa65VerificationKey2025", "publicKeyMultibase": "<...>" },
    { "id": "#x25519",    "type": "X25519KeyAgreementKey2020",  "publicKeyMultibase": "<...>" },
    { "id": "#ml-kem-768","type": "MlKem768KeyAgreementKey2025","publicKeyMultibase": "<...>" }
  ],
  "service": [
    { "id": "#mcp-spoke",  "type": "McpSpokeEndpoint",  "serviceEndpoint": "grpc://wg-fin-txn.adam.svc.cluster.local:7443" },
    { "id": "#a2a-mesh",   "type": "A2aMeshEndpoint",   "serviceEndpoint": "grpc://wg-fin-txn.adam.svc.cluster.local:7444" },
    { "id": "#policy",     "type": "PolicyEnforcement", "serviceEndpoint": "grpc://wg-fin-txn.adam.svc.cluster.local:7445" }
  ],
  "assertionMethod": ["#ed25519", "#ml-dsa-65"],
  "keyAgreement":    ["#x25519",  "#ml-kem-768"]
}
```

### 7.6 Trust scoring (IATP)

Inherited from AGT Agent Mesh; recapitulated here for completeness because
the trust score is the single most common runtime gate.

| Range      | Authority Level | Restrictions                                                               |
|------------|-----------------|----------------------------------------------------------------------------|
| 0–99       | `SUSPENDED`     | no execution; CISO reinstatement required                                  |
| 100–299    | `UNTRUSTED`     | read-only; governor review                                                 |
| 300–499    | `PROBATIONARY`  | limited scope; requires approval; no autonomous                            |
| 500–699    | `STANDARD`      | MODERATE-tier eligible; no SOAP autonomous                                 |
| 700–899    | `TRUSTED`       | SOAP autonomous eligible                                                   |
| 900–1000   | `VERIFIED`      | SOAP autonomous + sovereignty-elevated actions                             |

Continuous decay 1%/day, floor 100. Immediate revocation on
cryptographic-key-compromise, policy-violation-critical,
multi-auth-failures, security-incident-involvement.

### 7.7 Why this is the most secure available identity pattern

1. **Dual-signature defence-in-depth.** Even a far-horizon classical
   compromise of Ed25519 still leaves ML-DSA-65 holding; even a
   far-horizon lattice compromise of ML-DSA-65 leaves the SLH-DSA
   long-term anchor (hash-based) holding the audit story.
2. **Vault-bound private material.** The AIC private keys are never
   present outside the vault HSM in the clear. The only way to use them is
   via vault sign/decrypt RPCs, which are themselves audit-logged and
   rate-limited per agent.
3. **Quad-sig issuance.** Every AIC is co-signed by `wg-sec-vault`
   (issuer) + `ga-security` (governance) + `meta-integrity` (doctrinal
   non-amendment). A single compromised signer cannot mint a usable AIC.
4. **Append-only AIC chain.** Every AIC issuance / rotation / revocation
   is an FR event; full lineage is replayable.
5. **Per-call BOSS gate.** Identity is necessary but not sufficient: every
   call still runs the Pre-Action Gate.
6. **Egress fence at OS level.** AIC scope.egress_allowlist is mirrored as
   seccomp/CNI policy. A compromised agent process cannot reach unlisted
   endpoints even if it forges a signature.
7. **Trust decay.** A silently-compromised agent that does nothing also
   loses 1%/day of trust until governor review notices.

## 8. MCP Protocol Profile (ADAM-MCP)

ADAM uses MCP as the primary tool-call surface. The MCP base spec is
inherited; ADAM adds the constraints below. None of these constraints
break the public MCP spec — ADAM-compliant MCP clients/servers remain
MCP-compliant.

### 8.1 Transport

| Surface                          | Transport                       | Auth                                           |
|----------------------------------|---------------------------------|------------------------------------------------|
| Spoke ↔ ADAM Hub (in-cluster)    | gRPC over mTLS 1.3              | AIC-bound mTLS + AIC dual signature on every JSON-RPC frame |
| Spoke ↔ external MCP server      | HTTP+SSE over mTLS 1.3 or stdio | AIC-bound mTLS where supported; classical fallback recorded |
| Operator ↔ ADAM Hub (loopback)   | stdio or TCP loopback           | OS-level + AIC                                 |
| Browser/Director ↔ ADAM Hub      | HTTP+SSE behind reverse proxy   | director SSO + AIC bridge in `hi-gateway`      |

### 8.2 JSON-RPC 2.0 envelope (ADAM additions in **bold**)

```json
{
  "jsonrpc": "2.0",
  "id": "<request id>",
  "method": "tools/call",
  "params": {
    "name": "<tool name>",
    "arguments": {},
    "_adam": {
      "spoke_did": "did:adam:wg-fin-txn",
      "spoke_aic_hash": "<sha3-512>",
      "intent_id": "<linked Intent Object id>",
      "boss_pre_eval": {
        "composite": 24,
        "tier": "MODERATE",
        "dims": {
          "security": 18,
          "sovereignty": 12,
          "financial": 30,
          "regulatory": 22,
          "reputational": 14,
          "rights": 10,
          "doctrinal": 6
        }
      },
      "is_non_idempotent": false,
      "replay_marker": "<uuid v7>",
      "fr_pre_anchor_hash": "<previous FR head hash>",
      "signatures": {
        "ed25519": "<base64 over canonical params>",
        "ml_dsa_65": "<base64 over canonical params>"
      }
    }
  }
}
```

The `_adam` block is non-standard MCP and is stripped before forwarding
to a non-ADAM MCP target; in that case, the spoke records
`qsuite=classical-fallback` on the emitted FR event because the receiving
MCP server cannot verify the dual signature.

### 8.3 Method surface

| Method                       | Purpose                                                                         | Pre-Action Gate? |
|------------------------------|---------------------------------------------------------------------------------|------------------|
| `initialize`                 | capability negotiation (ADAM extension: dual-PQC handshake details)             | yes              |
| `tools/list`                 | enumerate the tool catalog scoped to the requesting spoke                       | yes (read-tier)  |
| `tools/call`                 | invoke a tool                                                                   | yes              |
| `resources/list`             | enumerate resources (ADAM-mediated docs, schemas, twin views)                   | yes (read-tier)  |
| `resources/read`             | read a resource                                                                 | yes              |
| `prompts/list`               | enumerate prompt templates (ADAM does not publish ungoverned prompt templates;  | yes (read-tier)  |
|                              | every published prompt is doctrinally reviewed)                                 |                  |
| `notifications/*`            | inbound state changes (catalog change, hub key rotation, OHSHAT broadcast)      | n/a              |
| `_adam/aic/refresh`          | (ADAM extension) request a fresh AIC pin from the hub                           | yes              |
| `_adam/conversation/open`    | (ADAM extension) request that the hub authorize an A2A conversation             | yes              |
| `_adam/conversation/close`   | (ADAM extension) close an A2A conversation and submit the converged proposal    | yes              |
| `_adam/preaction/probe`      | (ADAM extension) ask the hub to compute a Pre-Action verdict without executing  | yes              |

### 8.4 Tool definition shape

```yaml
- id: "stripe.invoice.create"                    # canonical tool id
  hub: "human_interface_hub"                     # which hub publishes it
  domain_owner: "wg-fin-txn"                     # which agent's domain owns it
  description: "Create a Stripe invoice for an existing customer."
  schema:
    type: object
    required: [customer_id, currency, line_items]
    properties:
      customer_id: { type: string, pattern: "^cus_[A-Za-z0-9]{6,}$" }
      currency:    { type: string, enum: [usd, eur, gbp] }
      line_items:  { type: array, minItems: 1 }
      due_in_days: { type: integer, minimum: 0, maximum: 90 }
  risk_tier: "low"                               # read | low | high | privileged
  boss_floor: 82                                 # min BOSS composite required to refuse (tighter for sensitive)
  min_authority_level: "TRUSTED"
  data_classes: ["pii", "internal"]
  forbidden_data_classes: ["raw_pan", "phi"]
  vault_handle: "wg-sec-vault://stripe/<account>/restricted/billing"
  egress: ["api.stripe.com:443"]
  idempotency: "client-key-required"             # always use Idempotency-Key header
  fr_namespace: "proto.tool.stripe.invoice.create"
  intent_class_required: "intent.action.stripe.invoice.create"
  collab_profile_required: "strict-agentic-flow|mixed"
```

### 8.5 Capability tiers and approval gates

Inherited from the Sovereignty Connector pattern; this card promotes them
to canonical for all MCP servers ADAM operates or consumes:

| Tier         | Effect                                                                                                                  | Approval                                  |
|--------------|-------------------------------------------------------------------------------------------------------------------------|-------------------------------------------|
| `read`       | inspect only; no mutation                                                                                               | none                                      |
| `low`        | local cluster mutation (apply manifest, write to local datastore)                                                       | none                                      |
| `high`       | host-level install, vendor-API mutation                                                                                 | Domain Governor concurrence               |
| `privileged` | destructive, cross-domain, or director-only (e.g., takedown, vault key issuance, production cutover, scope expansion)   | director quorum (5+2) + OHSHAT-style FR   |

### 8.6 Initialize handshake

```
client → server:  initialize { protocolVersion, capabilities, _adam.aic_pin }
server → client:  initialize_result { ..., _adam: { hub_aic_pin, supported_qsuites: [hybrid, classical-fallback] } }
client ← server:  notifications/initialized
```

ADAM extension on `initialize`:

* both parties exchange AIC pins (SHA3-512 of the AIC body) so a man-in-the-middle that holds
  only one side's public material cannot complete the handshake;
* both parties run a hybrid `X25519+ML-KEM-768` key-agreement before the
  first JSON-RPC frame, deriving an AEAD session key with HKDF-SHA3-512;
* both parties advertise their `qsuite` set; the chosen suite is the
  intersection's strongest member;
* if any of the above fails, the server emits `proto.mcp.handshake.failed`
  and refuses subsequent calls.

### 8.7 Pre-Action Gate (synchronous, in-process at the hub)

```
preAction(req):
    if req.spoke_aic.invalid:        emit("proto.mcp.refused", reason="aic-invalid"); deny.
    if req.spoke.authority < tool.min_authority_level:
                                     emit("proto.mcp.refused", reason="authority-low"); deny.
    if req.tool not in spoke.catalog:emit("proto.mcp.refused", reason="tool-not-bound"); deny.
    if req.intent_id is null and tool.intent_class_required is set:
                                     emit("proto.mcp.refused", reason="intent-missing"); deny.
    if req.data_classes - tool.data_classes_allowed != ∅:
                                     emit("proto.mcp.refused", reason="data-class-violation"); deny.
    if rate_window(req.tool) > tool.rate_ceiling:
                                     emit("proto.mcp.refused", reason="rate-ceiling"); deny.
    if egress_target not in tool.egress:
                                     emit("proto.mcp.refused", reason="egress-violation"); deny.
    if boss_compose(req) > tool.tier_ceiling:
                                     emit("proto.mcp.refused", reason="boss-tier"); deny.
    if sacred_boundary_violated(req):emit("proto.mcp.refused", reason="sacred-boundary"); ohshat.
    if doctrine_self_amend(req):     emit("proto.mcp.refused", reason="doctrine-self-amend"); ohshat.
    if !verify_dual_sig(req):        emit("proto.mcp.refused", reason="signature-invalid"); deny.
    record fr.proto.mcp.preaction.ok; allow.
```

The Pre-Action Gate is **synchronous and in-process** within the hub. It
cannot be skipped by a network or sidecar failure because the hub holds
the only credential that can produce a valid downstream call — that
credential is gated by the gate.

### 8.8 Hub redundancy and sharding

Each canonical hub is an HA Deployment with at least 3 replicas behind a
Service. The OPA bundle and the catalog database are loaded by every
replica at boot and refreshed on `proto.mcp.catalog.refresh`. The Pre-Action
Gate is stateless w.r.t. hub state — every replica computes the same
verdict for the same input. Per-tool rate windows are tracked against the
ADAM bus (Kafka topic `proto.mcp.rate`), not in hub memory, so sharding
does not break rate enforcement.

## 9. External-MCP-Server-Contract Pattern

External MCP servers (Microsoft Azure AI Foundry MCP endpoints, vendor
agent tools, customer-side MCP servers) are bound to ADAM exactly as
adapters bind via `_CONTRACT_SPEC`. The shape is identical except the
contract object names the MCP server's identity in place of an external
system.

```json
{
  "contract_id": "mcp-server-<name>-contract",
  "schema_version": "adam-mcp-server-contract-v1",
  "server_card_id": "proto-mcp-a2a",
  "server_endpoint_class": "saas|onprem|hybrid",
  "doctrine_version": "adam-book-new@v0.3",
  "issued_at": "<RFC3339>",
  "issued_by": { "agent_id": "ga-security", "co_signers": ["ga-legal", "orch-policy"] },
  "valid_from": "<RFC3339>",
  "valid_until": "<RFC3339>",
  "external_server": {
    "name": "azure-ai-foundry-mcp-prod",
    "endpoint": "https://<tenant>.foundry.azure.com/mcp",
    "residency": ["eu-west", "us-east"]
  },
  "identity": {
    "vault_key_handle": "wg-sec-vault://mcp/azure-ai-foundry/oauth",
    "rotation_policy": "every 60 days",
    "quantum_lock": "hybrid-where-supported, classical-fallback recorded"
  },
  "allowed_tools": [
    { "name": "foundry.assistant.invoke",   "data_classes": ["internal"]      },
    { "name": "foundry.embedding.create",   "data_classes": ["internal"]      },
    { "name": "foundry.evaluation.run",     "data_classes": ["internal"]      }
  ],
  "forbidden_tools": [
    "foundry.assistant.invoke_with_pii",
    "foundry.export.full"
  ],
  "data_classes_allowed":   ["pii", "internal"],
  "data_classes_forbidden": ["phi", "pci", "raw_pan"],
  "egress_allowlist": ["<tenant>.foundry.azure.com:443"],
  "boss_score_floor": 70,
  "fr_event_namespace": "proto.mcp.azure-ai-foundry.*",
  "intent_object_required_for": [
    "tool_addition", "scope_expansion", "credential_rotation_off_cycle",
    "rate_ceiling_increase", "residency_change", "termination", "suspension"
  ],
  "rfm_chain_anchor": "<FR event hash>",
  "signatures": {
    "ed25519":   "<base64 ed25519 signature>",
    "ml_dsa_65": "<base64 ml-dsa-65 signature>"
  },
  "fr_anchor_hash": "<sha3-512 of preceding FR head>"
}
```

Lifecycle (DRAFT → CO-SIGNED → BOUND → ACTIVE → SUSPENDED → RFM-PENDING →
AMENDED → RENEWED → TERMINATED → ARCHIVED) is identical to the adapter
contract lifecycle in `_CONTRACT_SPEC.md` §3.

## 10. A2A Protocol Profile (ADAM-A2A)

ADAM-A2A is gRPC + Protobuf + mTLS 1.3 with hybrid-PQC handshake. The
protocol is inherited from AGT Agent Mesh A2A (per
`agt-agent-mesh-config.yaml`); ADAM adds the constraints below.

### 10.1 Transport

* Primary: gRPC over mTLS 1.3.
* Cipher suites (priority): `TLS_AES_256_GCM_SHA384`,
  `TLS_CHACHA20_POLY1305_SHA256`, `TLS_AES_128_GCM_SHA256`.
* Hybrid handshake: `X25519+ML-KEM-768` key-agreement before the first
  Protobuf frame.
* Connection pool: 100 conns/agent; keepalive 30 s; max idle 300 s.
* Compression: `gzip` for messages ≥ 1 KB.
* Service discovery: DID-based, with DNS SRV `_adam-mesh._tcp` for
  bootstrap.

### 10.2 Protobuf message envelope

```protobuf
syntax = "proto3";
package adam.proto.a2a.v1;

message A2AEnvelope {
  string  envelope_id      = 1;   // uuid v7
  string  conversation_id  = 2;   // bound by Conversation Contract
  string  intent_id        = 3;   // optional; if set, anchors to Intent Object
  string  sender_did       = 4;
  string  receiver_did     = 5;   // or "broadcast:<scope>"
  int64   sent_at_unix_ns  = 6;
  string  schema_version   = 7;   // "adam-a2a-v1"

  // application payload
  bytes   payload_bytes    = 10;
  string  payload_schema   = 11;  // e.g. "innovation.proposal.v1"

  // governance pre-eval (filled by sender Pre-Send Gate)
  uint32  boss_pre_composite = 20;
  string  boss_pre_tier      = 21; // SOAP|MODERATE|ELEVATED|HIGH|OHSHAT
  bool    is_non_idempotent  = 22;
  string  replay_marker      = 23; // uuid v7

  // dual signatures
  bytes   sig_ed25519        = 30;
  bytes   sig_ml_dsa_65      = 31;

  // FR linkage
  string  fr_pre_anchor_hash = 40;
}
```

### 10.3 Conversation Contract

```json
{
  "conversation_id": "conv-<scope>-<epoch>",
  "schema_version": "adam-a2a-conversation-v1",
  "scope_purpose": "innovation.experiment.evaluation",
  "issued_by": { "agent_id": "orch-policy", "co_signers": ["ga-security", "ga-operations"] },
  "valid_from": "<RFC3339>",
  "valid_until": "<RFC3339>",
  "max_duration_seconds": 3600,
  "allowed_dids": [
    "did:adam:ai-innov-experiment",
    "did:adam:ai-innov-rollout",
    "did:adam:ai-innov-results"
  ],
  "domain": "ai_centric_division",
  "boss_score_floor": 30,
  "boss_score_ceiling": 50,
  "allowed_payload_schemas": [
    "innovation.proposal.v1",
    "innovation.objection.v1",
    "innovation.evidence.v1"
  ],
  "forbidden_topics": ["pii", "phi", "raw_pan", "directors_personal_data"],
  "max_messages_per_minute": 60,
  "max_total_messages": 2000,
  "transcript_anchor": "fr.proto.a2a.transcript.<conversation_id>",
  "convergence_required": true,
  "convergence_target_class": "intent.action.innovation.proposal",
  "signatures": { "ed25519": "<...>", "ml_dsa_65": "<...>" },
  "fr_anchor_hash": "<...>"
}
```

A Conversation Contract MUST be issued before the first A2A envelope and
MUST be referenced by every envelope's `conversation_id`. Conversations
that exceed `valid_until`, `max_duration_seconds`, `max_messages_per_minute`,
or `max_total_messages` are auto-closed by `orch-policy`. Forbidden topics
are detected by token-pattern + classifier and block the message at the
sender's Pre-Send Gate.

### 10.4 Pre-Send Gate (synchronous, in-process at the sender)

```
preSend(env):
    if !verify_self_aic():          emit("proto.a2a.refused", reason="self-aic-invalid"); deny.
    if env.receiver not in conversation.allowed_dids:
                                    emit("proto.a2a.refused", reason="receiver-not-allowed"); deny.
    if env.payload_schema not in conversation.allowed_payload_schemas:
                                    emit("proto.a2a.refused", reason="schema-not-allowed"); deny.
    if topic(env.payload) in conversation.forbidden_topics:
                                    emit("proto.a2a.refused", reason="topic-forbidden"); deny.
    if rate_window(env.conversation_id) > conversation.max_messages_per_minute:
                                    emit("proto.a2a.refused", reason="rate-ceiling"); deny.
    if total_window(env.conversation_id) >= conversation.max_total_messages:
                                    emit("proto.a2a.refused", reason="conversation-exhausted"); auto-close.
    if boss_pre_eval(env) > conversation.boss_score_ceiling:
                                    emit("proto.a2a.refused", reason="boss-ceiling"); deny.
    if env.collab_profile != "collaborative" and env.collab_profile != "mixed":
                                    emit("proto.a2a.refused", reason="collab.profile.violation"); deny.
    record fr.proto.a2a.send.ok; sign; ship.
```

### 10.5 Pre-Receive Gate (synchronous, in-process at the receiver)

```
preReceive(env):
    if !verify_dual_sig(env, sender_aic): refuse.
    if env.conversation_id invalid:        refuse.
    if env.sender_did not in conversation.allowed_dids: refuse.
    if env.payload_schema not in conversation.allowed_payload_schemas: refuse.
    if !verify_replay_window(env):         refuse.
    if env.fr_pre_anchor_hash not in known_FR_heads_window: refuse (stale).
    record fr.proto.a2a.receive.ok; deliver to handler.
```

### 10.6 Conversation patterns supported

| Pattern                        | Description                                                                              |
|--------------------------------|------------------------------------------------------------------------------------------|
| `request_response`             | bounded 1:1 exchange; up to 8 round-trips                                                |
| `broadcast_to_workgroup`       | sender → all-allowed-dids; replies are 1:1                                               |
| `gossip_to_workgroup`          | bounded propagation with hop-count cap; used for innovation-evidence circulation         |
| `multi_party_session`          | up to 8 agents in a contracted session with explicit turn-taking                         |
| `peer_review`                  | sender posts a proposal; reviewers post objections; orchestrator collates                |
| `convergence`                  | terminal pattern; produces a single converged Intent Object signed by all participants   |

### 10.7 Conversation closure & convergence

A Conversation Contract requires `convergence_required: true` (default).
On closure (reached `valid_until`, `max_duration_seconds`, explicit close,
or convergence reached early), the participants emit a final
`a2a.convergence.proposal` payload with the converged Intent Object body.
`orch-policy` validates that:

* every participant's signature is present,
* the proposed Intent Object class matches `convergence_target_class`,
* the proposed BOSS pre-eval is within the contract floor/ceiling.

It then submits the proposal to `hi-intent` as a normal Intent Object
flow. The conversation transcript is anchored at FR with SLH-DSA on the
closure event.

## 11. Intent Object Linkage (Protocol Class Registry)

| Protocol event                                  | Intent Object Class                            | Required Approvers                              |
|-------------------------------------------------|------------------------------------------------|-------------------------------------------------|
| Issue / re-issue AIC                            | `intent.proto.identity.aic.issue`              | wg-sec-vault, ga-security, meta-integrity       |
| Off-cycle AIC rotation                          | `intent.proto.identity.rotate.emergency`       | ga-security + CEO (director quorum at OHSHAT)   |
| Revoke AIC                                      | `intent.proto.identity.revoke`                 | ga-security (single-party allowed)              |
| Add new MCP tool to a hub                       | `intent.proto.tool_catalog.add`                | ga-security + domain governor of owning agent   |
| Promote MCP tool tier (read→low→high→privileged)| `intent.proto.tool_catalog.promote`            | ga-security + relevant domain governor + meta-stability (BOSS sim) |
| Remove MCP tool                                 | `intent.proto.tool_catalog.remove`             | ga-security + relevant domain governor          |
| Bind external MCP server                        | `intent.proto.mcp.server.bind`                 | ga-security, ga-legal, orch-policy              |
| Amend external MCP server contract              | `intent.proto.mcp.server.amend`                | ga-security + scope-relevant governor           |
| Open an A2A Conversation Contract               | `intent.proto.a2a.conversation.open`           | orch-policy + ga-security + ga-operations       |
| Amend a Conversation Contract mid-flight        | `intent.proto.a2a.conversation.amend`          | orch-policy + ga-security                       |
| Close a Conversation Contract                   | `intent.proto.a2a.conversation.close`          | orch-policy                                     |
| Change collab profile of an agent               | `intent.proto.collab_profile.change`           | ga-security + ga-operations + meta-stability    |
| Emergency suspension of a hub                   | `intent.proto.mcp.hub.suspend`                 | director quorum (CISO + CEO at minimum)         |
| Doctrine version bump (forces global rebind)    | `intent.proto.identity.doctrine_version.bump`  | full director quorum (5+2)                      |

Every protocol Intent Object MUST reference: (a) the prior FR head hash,
(b) the proposed change body, (c) the BOSS sim result, (d) the
`meta-integrity` doctrine-non-amendment verdict. Pre-Action Gates refuse
any protocol-scope change that lacks a fully populated Intent Object.

## 12. Routing Matrix — When to use MCP vs A2A

This matrix is canonical. The runtime enforces it at the Pre-Action /
Pre-Send Gate. Implementations that disagree are wrong.

| Situation                                                              | Use MCP? | Use A2A? | Rationale                                                                          |
|------------------------------------------------------------------------|:--------:|:--------:|------------------------------------------------------------------------------------|
| Agent invokes an external system (Stripe, SAP, Workday, …)             |    ✅    |    ❌    | Adapter is a tool; tool calls go through MCP                                       |
| Agent invokes an internal ADAM capability (twin sim, BOSS rerun, …)    |    ✅    |    ❌    | Twins/Meta-Gov are MCP hubs                                                        |
| Director or operator drives an action through console                  |    ✅    |    ❌    | Goes through `hi-gateway` MCP hub                                                  |
| Innovation / scenario / strategy ideation across workgroup peers       |    ❌    |    ✅    | Multi-perspective deliberation; star topology would over-serialize                 |
| Ethics-alignment review of a candidate model rollout                   |    ❌    |    ✅    | Multi-agent peer review under Conversation Contract                                |
| Intent classification by `hi-intent`                                   |    ✅    |    ❌    | `hi-intent` is itself an HI hub                                                    |
| Strict-agentic-flow step (e.g., `wg-fin-txn` posts a journal entry)    |    ✅    |    ❌    | A2A forbidden in strict flows                                                      |
| Cross-domain governor concurrence (5 governors concur on an Intent)    |    ✅*   |    ❌    | * `orch-policy` orchestrates via MCP `concur` calls; not a peer chat               |
| Twins broadcasting a divergence > 5%                                   |    ✅    |    ❌    | Broadcast notification on the Twins MCP hub                                        |
| Workgroup post-mortem after a refusal                                  |    ❌    |    ✅    | Multi-agent retrospective; bounded Conversation Contract                           |
| Adapter ↔ Adapter coordination                                         |   N/A    |    ❌    | Adapters never talk to each other directly; orchestrator mediates via MCP          |
| Director ↔ Director (human ↔ human)                                    |   N/A    |   N/A    | Out of scope; humans use Directors Dashboard, not MCP/A2A                          |

## 13. Collaborative-Flow vs Strict-Agentic-Flow Classification

Every agent in the 81-mesh and the 34 ADAMPLUS extensions has a
`collab_profile` ∈ `{strict-agentic-flow, collaborative, mixed}`. The
profile is bound in the AIC and is not changeable without an
`intent.proto.collab_profile.change` Intent Object.

### 13.1 Default classification table (canonical)

The following is the canonical Day-1 classification. Implementations MAY
narrow scope (e.g., move a `mixed` agent to `strict`) per DNA tuning;
they MAY NOT broaden it.

#### Human Interface (3) — all `mixed`

| Agent ID    | Profile | Notes                                                                          |
|-------------|---------|--------------------------------------------------------------------------------|
| hi-intent   | mixed   | Collaborative inside intent triage; strict on the FR-anchor emission.          |
| hi-gateway  | mixed   | Collaborative on director console; strict on every authenticated action.       |
| hi-explain  | mixed   | Collaborative on explanation drafting; strict on what evidence it cites.       |

#### Domain Governors (5) — all `mixed`

| Agent ID      | Profile |
|---------------|---------|
| ga-financial  | mixed   |
| ga-legal      | mixed   |
| ga-security   | mixed   |
| ga-market     | mixed   |
| ga-operations | mixed   |

Governors collaborate inside their domain workgroups but produce
single-signed concurrence/refusal that flows through MCP only.

#### Orchestration (4) — all `strict-agentic-flow`

| Agent ID       | Profile                   |
|----------------|---------------------------|
| orch-global    | strict-agentic-flow       |
| orch-policy    | strict-agentic-flow       |
| orch-exception | strict-agentic-flow       |
| orch-evidence  | strict-agentic-flow       |

Orchestrators are deterministic. They receive structured inputs and emit
structured outputs. They never participate in a conversation.

#### Corporate Work Groups (39) — by sub-domain

| Sub-domain | Agents                                                              | Default Profile         |
|------------|---------------------------------------------------------------------|-------------------------|
| Financial  | wg-fin-txn, -recon, -budget, -capital, -audit, -efficiency          | strict-agentic-flow     |
| Legal      | wg-legal-contract, -reg, -compliance, -risk, -jurisdiction          | mixed                   |
| Risk       | wg-risk-assess, -monitor, -liability                                | mixed                   |
| Market     | wg-market-customer, -partner, -intel, -demand, -reputation          | collaborative (intel/demand/reputation) / mixed (customer/partner) |
| Ops        | wg-ops-translate, -innovation, -dependency, -recovery, -bc, -resilience, -catastrophe | -translate=strict; -innovation=collaborative; rest mixed |
| Security   | wg-sec-threat, -access, -incident, -vault                           | strict-agentic-flow (vault); mixed (others, but never collaborative on key issuance) |
| Governance | wg-gov-board, -stakeholder, -filing, -compliance                    | mixed (board/stakeholder); strict (filing/compliance) |
| Data       | wg-data-gov, -quality, -residency, -pii, -rights                    | strict-agentic-flow (residency/pii/rights); mixed (gov/quality) |

#### AI-Centric Division (23)

| Agent ID                  | Profile         |
|---------------------------|-----------------|
| ai-auto-budget            | strict          |
| ai-auto-authority         | strict          |
| ai-auto-escalation        | strict          |
| ai-audit-collect          | strict          |
| ai-audit-correlate        | mixed           |
| ai-audit-simulate         | mixed           |
| ai-ethics-bias            | collaborative   |
| ai-ethics-fairness        | collaborative   |
| ai-ethics-alignment       | collaborative   |
| ai-model-registry         | strict          |
| ai-model-drift            | strict          |
| ai-data-pipeline          | strict          |
| ai-data-knowledge         | mixed           |
| ai-innov-experiment       | collaborative   |
| ai-innov-rollout          | mixed           |
| ai-innov-results          | collaborative   |
| ai-core-sync              | strict          |
| ai-core-alignment         | mixed           |
| ai-external-stakeholder   | mixed           |
| ai-external-regulatory    | strict          |
| ai-strategy-align         | collaborative   |
| ai-strategy-competitive   | collaborative   |
| ai-strategy-scenario      | collaborative   |

#### Digital Twins (4) — all `mixed`

Twins speak in scenarios and divergences; collaborative inside
simulation, strict on what they assert downstream.

#### Meta-Governance (3) — all `strict-agentic-flow`

| Agent ID         | Profile             |
|------------------|---------------------|
| meta-stability   | strict              |
| meta-integrity   | strict              |
| meta-audit       | strict              |

Meta-Governance never collaborates. It observes, scores, and refuses.

#### ADAMPLUS Financial Operations (12) — all `strict-agentic-flow`

AR/AP/Treasury/FX/Tax/GL flows are deterministic by regulatory
requirement.

#### ADAMPLUS HR (7)

| Agent ID                   | Profile |
|----------------------------|---------|
| adamplus-hr-onboarding     | mixed   |
| adamplus-hr-offboarding    | strict  |
| adamplus-hr-payroll        | strict  |
| adamplus-hr-benefits       | mixed   |
| adamplus-hr-time           | strict  |
| adamplus-hr-performance    | mixed   |
| adamplus-hr-compliance     | strict  |

#### ADAMPLUS CRM (5) — all `mixed` or `collaborative`

| Agent ID            | Profile         |
|---------------------|-----------------|
| adamplus-crm-360    | mixed           |
| adamplus-crm-lead   | collaborative   |
| adamplus-crm-pipeline | mixed         |
| adamplus-crm-success | mixed          |
| adamplus-crm-cases  | mixed           |

#### ADAMPLUS Operations (6) — by line

| Agent ID                        | Profile         |
|---------------------------------|-----------------|
| adamplus-ops-content-catalog    | mixed           |
| adamplus-ops-streaming          | strict          |
| adamplus-ops-subscription       | strict          |
| adamplus-ops-mes (mfg)          | strict          |
| adamplus-ops-ehr (health)       | strict          |
| adamplus-ops-trading (fin)      | strict          |

#### ADAMPLUS ITSM (2) and Procurement (2)

| Agent ID                  | Profile |
|---------------------------|---------|
| adamplus-itsm-incident    | mixed   |
| adamplus-itsm-change      | strict  |
| adamplus-proc-sourcing    | mixed   |
| adamplus-proc-po          | strict  |

### 13.2 The non-bypass invariant

**No agent — collaborative, strict, or mixed — can ever bypass governance.**
The Pre-Send Gate, the Pre-Action Gate, BOSS scoring, Sacred Boundaries,
the doctrine-non-amendment check, the Vault binding, and the Flight
Recorder anchor apply equally to both planes. Specifically:

* A collaborative agent in a Conversation Contract is **still subject to**
  every BOSS dim, every CORE rule, every AGT trust check, and every
  Director quorum requirement at the moment its converged proposal is
  submitted as an Intent Object.
* A strict agent's idempotency-keyed MCP call is **still subject to**
  Sacred Boundaries — an OHSHAT trip refuses the call regardless of how
  routine the flow is.
* A mixed agent **cannot** straddle the planes by, e.g., trying to send
  an A2A message to coordinate a strict-flow step. The Pre-Send Gate
  refuses with `collab.profile.violation` and the attempt is logged as
  an incident.

### 13.3 Worked examples

* **Innovation portfolio** (`wg-ops-innovation`, `ai-innov-experiment`,
  `ai-innov-rollout`, `ai-innov-results`, `ai-strategy-scenario`):
  collaborative A2A under a Conversation Contract; converges on an
  `intent.action.innovation.proposal`; submitted via MCP through
  `hi-intent` → BOSS → Governors → `orch-policy` → `orch-evidence`.
* **Vendor invoice payment** (`adamplus-ap-vendor-invoice`,
  `adamplus-ap-3way-match`, `adamplus-ap-payment-run`,
  `adapter-stripe`/`adapter-sap-s4hana`/`adapter-coupa`): strict-agentic-flow.
  No A2A. Each step is an MCP tool call recorded with an idempotency key.
* **Content takedown after legal hold** (`adapter-netstreamx-cms`,
  `wg-legal-contract`, `wg-data-rights`, `ga-legal`): mixed. Inside the
  legal review workgroup, a bounded A2A conversation; takedown itself
  is a privileged MCP tool call requiring director quorum.
* **Quarterly tax filing** (`adamplus-fin-tax-calc`, `adamplus-fin-tax-file`,
  `wg-gov-filing`, `wg-fin-audit`): strict-agentic-flow. Deterministic.
  Audit trail is the proof.
* **Customer support refund > $500**: mixed. Customer-interaction agent
  collaborates briefly with finance/audit; the refund itself is a strict
  MCP tool call gated by BOSS.

## 14. Governance Gating Stack (per call, per message)

Every MCP tool call and every A2A message passes through every gate
below, in this order, synchronously and in-process. A failure at any
gate refuses the call. There is no "fast path."

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INBOUND CALL/MESSAGE                         │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │ 1. AIC verification (issuer chain, valid_until,│
        │    revocation list, dual signature)            │
        └──────────────────────────────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │ 2. IATP authority check                       │
        │    (current trust score → authority level)    │
        └──────────────────────────────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │ 3. Catalog binding / Conversation membership  │
        │    (tool ∈ catalog OR sender ∈ allowed_dids)  │
        └──────────────────────────────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │ 4. Intent linkage                             │
        │    (Intent Object exists, class matches)      │
        └──────────────────────────────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │ 5. CORE doctrine non-amendment check          │
        │    (meta-integrity OPA bundle)                │
        └──────────────────────────────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │ 6. Sacred Boundary check (OHSHAT trip if hit) │
        └──────────────────────────────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │ 7. BOSS Pre-Action / Pre-Send composite       │
        │    + critical-dim override + non-idempotent   │
        │    +15 → tier routing                         │
        └──────────────────────────────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │ 8. AGT runtime ring assignment + Exception    │
        │    Economy routing                            │
        └──────────────────────────────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │ 9. Vault token mint (Ed25519 + ML-DSA-65)     │
        │    valid only for this single call            │
        └──────────────────────────────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │ 10. FR pre-action emission (chain-anchored)   │
        └──────────────────────────────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │ 11. ACTION (the actual tool call / message)   │
        └──────────────────────────────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │ 12. FR post-action emission + outcome boss    │
        │     dim feedback for IATP factor update       │
        └──────────────────────────────────────────────┘
```

If any gate refuses, FR records the refusal with reason; no downstream
gates run; the vault token is never minted; the action never occurs.

## 15. Tool Catalog Binding (TCB) Schema

The Tool Catalog Binding is the per-agent record of which tools the agent
may invoke through which hub. Issued by `wg-sec-vault` co-signed by
`ga-security` and the agent's Domain Governor.

```yaml
tcb_id: "tcb-wg-fin-txn-2026-05-06"
schema_version: "adam-tcb-v1"
agent_id: "wg-fin-txn"
issued_by:
  agent_id: "wg-sec-vault"
  co_signers: ["ga-security", "ga-financial"]
issued_at: "2026-05-06T00:00:00Z"
valid_from: "2026-05-06T00:00:00Z"
valid_until: "2026-08-04T00:00:00Z"  # 90 d
hub_bindings:
  human_interface_hub:
    allowed_tools:
      - id: "stripe.invoice.create"
        max_authority_required: "TRUSTED"
        boss_floor: 82
        rate_per_min: 30
      - id: "stripe.invoice.finalize"
        max_authority_required: "TRUSTED"
        boss_floor: 82
        rate_per_min: 60
      - id: "stripe.refund.create"
        max_authority_required: "VERIFIED"
        boss_floor: 70
        rate_per_min: 5
        per_call_intent_class: "intent.action.stripe.refund.create"
  meta_governance_hub:
    allowed_tools:
      - id: "doctrine.read"
        max_authority_required: "STANDARD"
  digital_twins_hub:
    allowed_tools:
      - id: "twin.economic.simulate"
        max_authority_required: "STANDARD"
forbidden_tools:
  - "stripe.payout.create"
  - "stripe.connect.account.create"
  - "doctrine.write"
  - "vault.key.issue"
fr_event_namespace: "proto.tool.wg-fin-txn.*"
signatures:
  ed25519: "<...>"
  ml_dsa_65: "<...>"
```

Pre-Action Gate uses the TCB as the authoritative source of "may this
agent invoke this tool" — not the hub's catalog alone, not the agent's
self-declaration.

## 16. BOSS Floors and Tier Ceilings (defaults — overridable per tool)

| Surface                          | Default BOSS floor | Default tier ceiling |
|----------------------------------|-------------------:|----------------------|
| MCP read-tier tool               | 30                 | MODERATE             |
| MCP low-tier tool                | 50                 | ELEVATED             |
| MCP high-tier tool               | 70                 | HIGH                 |
| MCP privileged-tier tool         | 85                 | HIGH (OHSHAT trips quorum) |
| A2A message inside a Conversation| (per CC)           | (per CC)             |
| External-MCP-server (default)    | 70                 | ELEVATED             |
| External-MCP-server (PII / PHI)  | 82                 | HIGH                 |
| External-MCP-server (regulatory filing) | 88          | HIGH                 |

Per-adapter and per-tool floors override the default. Where a strict-flow
adapter (Stripe Treasury, SWIFT, FIX, regulatory filings) is involved, the
floor is set per the relevant adapter contract — typically ≥ 82.

## 17. Sacred Boundaries (OHSHAT)

Sacred Boundaries are doctrine-level invariants that may not be crossed
under any BOSS or trust posture. Hitting one trips OHSHAT regardless of
the composite. The protocol surface enforces Sacred Boundaries at gate 6
(§14). The canonical NetStreamX boundaries are inherited from
`exception_economy/exception_router.py`; protocol-relevant ones are:

| Boundary                                                           | Trip behavior                                              |
|--------------------------------------------------------------------|------------------------------------------------------------|
| Doctrine self-amendment via tool call                              | OHSHAT; full director quorum; agent suspended              |
| Vault key issuance / rotation outside policy window                | OHSHAT; director quorum; all dependent agents rebind       |
| Underage-content playback / age-rating bypass                      | OHSHAT; takedown; director quorum                          |
| Region-lock bypass on adapter call                                 | OHSHAT; refusal; legal review                              |
| Raw PAN / PHI / SSN in a tool argument                             | OHSHAT; refusal; data classification incident              |
| A2A from / to a forbidden DID pattern (e.g. director personal data)| OHSHAT; refusal; conversation auto-closed                  |
| Cross-adapter PII fan-out without an Intent Object of class `pii.transfer` | OHSHAT; refusal                                    |
| MCP tool call with `qsuite=classical-fallback` against a `data_classes ⊇ {pii, phi, pci}` tool | OHSHAT; refusal                |

OHSHAT trips are dual-signed with SLH-DSA additionally on emission — the
event is doctrine-grade evidence.

## 18. Failure Posture & Refusal Matrix

| Condition                                                  | Behavior                                                 |
|------------------------------------------------------------|----------------------------------------------------------|
| AIC missing / invalid                                      | inert; refuse all; emit `proto.identity.aic.absent`      |
| AIC valid but `valid_until` in past                        | inert; refuse all; emit `proto.identity.aic.expired`     |
| Catalog (TCB) missing / expired                            | inert; refuse all; emit `proto.tool.tcb.absent`          |
| Conversation Contract missing for an A2A send              | refuse send; emit `proto.a2a.refused`                    |
| Hub key rotation in flight                                 | refuse; client retries with refreshed pin                |
| Doctrine version mismatch                                  | inert; refuse; emit `proto.identity.doctrine.mismatch`   |
| Trust score < 100                                          | inert; refuse; emit `proto.identity.suspended`           |
| Sacred Boundary tripped                                    | refuse; OHSHAT broadcast; agent quarantined              |
| Egress allowlist breach                                    | refuse; emit `proto.mcp.refused.egress`                  |
| Replay-window violation                                    | refuse; emit `proto.a2a.refused.replay` / `.mcp.refused.replay` |
| Rate ceiling hit                                           | refuse; back off; emit `proto.mcp.refused.rate`          |
| Hub overloaded (circuit breaker open)                      | refuse; redirect to standby replica; emit `proto.mcp.circuit.open` |
| Receiver disconnected mid-A2A                              | retry per conversation contract; close on exhaustion     |
| FR head not yet visible to the spoke                       | refuse; emit `proto.session.fr.head.stale`; retry        |

## 19. Smart-Plane Behaviors (mandatory per surface)

Both planes MUST implement:

1. **Self-introspection.** Expose bound AIC head, current TCB head, current
   active Conversation Contracts, and last refusals over `proto.session.head`.
2. **Drift detection.** Continuously compare hub catalog hash to TCB hub
   bindings; on drift, file an `intent.proto.tool_catalog.amend` RFM. Do
   not silently broaden scope.
3. **Rate self-throttling.** Track per-tool / per-conversation rate windows
   on the bus topic `proto.mcp.rate` / `proto.a2a.rate`. Never rely solely
   on remote 429s.
4. **Egress fencing.** Enforce `egress_allowlist` via seccomp / CNI; do
   not trust DNS.
5. **Replay defense.** 5-minute replay window on every dual-signed
   message; persistent (idempotency journal) replay-protection across
   restarts.
6. **Heartbeat with attestation.** Heartbeats carry the current AIC head
   hash and TCB head hash so monitors detect silent divergence.
7. **No latent state.** No durable state outside FR + vault + idempotency
   journal. Safe to destroy and respawn at any time.
8. **Refusal recording.** Every refusal is a first-class FR event with a
   reason taxonomy (§22).
9. **Convergence enforcement** (A2A only). Cannot exit a conversation
   without a converged proposal or a logged closure reason.
10. **OHSHAT propagation.** OHSHAT events received on the bus pause every
    in-flight call/message until cleared.

## 20. Day-1 PQC Posture Recap

Per the canonical Day-1 baseline declared in
`Build Cards/ADAM Agent Definitions/_INDEX.md` and re-stated in
`_CONTRACT_SPEC.md` §9:

* All MCP/A2A signatures: hybrid `Ed25519 + ML-DSA-65` (NIST FIPS 204).
* All in-cluster mTLS: hybrid `X25519 + ML-KEM-768` (NIST FIPS 203).
* All AIC issuance: dual `Ed25519 + ML-DSA-65`; SLH-DSA long-term anchor.
* Vault at-rest wrap: `ML-KEM-1024` (longer-strength variant).
* Every protocol scope-change FR event additionally signed with `SLH-DSA`
  (NIST FIPS 205) and stored in `tamper_evident.attestations[]`.
* `qsuite=classical-fallback` is recorded on every event where the peer
  could not negotiate hybrid; CMSA-2.0-conformant audit can compute
  exposure exactly.
* No classical-only path lands in production. CMSA 2.0 conformant from
  Day-1 (Jan 2027 deadline already met).

## 21. Sandbox & Containment (RGI-03)

Every spoke and every hub runs inside an Execution Ring per AGT runtime:

| Ring | Class                                      | Capabilities                                                |
|------|---------------------------------------------|-------------------------------------------------------------|
| 0    | Meta-Governance, Digital Twins              | doctrine read; schema registry write under Intent           |
| 1    | Domain Governors                            | concurrence/refusal only; no execution                      |
| 2    | Orchestration, Human Interface              | orchestrate; never execute against externals directly       |
| 3    | Corporate WG, AI-Centric, ADAMPLUS, Adapters| execute; gated by every gate above                          |

Ring crossings are themselves MCP tool calls and are recorded.

* Saga compensation (per AGT runtime config) covers strict-agentic-flow
  multi-step sequences. If step N fails, the orchestrator runs the
  recorded compensating tool calls in reverse order and records each.
* OHSHAT kill switch is a global broadcast that pauses every Ring 2/3
  spoke; only Ring 0 may resume after director quorum.
* Network policy mirrors `egress_allowlist` per agent class and per
  Domain.

## 22. Flight Recorder Event Catalog (Common to All Protocol Surfaces)

```
proto.identity.aic.requested
proto.identity.aic.issued
proto.identity.aic.bound
proto.identity.aic.refreshed
proto.identity.aic.expired
proto.identity.aic.revoked
proto.identity.aic.compromise_suspected
proto.identity.aic.absent
proto.identity.doctrine.mismatch
proto.identity.suspended

proto.tool.tcb.issued
proto.tool.tcb.bound
proto.tool.tcb.expired
proto.tool.tcb.amended
proto.tool.tcb.absent
proto.tool.<tool_id>.preaction.ok / .refused
proto.tool.<tool_id>.action.ok / .failed
proto.tool.<tool_id>.postaction.ok / .compensated

proto.mcp.handshake.ok / .failed
proto.mcp.preaction.ok / .refused
proto.mcp.action.ok / .failed
proto.mcp.postaction.ok / .compensated
proto.mcp.refused                      (with reason taxonomy)
proto.mcp.hub.suspended / .resumed
proto.mcp.hubkey.refresh
proto.mcp.catalog.refresh
proto.mcp.circuit.open / .closed
proto.mcp.rate.pressure
proto.mcp.<server_id>.contract.bound / .activated / .amended / .terminated

proto.a2a.conversation.opened
proto.a2a.conversation.amended
proto.a2a.conversation.closed
proto.a2a.conversation.exhausted
proto.a2a.send.ok / .refused
proto.a2a.receive.ok / .refused
proto.a2a.transcript.<conversation_id>
proto.a2a.convergence.proposed
proto.a2a.convergence.refused
proto.a2a.refused                       (with reason taxonomy)

proto.session.handoff.collab_to_strict
proto.session.handoff.strict_to_collab
proto.session.head
proto.session.fr.head.stale
proto.session.boundary.tripped          (Sacred Boundary)
proto.session.ohshat.broadcast
```

Refusal reason taxonomy (the closed enum):

```
aic-invalid | aic-expired | tcb-absent | tool-not-bound |
authority-low | rate-ceiling | egress-violation |
data-class-violation | boss-tier | boss-ceiling |
intent-missing | doctrine-self-amend | sacred-boundary |
collab.profile.violation | conversation-exhausted |
receiver-not-allowed | schema-not-allowed | topic-forbidden |
signature-invalid | replay | qsuite-fallback-on-sensitive |
hub-overloaded | hub-suspended | doctrine-mismatch
```

## 23. Integration Matrix — Open-Source & Product-Specific Tools

Open-source where possible; product-specific where the user explicitly
deploys a managed service. ADAM's stance on every entry: open-source
implementations are first-class; product-specific implementations are
adapter-bound and contract-gated identically.

| Capability                    | OSS Reference (Day-1 baseline)            | Product-specific Alternatives                   | Binding Pattern in ADAM                                                          | BOSS / Tier notes                              |
|-------------------------------|-------------------------------------------|-------------------------------------------------|-----------------------------------------------------------------------------------|-----------------------------------------------|
| MCP server framework          | Anthropic MCP reference Python/TS SDKs    | Microsoft Azure AI Foundry MCP Surface; AWS Bedrock AgentCore MCP; Google Vertex Agent Builder; OpenAI Agents SDK | external-mcp-server-contract (§9); per-tool TCB binding; Pre-Action Gate          | per tool tier; PII tool ⇒ floor 82            |
| MCP client (in-cluster spokes)| Anthropic MCP client SDK (Python)         | LangGraph, CrewAI, AutoGen, Semantic Kernel    | spoke library wraps SDK; AIC-bound mTLS; signs every JSON-RPC frame              | per call                                       |
| A2A reference protocol        | AGT Agent Mesh A2A (gRPC + Protobuf)      | Google A2A Reference; LangGraph multi-agent; AutoGen group chat | gRPC + mTLS 1.3 + hybrid PQC; Conversation Contract; Pre-Send/Pre-Receive Gates  | per conversation contract                     |
| Identity / DIDs               | W3C DID Core + AGT IATP                   | Microsoft Entra Verified ID; Hyperledger AnonCreds; SPIFFE/SPIRE | `did:adam` method on top of W3C DID Core; SPIFFE/SPIRE bridge for Kubernetes ID  | identity gate                                  |
| Workload identity in K8s      | SPIFFE/SPIRE                              | Azure AD Workload Identity; AWS IAM Roles for Service Accounts; GCP Workload Identity Federation | SPIFFE-SVID bridged into AIC at boot; cluster issuer co-signed by `wg-sec-vault` | identity gate                                  |
| Vault / HSM (software)        | open-source PyNaCl + dilithium-py + sphincs+ libs | HashiCorp Vault Enterprise; Azure Key Vault HSM; AWS CloudHSM; GCP HSM | `wg-sec-vault` is the ADAM façade; product HSMs are storage backends, never replace `wg-sec-vault` | vault gate                                    |
| Policy engine                 | OPA (Rego)                                | Cedar (AWS); Azure Policy; Google IAM Conditions| `orch-policy` loads Rego bundles; product policy engines bridged via OPA-bundle export                                                                  | gate 5 (CORE)                                 |
| Telemetry                     | OpenTelemetry (OTLP) + Prometheus         | Azure Monitor + App Insights; AWS CloudWatch + X-Ray; GCP Cloud Operations; Datadog; New Relic | `adapter-otel` is canonical; product backends are sinks                          | RGI-04                                         |
| Bus / event backbone          | Apache Kafka or NATS JetStream            | Azure Service Bus / Event Hubs; AWS MSK / EventBridge; GCP Pub/Sub | Kafka topics under `proto.*`; product bridges via Kafka Connect                   | n/a                                            |
| Twins simulation              | NetworkX + custom replicas                | Azure Digital Twins; AWS IoT TwinMaker; Microsoft Fabric simulation | Twins MCP hub publishes simulation tools; product backends bound via adapter      | per simulation tool                            |
| Director console              | open-source SPA (current Directors Dashboard v0.3) | Microsoft Power Apps; ServiceNow Workspaces; Salesforce Lightning App | Console drives `hi-gateway` MCP hub; products bound via adapter                  | privileged tier                                |
| Reasoning model               | local Ollama (qwen2.5, llama3.2, mistral) | Anthropic Claude; OpenAI GPT-x; Google Gemini; Azure OpenAI; AWS Bedrock; Mistral Inference | Models live behind an MCP server façade; never given direct vault/FR access; tool-only | per call                                       |
| Reinforcement learning bound  | Microsoft Agent Lightning                 | (none — RL is gated to Lightning per CORE)     | RL training is sacred-boundary gated; topic filter + BOSS ≤ 30 ceiling           | per training job                               |
| Sandbox / Execution rings     | gVisor / Kata + Kubernetes admission      | Azure Container Apps with confidential compute; AWS Nitro Enclaves; GCP Confidential VMs | RGI-03 enforced at admission + runtime                                           | gate 8                                         |
| External-tool catalog         | open MCP catalog (community)              | Azure AI Foundry Tool Hub; AWS AgentCore Tools; OpenAI Tool Library | Every imported tool is mapped onto a TCB entry per §15                            | tier per tool                                  |
| Model registry                | MLflow                                    | Azure ML Model Registry; AWS SageMaker Model Registry; GCP Vertex Model Registry | `ai-model-registry` MCP tools; product bound via adapter                          | high tier                                      |

The matrix is **prescriptive**: open-source rows are the Day-1 reference;
product-specific rows are first-class alternatives bound through the
external-server-contract (or adapter-contract) pattern. **Choosing a
product alternative does not relax any gate.** It only changes the
backend.

## 24. Resource Profile & SLOs

| Surface              | Resource (test-scale, per replica) | Resource (full-scale, per replica) | SLO                                  |
|----------------------|-----------------------------------:|-----------------------------------:|--------------------------------------|
| MCP hub (per replica)| 2 vCPU / 4 GB                      | 8 vCPU / 32 GB                     | p99 Pre-Action Gate < 0.1 ms; p99 tools/call < 50 ms in-cluster |
| MCP spoke library    | + 0.2 vCPU / 0.2 GB                | + 0.5 vCPU / 1 GB                  | p99 envelope sign + send < 5 ms      |
| A2A peer endpoint    | + 0.5 vCPU / 1 GB                  | + 1 vCPU / 2 GB                    | p99 Pre-Send/Receive Gate < 1 ms     |
| AIC mint (vault)     | 0.5 vCPU / 1 GB shared             | 2 vCPU / 4 GB                      | mint p95 < 200 ms                    |
| Conversation orchestrator | 0.5 vCPU / 1 GB              | 2 vCPU / 4 GB                      | open p95 < 300 ms; close p95 < 200 ms|
| FR write             | shared (FR sizing)                 | shared (FR sizing)                 | append p95 < 5 ms (named-volume)     |

Hub HA: 3 replicas per hub minimum; 5 in production. Vault: 3 replicas
minimum. FR: per existing chain sizing (named-volume). All on Kubernetes
with PodDisruptionBudgets and topology-spread constraints.

## 25. Configuration Schema (canonical YAML, prescriptive)

```yaml
proto_mcp_a2a:
  version: "0.3"
  mcp:
    hubs:
      meta_governance_hub:
        replicas: { test: 1, prod: 5 }
        listeners:
          grpc:    { host: "0.0.0.0", port: 7443, tls: { hybrid: true } }
          stdio:   { enabled: true }
          http_sse: { host: "127.0.0.1", port: 7080, tls: { hybrid: false, fallback: classical } }
        agents: ["meta-stability", "meta-integrity", "meta-audit"]
        opa_bundle: "wg-sec-vault://opa/meta_governance_hub/current"
        catalog: "wg-sec-vault://catalog/meta_governance_hub/current"
      human_interface_hub:
        replicas: { test: 1, prod: 5 }
        listeners:
          grpc:    { host: "0.0.0.0", port: 7443, tls: { hybrid: true } }
          http_sse: { host: "0.0.0.0", port: 7080, tls: { hybrid: true } }
        agents: ["hi-intent", "hi-gateway", "hi-explain"]
      digital_twins_hub:
        replicas: { test: 1, prod: 3 }
        listeners:
          grpc: { host: "0.0.0.0", port: 7443, tls: { hybrid: true } }
        agents: ["twin-enterprise", "twin-operational", "twin-economic", "twin-risk"]
    external_servers:
      - name: "azure-ai-foundry-prod"
        endpoint: "https://<tenant>.foundry.azure.com/mcp"
        contract_id: "mcp-server-azure-ai-foundry-contract"
        residency: ["eu-west", "us-east"]
        qsuite: "hybrid-where-supported"
      - name: "anthropic-mcp-tools-marketplace"
        endpoint: "https://mcp.anthropic.com/v1"
        contract_id: "mcp-server-anthropic-marketplace-contract"
        residency: ["us-east"]
        qsuite: "classical-fallback-recorded"
    rate_limits:
      window_seconds: 60
      bus_topic: "proto.mcp.rate"
    handshake:
      hybrid_required_in_cluster: true
      hybrid_preferred_external: true
      classical_fallback_recorded: true
  a2a:
    transport:
      grpc:
        keep_alive_seconds: 30
        keep_alive_timeout_seconds: 10
        max_idle_seconds: 300
        connection_pool_size: 100
        compression: "gzip"
      mtls:
        version: "1.3"
        cipher_suites:
          - "TLS_AES_256_GCM_SHA384"
          - "TLS_CHACHA20_POLY1305_SHA256"
          - "TLS_AES_128_GCM_SHA256"
        rotation_seconds: 2592000   # 30 d
    discovery:
      did_method: "did:adam"
      registry_endpoint: "wg-sec-vault://did-registry/current"
      dns_srv: "_adam-mesh._tcp"
      cache_ttl_seconds: 3600
    conversations:
      orchestrator: "orch-policy"
      max_concurrent_per_agent: 3
      default_max_messages_per_minute: 60
      default_max_total_messages: 2000
      transcript_anchor_topic: "proto.a2a.transcript"
      slh_dsa_anchor_on_close: true
  identity:
    issuer: "wg-sec-vault"
    co_signers: ["ga-security", "meta-integrity"]
    rotation_days: 90
    qsuite:
      sign:    ["Ed25519", "ML-DSA-65"]
      keyex:   ["X25519",  "ML-KEM-768"]
      wrap:    ["ML-KEM-1024"]
      anchor:  ["SLH-DSA"]
    iatp:
      score_scale: 1000
      decay_rate_per_day: 0.01
      decay_floor: 100
  collab_profiles:
    schema_id: "agent-collab-profile-schema"
    default: "strict-agentic-flow"
    overrides_file: "wg-sec-vault://collab-profiles/current"
  governance:
    boss:
      pre_eval_engine: "boss-scorer"
      tier_routing_topic: "boss.routing"
    exception_economy:
      router: "orch-exception"
      ohshat_tier_kill_switch: true
    sacred_boundaries:
      registry: "wg-sec-vault://boundaries/current"
      slh_dsa_on_trip: true
  flight_recorder:
    schema_version: "v2.1"
    namespaces:
      - "proto.identity.*"
      - "proto.tool.*"
      - "proto.mcp.*"
      - "proto.a2a.*"
      - "proto.session.*"
    dual_sign: ["Ed25519", "ML-DSA-65"]
    long_term_anchor: "SLH-DSA"
    hot_volume: "/var/lib/adam/chain"   # per chain corruption history fix
    snapshot_to_bind_mount: true
    snapshot_interval_seconds: 300
```

## 26. RFM (Request-for-Modification) Flow for Protocol Scope

Mirrors `_CONTRACT_SPEC` §6, applied to MCP/A2A scope. Any change to:

* Tool catalog (add/remove/promote tier),
* Conversation Contract template (raising ceilings, broadening DID
  patterns, adding payload schemas),
* External MCP server contract,
* Agent collab profile,
* Hub key suite,
* IATP factor weights,
* BOSS floor on a tool,

requires an Intent Object of the corresponding class (§11) and
governor-quorum cosignature. RFMs expire if not co-signed within 14 days.
Pre-Action Gate refuses any scope-broadening tool call against an active
RFM that has not converged.

## 27. 360 QA Coverage (Pass 1–5)

This card is exercised by the canonical build-card harnesses
(`qa_all.py`, `qa_360.py`, `qa_pass3.py`, `qa_pass4.py`, `qa_pass5.py`)
and the production runtime QA at
`deployment/NetStreamX/qa/qa_suite.py`:

| Pass | Focus                                  | Card-specific tests                                                         |
|------|----------------------------------------|------------------------------------------------------------------------------|
| 1    | Schema parity (card ↔ doctrine)        | section completeness, ordering, all 35 sections present                      |
| 2    | Capability matrix                      | every MCP tool, every A2A pattern enumerated has an FR namespace             |
| 3    | Identity lifecycle                     | AIC issue → bind → rotate → revoke → re-bind clean across the chain         |
| 4    | Refusal posture                        | every row of §18 reproduced; every Sacred Boundary trip verified            |
| 5    | RFM + Intent linkage                   | tool-add, tool-promote, conversation-open, server-bind round-trips clean    |

Cross-mesh checks (`qa_360`):

* Every Agent Definition Card's `collab_profile` matches §13 default
  table.
* Every Adapter Card's tool list is 100% covered by an MCP TCB binding for
  at least one consuming agent.
* Every MCP tool has an `intent_class_required` resolvable in the Intent
  Object class registry (post-§11 reification).
* Every A2A conversation pattern in §10.6 has a representative trace in
  one of the 20 canonical real-world flows.
* Every protocol FR event in §22 is observed at least once by the live
  smoke harness.

The 117/117 `qa_suite.py` and 70/70 `views_smoke.py` baselines must remain
green after this card lands.

## 28. Build Plan (prescriptive, ordered)

Prerequisites:

* Authoritative SpecPack under `D:\ADAM\ADAM Book New\` (v0.3).
* Production runtime under `D:\ADAM\deployment\NetStreamX\` (test-scale 100/100).
* Day-1 PQC libraries available (PyNaCl, dilithium-py, sphincs+ Python bindings; `cryptography` ≥ 42 with ML-KEM/ML-DSA bindings or `pqclean`/`pqcrypto`).

Steps (each step's exit criterion is a green QA pass):

1. **Reify SpecPack schemas.**
   * `external-mcp-server-contract-schema.json` (mirrors `external-adapter-contract-schema.json`).
   * `a2a-conversation-contract-schema.json`.
   * `agent-collab-profile-schema.json`.
   * `agent-identity-certificate-schema.json` (AIC).
   * `tool-catalog-binding-schema.json` (TCB).
   Place under the canonical SpecPack schemas location at
   `ADAM Book New/ADAM - DNA Deployment Tool v0.3/example-output-netstreamx/config-bundle/schemas/`
   (the same directory that already holds `boss-score-schema.json` and the
   AGT plugin schemas at `ADAM Book New/ADAM - AGT-Plugin - FULL AGT Implementation v0.3/schemas/`).
   Version-pin every schema with `$id`.

2. **Reify FR topic registry.** Add every `proto.*` namespace from §22.
   Bump FR `event_type` enum to schema v2.2. Migrate live FR rolling
   schema entry (NOT the chain rows — the chain remains append-only).

3. **Reify Intent Object class registry.** Add every `intent.proto.*`
   class from §11. Bump Intent Object schema to v1.2. Anchor migration
   under `intent.proto.identity.doctrine_version.bump`.

4. **Vault expansion.** Extend `wg-sec-vault` to issue:
   * AICs (dual-signed, SLH-DSA-anchored on issuance);
   * TCBs;
   * Conversation Contract dual signatures;
   * external-MCP-server contract dual signatures.
   Backfill keys for the 81+34 agents already in the registry.

5. **Implement `wg-sec-vault://aic/<agent_id>/current`** access pattern in
   `auth_vault.py` and the corresponding software-HSM API.

6. **Hub services.** Stand up three HA Deployments:
   * `mcp-hub-meta-governance` (3 agents),
   * `mcp-hub-human-interface` (3 agents),
   * `mcp-hub-digital-twins` (4 agents).
   Each loads its OPA bundle, its TCB index, its catalog, and binds AICs.

7. **Spoke library.** Publish `adam-mcp-spoke-sdk` (Python first; TS
   parity by Pass 5). Every base/ADAMPLUS/adapter image consumes it. The
   library performs §14 gates 1, 4, and 5 client-side; the hub performs
   2, 3, 6–10. Both perform 11–12 in cooperation.

8. **A2A service.** Stand up `adam-a2a-orchestrator` (`orch-policy`
   inside) and `adam-a2a-mesh` (per-agent gRPC sidecar). The mesh sidecar
   ships `pre_send_gate.py` and `pre_receive_gate.py`.

9. **Conversation Contracts.** Implement the orchestrator: open / amend /
   close; transcript anchoring; convergence proposal handoff to
   `hi-intent`.

10. **TCB issuance.** Mint TCBs for the existing 81+34 agents based on
    their current Build Cards' Section 19 ("Adapters Used") + the new
    §13 collab profile defaults.

11. **External-MCP-server contracts.** Mint contracts for every external
    MCP server selected by the operator. Day-1 default: `azure-ai-foundry-prod`
    (if the operator has bound Azure) and `anthropic-mcp-tools-marketplace`
    (read-only tier ≤ low; PII forbidden).

12. **OPA bundle authoring.** Following the `OPA Rego Authoring Standards
    v0.3` document, produce:
    * `proto_mcp_preaction.rego`
    * `proto_a2a_presend.rego`
    * `proto_a2a_prereceive.rego`
    * `proto_identity_aic.rego`
    * `proto_collab_profile.rego`
    * `proto_sacred_boundaries.rego`

13. **Runtime ring & containment.** Pod admission policy mirrors §21.
    Egress NetworkPolicies mirror per-agent `egress_allowlist`.

14. **Telemetry wiring.** `adapter-otel` exports `proto.*` traces;
    metrics are scraped by Prometheus; alerting rules added for
    OHSHAT-trip rate and refusal-rate-spike.

15. **Smoke against `wg-fin-txn` + `adapter-stripe`** (a strict-flow
    representative). Verify: TCB-bound, AIC-bound, MCP tool call works,
    BOSS gate refuses raw PAN, OHSHAT trips on age-gate violation, FR
    chains and dual-signs.

16. **Smoke against `ai-innov-experiment` + `ai-innov-rollout` +
    `ai-innov-results`** (a collaborative-flow representative). Verify:
    Conversation Contract opens, A2A messages dual-signed and gated,
    convergence reached, proposal becomes Intent Object, MCP tool call
    follows, FR transcript anchored with SLH-DSA on close.

17. **QA replication to remaining mesh.** Replay 18 of the 20 canonical
    real-world flows; fix to green.

18. **Run `qa_suite.py`, `views_smoke.py`, `qa_all`, `qa_360`,
    `qa_pass3..5`** to clean. Record results in
    `deployment/NetStreamX/qa/last_run.json` and in
    `D:\ADAM\upgrade_log\UPGRADE_LOG.md`.

19. **Index updates.** Add this card to
    `Build Cards/ADAM Protocols/_INDEX.md`. The card is now the
    authoritative protocol baseline for the entire mesh.

20. **Director quorum sign-off.** Quorum vote (5+2 minus inactive)
    co-signs the Day-1 baseline. In test, Michael Lamb (proxy) signs all
    seats with `director_proxy_acting` event per seat.

## 29. Definition of Done

* `external-mcp-server-contract-schema.json`,
  `a2a-conversation-contract-schema.json`, `agent-collab-profile-schema.json`,
  `agent-identity-certificate-schema.json`,
  `tool-catalog-binding-schema.json` all present and version-pinned in
  the SpecPack.
* FR `event_type` enum reified to v2.2 with every `proto.*` namespace
  from §22.
* Intent Object reified to v1.2 with every `intent.proto.*` class
  from §11.
* Three MCP hubs live in test (`meta_governance_hub`,
  `human_interface_hub`, `digital_twins_hub`); each HA with ≥ 1 replica
  in test, ≥ 3 in production.
* Every base 81 + ADAMPLUS 34 agent has a current AIC, current TCB, and
  current collab profile bound and FR-anchored.
* Every adapter has been re-bound under the current AIC of its consuming
  agents — adapter contract behavior unchanged from `_CONTRACT_SPEC`.
* `adam-mcp-spoke-sdk` published, consumed, and version-pinned across
  every container image.
* `adam-a2a-orchestrator` and `adam-a2a-mesh` running.
* OPA Rego bundle from §28 step 12 deployed and `orch-policy` linting
  green.
* Strict smoke (`wg-fin-txn` + Stripe) green; collaborative smoke
  (`ai-innov-*`) green; OHSHAT trip negative test green; classical
  fallback against PII forbidden test green.
* `qa_suite.py 117+/117+`, `views_smoke.py 70+/70+`, `qa_all 100%`,
  `qa_360 100%`, `qa_pass3..5 100% each`.
* Day-1 PQC posture verified end-to-end: every protocol FR event signed
  Ed25519 + ML-DSA-65; every scope-change event additionally SLH-DSA-anchored.
* Vault rotation runbook tested (90-day rotation, off-cycle rotation,
  emergency revoke, doctrine-version bump rebind).
* OHSHAT kill-switch runbook tested.
* Directors Dashboard v0.3 displays:
  * AIC status per agent (issued / valid / expiring / revoked),
  * Active Conversation Contracts (count, scope, expiry),
  * Hub health (replicas, p99 Pre-Action Gate, refusal rate),
  * Tool catalog version per hub,
  * Sacred Boundary trip rate (target: 0).
* Upgrade entry written to `D:\ADAM\upgrade_log\UPGRADE_LOG.md` (note:
  index update only — no doctrinal self-amendment).

## 30. Doctrine Cross-Refs

| Doctrine artifact                                                                                  | Where this card honors it                                                       |
|----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| `ADAM - Autonomy Doctrine and Architecture Model v0.2.docx`                                        | §1 framing, §3 anchors, §13 collab profile classification                       |
| `ADAM - Support Documents/ADAM - Agent Org Chart v0.3.docx`                                        | §4 hubs, §5 mesh, §13 per-class profile defaults                                |
| `ADAM - Support Documents/ADAM - BOSS Score Formulas v0.3.docx`                                    | §16 floors / ceilings, §14 gate 7                                               |
| `ADAM - Support Documents/ADAM - Intent Object Definition v0.3.docx`                               | §11 protocol class registry; §14 gate 4                                         |
| `ADAM - Support Documents/ADAM - Governance Charter and Human Directorship v0.3.docx`              | §11 director-quorum gates; §17 Sacred Boundaries                                |
| `ADAM - Support Documents/ADAM - OPA Rego Authoring Standards v0.3.docx`                           | §28 step 12; §14 gates 5–7                                                       |
| `ADAM - Security and Quantum at Scale/ADAM - Hardware-Free Cryptographic Substrate v0.3.docx`      | §7.2 PQC posture; §20 recap; software-HSM only                                  |
| `ADAM - Security and Quantum at Scale/ADAM - Quantum and Cryptographic Security at Scale v0.3.docx`| §7.2 algorithm choices; §20 SLH-DSA anchor                                       |
| `ADAM - AGT-Plugin - FULL AGT Implementation v0.3/config/agt-agent-mesh-config.yaml`               | §10 transport, mTLS, IATP, A2A primary protocol                                 |
| `ADAM - AGT-Plugin - FULL AGT Implementation v0.3/schemas/adam-agt-trust-score-schema.json`        | §7.6 IATP authority levels                                                      |
| `Build Cards/ADAM Integration Adapters/_CONTRACT_SPEC.md`                                          | §9 external-MCP-server-contract pattern; §17 sacred boundaries; §18 refusal     |
| `Build Cards/ADAM Agent Definitions/_INDEX.md`                                                     | §3 Day-1 PQC suite; §13 81-agent class breakdown                                |
| `Build Cards/ADAMPLUS Agent Definitions/_INDEX.md`                                                 | §13 ADAMPLUS profile defaults                                                   |
| `deployment/NetStreamX/agents/agent-registry.json`                                                 | §13 canonical agent IDs (`hi-*`, `ga-*`, `orch-*`, `wg-*`, `ai-*`, `twin-*`, `meta-*`) |
| `deployment/NetStreamX/flight_recorder/flight-recorder-schema.json` (v2.1 → v2.2)                  | §22 event catalog; §28 step 2                                                   |
| `deployment/NetStreamX/intent/`                                                                    | §11 protocol class registry; §28 step 3                                         |
| `D:\ADAM\spec_diff\upgrade_plan.json`                                                              | §28 ordered build plan reflects the 9-step canonical upgrade discipline         |

## 31. Acceptance Criteria

This card is **acceptance-clean** when:

1. The 35 sections are present, in order, with no placeholders.
2. Every cross-reference resolves to a file in `D:\ADAM\ADAM Book New\` or
   `D:\ADAM\deployment\NetStreamX\`.
3. Every protocol event in §22 has a one-to-one entry in the §27 QA pass
   coverage and a one-to-one entry in the FR schema v2.2 reification PR.
4. Every collab profile in §13.1 matches the canonical agent registry
   (any drift fails `qa_360`).
5. Every default BOSS floor in §16 is consistent with `boss-config.json`
   tier breakpoints; no internal inconsistency.
6. Every routing matrix row in §12 is exercised by at least one of the 20
   canonical real-world flows.
7. The Day-1 PQC posture in §7.2 / §20 matches the canonical posture
   declared in `Build Cards/ADAM Agent Definitions/_INDEX.md` byte-for-byte.
8. The Build Plan in §28 is ordered such that no step depends on a
   downstream step (DAG-clean).
9. The DoD in §29 references concrete production artifacts (no stubs, no
   mocks, no "if/when" language).
10. The card refuses doctrine self-amendment in every example, every
    flow, every FR event, every gate (verified by reading every `if`
    block in §8.7, §10.4, §10.5, §14, §17, §18).

## 32. Worked Examples (concrete, build-ready)

### 32.1 Strict-agentic-flow: vendor invoice → 3-way match → payment run

```
[adamplus-ap-vendor-invoice] (collab=strict) bound TCB allows: invoice.ingest.
   ── MCP/tools/call name="adapter.coupa.invoice.fetch" args={po_id, vendor_id}
   ── MCP hub: human_interface_hub
   ── Pre-Action Gate: BOSS=18 (MODERATE), tier OK; data_classes=[internal]; egress=api.coupa.com:443
   ── Action OK; FR proto.tool.adapter.coupa.invoice.fetch.action.ok

[adamplus-ap-3way-match] (collab=strict)
   ── MCP/tools/call name="adapter.sap-s4hana.po.read" args={po_id}
   ── Pre-Action Gate: ok; FR proto.tool.adapter.sap-s4hana.po.read.action.ok
   ── MCP/tools/call name="adapter.sap-s4hana.grn.read" args={po_id}
   ── BOSS includes financial_exposure=42 (ELEVATED). 3-way match passes; emits intent.action.payment.schedule.

[adamplus-ap-payment-run] (collab=strict)
   ── Intent Object: intent.action.payment.schedule (governor concurrence: ga-financial)
   ── BOSS pre: composite=58 (HIGH); director SLA 4h applies if amount >> per-txn cap.
   ── If under cap: MCP/tools/call name="adapter.stripe.bill.payable.pay" args={...} idempotency_key=<uuidv7>
   ── Pre-Action Gate: BOSS pass (composite 58, tier HIGH, tool tier ceiling HIGH); egress api.stripe.com:443; PAN forbidden.
   ── Action OK; FR proto.tool.adapter.stripe.bill.payable.pay.action.ok with dual-sign.
   ── Compensating tool: adapter.stripe.bill.payable.cancel (registered for saga rollback).

[At any point a Sacred Boundary trip (PAN, region-lock, takedown override) refuses + OHSHAT.]

[A2A is forbidden across this entire flow. Any attempt: refuse, FR proto.a2a.refused reason=collab.profile.violation.]
```

### 32.2 Collaborative-flow: innovation experiment → rollout proposal

```
[orch-policy] opens Conversation Contract:
  conversation_id: conv-innovation-2026-05-06-a, allowed_dids:
    [did:adam:ai-innov-experiment, did:adam:ai-innov-rollout, did:adam:ai-innov-results,
     did:adam:wg-ops-innovation, did:adam:ai-strategy-scenario]
  scope_purpose: "innovation.experiment.evaluation"
  boss_score_floor: 30, boss_score_ceiling: 50
  allowed_payload_schemas: [innovation.proposal.v1, innovation.objection.v1, innovation.evidence.v1]
  forbidden_topics: [pii, phi, raw_pan, directors_personal_data]
  max_messages_per_minute: 60, max_total_messages: 1000
  convergence_required: true, target_class: intent.action.innovation.proposal

[ai-innov-experiment] sends A2A "innovation.proposal.v1" to all-allowed broadcast.
   Pre-Send Gate: collab=collaborative; BOSS pre=22 (MODERATE) within ceiling; payload schema OK; sign.
   FR proto.a2a.send.ok. Receivers verify per Pre-Receive Gate.

[ai-strategy-scenario] sends A2A "innovation.objection.v1" with twin-economic divergence ref.
   FR proto.a2a.send.ok.

[ai-innov-results] sends A2A "innovation.evidence.v1" with model-eval results.
   FR proto.a2a.send.ok.

[Conversation closes (convergence reached or expiry).
 Participants emit "a2a.convergence.proposal" containing the converged Intent Object body.
 orch-policy verifies all participant sigs + class match + BOSS within bounds.
 SLH-DSA anchor on close. proto.a2a.convergence.proposed.]

[hi-intent] receives the converged Intent Object → six-stage pipeline →
  governor concurrence (ga-operations + ga-security) → BOSS score → orch-policy authorize →
  MCP/tools/call name="ai.model.rollout.canary" hub=meta_governance_hub args={model_id, canary_pct}

[FR records every step with dual sign; meta-audit verifies the trail; conversation closed.]
```

### 32.3 Mixed-flow: legal-hold-driven content takedown

```
[Workgroup A2A among wg-legal-contract, wg-data-rights, wg-legal-jurisdiction]
   under conv-legal-takedown-<id>. Conversation reaches convergence on Intent
   intent.action.netstreamx.takedown {asset_id, jurisdiction, legal_basis}.

[BOSS pre-eval after convergence: regulatory_impact=72 (HIGH), reputational_risk=58 (HIGH)
  → composite (with weights) ≈ 64. Critical-dim override would NOT trigger here.
  But: takedown is a privileged-tier MCP tool → director quorum required.]

[Director Action: Legal Director (Michael Lamb proxy) approves; CISO concurs;
 director_proxy_acting events emitted per seat.]

[orch-policy authorizes; MCP/tools/call name="adapter.netstreamx-cms.asset.takedown" args={asset_id} idempotency_key=<uuidv7>.
 Pre-Action Gate: privileged tier; BOSS within ceiling; Sacred Boundary intentionally invoked
 (the boundary IS the takedown reason, not a refusal cause); FR action_ok with SLH-DSA anchor.]

[orch-evidence anchors the trail; meta-audit verifies; conversation closed.]
```

## 33. Why this card is "bulletproof secure" (the explicit threat-model walkthrough)

This card eliminates the canonical agentic threat surfaces the OWASP
Agentic AA01–AA10 series enumerates and that ADAM's BOSS Security
dimension is anchored to. Section by section:

| Threat                                                                     | Where this card mitigates                                                                      |
|----------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Identity spoofing** (impersonation of a trusted agent)                   | §7 AIC dual-sig + quad-sig issuance + IATP decay (silent compromise eventually loses authority) |
| **Privilege escalation via tool catalog**                                  | §15 TCB binding + §11 promote requires Domain Governor + meta-stability BOSS sim                |
| **Doctrine self-amendment**                                                | §14 gate 5 + §28 step 12 OPA bundle + §17 Sacred Boundary trip                                  |
| **Off-record sidechannel between agents**                                  | §5 A2A is on-bus only; off-record sockets violate RGI-04 and are detected by `meta-audit`       |
| **Replay attack on a captured signed message**                             | §10.2 / §8.2 replay marker + §10.4 / §8.7 replay window + idempotency journal                   |
| **Long-horizon classical key compromise**                                  | §7.2 hybrid Ed25519 + ML-DSA-65 + SLH-DSA anchor                                                |
| **Long-horizon lattice key compromise**                                    | §7.2 SLH-DSA hash-based long-term anchor + §22 anchor on every scope-change event              |
| **Vault key exfiltration**                                                 | §7.7 software-HSM keeps private material wrapped under ML-KEM-1024 master key                   |
| **Tool-confused-deputy** (agent calls a tool it's not supposed to)         | §15 TCB + §14 gate 3 (catalog binding) + §14 gate 7 (BOSS tier ceiling)                         |
| **Collaboration-as-bypass** (use A2A to coordinate around a strict gate)   | §13.2 non-bypass invariant + §10.4 collab.profile.violation + §17 Sacred Boundary               |
| **PII / PHI / PAN data-class leakage**                                     | §15 forbidden_data_classes + §17 Sacred Boundary + §16 floor 82 for PII tools                   |
| **Egress to unsanctioned destination**                                     | §7.1 AIC.scope.egress_allowlist mirrored as seccomp/CNI; §14 gate 8                             |
| **Rate exhaustion / DoS by misbehaving agent**                             | §15 rate_per_min + §10.3 Conversation Contract caps + §14 gate 7 BOSS                           |
| **Hub takeover**                                                           | §8.8 HA replicas + OPA-bundle determinism + §11 hub.suspend requires director quorum            |
| **Cross-tenant / cross-residency leakage**                                 | §9 contract.residency + §15 TCB residency match + §17 Sacred Boundary                           |
| **Model-prompt injection** (user-controlled text reaches a tool arg)       | §8.4 strict JSON-Schema + §14 gate 4 Intent linkage + Director console drives privileged tools  |
| **Saga half-execution**                                                    | §21 saga compensation registered per tool; §18 receiver-disconnected → retry per CC; OHSHAT path|
| **Sacred Boundary attempted normalization**                                | §17 SLH-DSA anchor on every trip; OHSHAT broadcast; full director quorum required to lift       |

## 34. Open Questions / Director-Decision Hooks

This card is build-ready; nevertheless, the following are explicit hooks
where Michael (or the future production director quorum) should weigh in
before the Build Plan is executed end-to-end:

1. **Hub HA replica counts in production** — defaults are 5/5/3; a
   per-Domain breakdown driven by DNA may be warranted at scale.
2. **External-MCP-server allowlist for Day-1** — the canonical default in
   §25 includes Azure AI Foundry and Anthropic MCP marketplace at
   read/low tier with PII forbidden. Director quorum should explicitly
   accept or modify this list before Step 11 of the Build Plan.
3. **Conversation Contract default ceiling** — 50 (ELEVATED). May want
   to lower to 30 (MODERATE) for ethics-bias / fairness conversations
   where the bar should be tighter.
4. **AIC rotation period** — 90 d default; CISO may want 60 d for
   `wg-sec-vault`-issued AICs and 30 d for AICs that hold privileged-tier
   tools.
5. **Agent Lightning A2A inclusion** — `proto.a2a.*` events generated by
   RL-bound agents are currently held to BOSS ≤ 30 ceiling per the RL
   governance bound. If RL is ever enabled in production, the
   Conversation Contract template must be tightened further.
6. **Classical-fallback exposure budget** — `qsuite=classical-fallback`
   on a non-PII tool is acceptable Day-1; on a PII/PCI/PHI tool it is a
   Sacred Boundary. The full `qsuite` exposure report should be a daily
   line item in the Directors Dashboard.

These do **not** block the Build Plan; they are explicit invitations to
the director quorum to set policy bands before Step 11 onwards.

## 35. Closing posture

This card is the Day-1 **baseline layer** of ADAM. It sits at the same
foundational tier as BOSS Score v3.2, the Flight Recorder, the
Authorization Vault, and the 5+2 Director Constitution. It is not a
feature, not a plug-in, and not optional. Every agent in the 81-mesh,
the 34 ADAMPLUS extension, and the 20 adapters operates against this
card from boot. Every action ADAM takes — collaborative or strict,
internal or external, routine or director-quorum-approved — is bound by
the gates, identities, contracts, and FR events this card defines.

It is doctrine-binding, RGI-compliant, BOSS-bound, PQC-day-1,
vault-anchored, FR-replayable, sacred-boundary-fenced, and no-bypass on
collaboration. Every agent is reachable through a single contract
pattern (AIC + TCB + Conversation Contract + external-MCP-server-contract).

If a future protocol arrives (e.g., a successor to MCP, a new direct
agent-to-agent peer protocol), it joins ADAM through a sibling card under
`Build Cards/ADAM Protocols/`. The non-negotiables — chain append-only,
doctrine never self-amends, software-HSM only, ADAM Book New wins on
contention, Day-1 PQC, no blockchain — apply identically. ADAM's
governance does not relax for new wire-protocols. New wire-protocols
relax to fit ADAM's governance, or they do not bind.

<!-- end of card -->

