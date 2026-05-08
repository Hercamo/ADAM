# ADAM External-Adapter-Contract Spec (v0.3, Day-1 PQC)

**Card ID:** `_CONTRACT_SPEC`
**Version:** v0.3 (canonical contract-binding pattern for all 20 integration adapters)
**Status:** build-ready, advanced-AI-feed
**Doctrine binding:** ADAM Book New v0.3 — RGI 5-domain contract model + Flight Recorder + Intent Object + BOSS Score + Day-1 PQC
**Supersedes:** none (new card; the per-adapter v0.2 originals remain alongside as `.docx.BAK` old-version backups)
**Used By:** every card in `ADAM Integration Adapters/` (`adapter-*.md` v0.3)
**Forward-looking SpecPack extensions (tracked in §14 Build Plan):**

* extends FR `event_type` enum (schema v2.1) with the dotted `adapter.contract.*` and `adapter.<name>.*` namespaces enumerated in §11 — to be reified into FR schema v2.2 before code lands;
* extends Intent Object schema v1.1 with a `class` field whose initial registry is the seven classes enumerated in §7;
* extends FR `cryptographic_proof` (schema v2.1 permits one signature) to persist the second of the dual signatures in `tamper_evident.attestations[]` — to be normalised in FR schema v2.2.

These extensions are forward-looking: the cards are authored so that as soon as the SpecPack reifies them, the harness validates clean. Until then, the dual-signature, dotted-event, and Intent-class behaviours are described as conventions, with reified-schema names listed in §14.

---

## 1. Purpose

This card is the canonical specification for the **External-Adapter-Contract** that every ADAM integration adapter must bind to before performing any action. It exists so that adapter cards can reference one source of truth for the contract pattern instead of restating it 20 times.

An adapter without a bound, currently-valid contract is **inert**: it MUST refuse to translate, emit, ingest, or call. Refusal is logged to Flight Recorder as an `adapter.contract.absent` event and surfaced to the Exception Orchestrator. There are no exceptions, including for healthchecks, demos, or break-glass.

## 2. The Contract Object

The contract is a JSON document, schema-versioned, hash-chained into the Flight Recorder, and dual-signed (Ed25519 + ML-DSA-65). It is the only authority that grants an adapter the right to act.

### 2.1 Contract Schema (canonical)

```json
{
  "contract_id": "adapter-<name>-contract",
  "contract_version": "<semver>",
  "schema_version": "adam-contract-v1",
  "adapter_card_id": "adapter-<name>",
  "adapter_card_version": "<semver>",
  "doctrine_version": "adam-book-new@v0.3",
  "issued_at": "<RFC3339>",
  "issued_by": {
    "agent_id": "ga-security",
    "co_signers": ["ga-legal", "ga-financial", "orch-policy"]
  },
  "valid_from": "<RFC3339>",
  "valid_until": "<RFC3339|null>",
  "external_system": {
    "name": "<vendor system name>",
    "endpoint_class": "saas|onprem|hybrid|protocol",
    "residency": ["<region>", ...],
    "tenant_ids": ["<tenant>"]
  },
  "identity": {
    "vault_key_handle": "wg-sec-vault://<handle>",
    "rotation_policy": "<cron>",
    "quantum_lock": "ml-kem-1024+ml-dsa-65"
  },
  "allowed_actions": [
    {
      "action": "<canonical adapter verb>",
      "direction": "inbound|outbound|bidirectional",
      "rate_ceiling_per_min": <int>,
      "data_classes": ["<class>", ...],
      "preconditions": ["<predicate>", ...]
    }
  ],
  "forbidden_actions": ["<canonical adapter verb>", ...],
  "data_classes_allowed": ["pii", "phi", "pci", "public", "internal", "restricted"],
  "data_classes_forbidden": [...],
  "egress_allowlist": ["<fqdn:port>", ...],
  "ingress_allowlist": ["<fqdn:cidr>", ...],
  "boss_score_floor": 72,
  "fr_event_namespace": "adapter.<name>.*",
  "intent_object_required_for": [
    "schema_evolution", "scope_expansion", "credential_rotation_off_cycle",
    "rate_ceiling_increase", "new_action_class", "residency_change",
    "termination", "suspension"
  ],
  "rfm_chain_anchor": "<FR event hash>",
  "signatures": {
    "ed25519": "<base64>",
    "ml_dsa_65": "<base64>"
  },
  "fr_anchor_hash": "<sha3-512 of preceding FR head>"
}
```

### 2.2 Storage and Retrieval

Contracts live as immutable rows in the Flight Recorder under topic `adapter.contract.bound`. The current contract for an adapter is the head of its `contract_id` chain that has not been superseded by an `adapter.contract.terminated` or `adapter.contract.suspended` event. Adapters MUST resolve the head on every cold start and MUST re-validate at least every 60 s during runtime.

## 3. Binding Lifecycle

```
DRAFT → CO-SIGNED → BOUND → ACTIVE → (SUSPENDED) → (RFM-PENDING) →
   (AMENDED) → (RENEWED) → TERMINATED → ARCHIVED
```

| State        | Adapter Posture                                         | FR Event                          |
|--------------|---------------------------------------------------------|-----------------------------------|
| DRAFT        | inert                                                   | `adapter.contract.draft`          |
| CO-SIGNED    | inert; awaiting BOUND                                   | `adapter.contract.cosigned`       |
| BOUND        | inert; awaiting `valid_from`                            | `adapter.contract.bound`          |
| ACTIVE       | actions allowed within `allowed_actions`                | `adapter.contract.activated`      |
| SUSPENDED    | inert; queued events held in DLQ                        | `adapter.contract.suspended`      |
| RFM-PENDING  | actions allowed under prior contract; no scope changes  | `adapter.contract.rfm_pending`    |
| AMENDED      | new contract version supersedes prior                   | `adapter.contract.amended`        |
| RENEWED      | identical scope, new validity window                    | `adapter.contract.renewed`        |
| TERMINATED   | inert; credentials rotated and revoked at vault         | `adapter.contract.terminated`     |
| ARCHIVED     | retained read-only for evidence                         | `adapter.contract.archived`       |

## 4. Binding at Adapter Init

Every adapter implementation MUST follow this exact init sequence and MUST NOT emit, ingest, or call the external system between steps 0 and 5:

0. Boot. Load card-id, card-version, vault-handle, FR client.
1. **Resolve contract head.** Query FR for `adapter.contract.bound` matching `contract_id = "adapter-<name>-contract"` whose chain head is not `terminated|suspended|archived`.
2. **Verify dual signature.** Validate Ed25519 and ML-DSA-65 against `ga-security` signer set. Validate `fr_anchor_hash` chains correctly into FR head at issuance time.
3. **Verify card binding.** `contract.adapter_card_id == self.card_id` and `contract.adapter_card_version == self.card_version`. If card was upgraded without a contract amendment, refuse to start.
4. **Verify quantum lock.** Pull `vault_key_handle` from `wg-sec-vault`; assert key wrapping is ML-KEM-1024 and signing key is ML-DSA-65. If not, refuse.
5. **Emit `adapter.contract.activated`** with hash chain anchor. Adapter is now ACTIVE.

If any step fails: emit `adapter.contract.bind_failed`, halt, and notify `orch-exception`. Do not retry without a fresh intent object.

## 5. Per-Action Enforcement

Every adapter action — inbound translation, outbound call, schema migration, healthcheck — MUST pass the **Pre-Action Gate**:

```
preAction(actionRequest):
    if contract.state != ACTIVE and not (RFM-PENDING and actionRequest in prior_scope):
        emit("adapter.contract.refused", reason="not-active"); deny.
    if actionRequest.verb not in contract.allowed_actions:
        emit("adapter.contract.refused", reason="verb-not-allowed"); deny.
    if actionRequest.verb in contract.forbidden_actions:
        emit("adapter.contract.refused", reason="verb-forbidden"); deny.
    if actionRequest.data_classes - contract.data_classes_allowed != ∅:
        emit("adapter.contract.refused", reason="data-class-violation"); deny.
    if rate_window_count(verb) >= contract.rate_ceiling_per_min:
        emit("adapter.contract.refused", reason="rate-ceiling"); deny.
    if egress_target not in contract.egress_allowlist:
        emit("adapter.contract.refused", reason="egress-violation"); deny.
    if boss_score(actionRequest) < contract.boss_score_floor:
        emit("adapter.contract.refused", reason="boss-floor"); deny.
    record fr.preaction.ok; allow.
```

The Pre-Action Gate is **synchronous and in-process** within the adapter — it cannot be skipped by a network or sidecar failure, because the adapter holds the only key handle that can produce a valid outbound signature, and that handle is gated by the gate.

## 6. Request-for-Modification (RFM) Flow

Any change to an adapter's surface — new verb, scope expansion, residency change, rate ceiling lift, off-cycle credential rotation, schema evolution, suspension, or termination — requires an RFM. Adapters cannot self-amend.

### 6.1 RFM Sequence

1. **Trigger.** Any agent (including the adapter itself, observing schema drift) may file an RFM by emitting `adapter.contract.rfm_requested` with: requesting agent, justification, requested delta (JSON-Patch over current contract), supporting evidence hashes.
2. **Intent Object created.** The Intent Interpretation Agent (`hi-intent`) receives the RFM and creates an Intent Object of class `intent.adapter.contract.amend` (see §7).
3. **Governor review.** The Intent Object is routed to `ga-security`, plus `ga-legal` and/or `ga-financial` and/or `ga-market` based on data classes touched. Each governor either co-signs, requests changes, or refuses.
4. **BOSS calibration.** `meta-stability` runs the proposed contract through BOSS Score simulation; if the proposed `boss_score_floor` would gate the adapter below project floor, the RFM is refused.
5. **Doctrinal check.** `meta-integrity` verifies the proposed delta does not conflict with ADAM Book New v0.3 doctrine. Doctrine never self-amends; if the RFM would require doctrinal change, the RFM is refused regardless of governor consent.
6. **Co-sign and bind.** If all governors co-sign, a new contract version is minted, dual-signed, and FR-anchored. The adapter receives `adapter.contract.amended`, atomically swaps to the new contract head, and emits `adapter.contract.activated@<new_version>`.
7. **Evidence chain.** The Intent Object retains pointers to: original RFM event, all co-signatures, BOSS sim result, doctrine check, prior contract head, new contract head. Chain is append-only.

### 6.2 Refusal Posture

If any step refuses, the RFM is closed with `adapter.contract.rfm_refused`. The adapter remains on the prior contract. The refusing agent's reason is written into the Intent Object for audit.

### 6.3 Time Bounds

RFMs expire if not co-signed within 14 days. Expired RFMs require a fresh Intent Object.

## 7. Intent Object Linkage

Every contract event produces or consumes an Intent Object. The Intent Object is the durable, queryable, governor-visible record that ties the contract change to its motivation, evidence, and approvers.

| Contract Event              | Intent Object Class                  | Required Approvers                |
|-----------------------------|--------------------------------------|-----------------------------------|
| Initial bind                | `intent.adapter.contract.bind`       | ga-security, ga-legal, orch-policy|
| Amend (scope/rate/residency)| `intent.adapter.contract.amend`      | ga-security + scope-relevant gov  |
| Renew (same scope)          | `intent.adapter.contract.renew`      | ga-security                        |
| Suspend                     | `intent.adapter.contract.suspend`    | ga-security or orch-exception     |
| Terminate                   | `intent.adapter.contract.terminate`  | ga-security + ga-legal            |
| Off-cycle key rotation      | `intent.adapter.contract.rotate`     | ga-security + wg-sec-vault        |
| Emergency revoke            | `intent.adapter.contract.revoke`     | ga-security (single-party allowed)|

Intent Objects MUST reference the prior FR head hash, the proposed contract diff, the BOSS Score simulation result, and the doctrine-check verdict. Adapters MUST NOT act on a contract change that lacks a fully populated Intent Object.

## 8. Smart-Adapter Behaviors

The adapter is "smart" only to the degree required to honor the contract. Specifically, every adapter MUST implement:

1. **Self-introspection.** Expose the bound contract head, current state, last RFM, and current `boss_score_floor` over the ADAM bus topic `adapter.<name>.contract.head`.
2. **Schema-drift detection.** Continuously compare external system schemas (where vendor APIs expose them) against the contract's allowed schema mappings. On drift, file an RFM automatically; do not silently reshape.
3. **Rate self-throttling.** Track per-verb rate windows in-process; never rely on external system 429s alone.
4. **Egress fencing.** Refuse any outbound socket whose `host:port` is not in `egress_allowlist`. Bind syscalls to seccomp/CNI policy that mirrors the allowlist; do not trust DNS.
5. **Inbound signature recording.** For inbound payloads, record the source signature posture (`unsigned`, `single-ed25519`, `dual-pqc`, `mtls-only`, `webhook-hmac-sha256`) on every emitted bus event, even if the payload is single-signed.
6. **Dual-signature on emission.** Every event emitted onto the ADAM bus is dual-signed Ed25519 + ML-DSA-65 using the vault key handle. No exceptions.
7. **Refusal recording.** Every refusal increments per-reason counters and emits an `adapter.contract.refused` event; refusal is a first-class behavior, not an error.
8. **Replay-safe restart.** On crash and restart, the adapter MUST reconcile its idempotency journal against FR before resuming any outbound call.
9. **Heartbeat with contract attestation.** Heartbeat events carry the current contract head hash so monitors can detect silent contract divergence.
10. **No latent state.** The adapter holds no durable state outside FR + vault + idempotency journal; it must be safe to destroy and respawn at any time.

## 9. Quantum Posture (Day-1 PQC)

Canonical Day-1 PQC suite (per `Build Cards\ADAM Agent Definitions\_INDEX.md`): **Ed25519 + ML-DSA-65 + ML-KEM-768; SLH-DSA long-term anchor.**

* All adapter→bus signatures: hybrid Ed25519 + ML-DSA-65 (NIST FIPS 204).
* All adapter→external mTLS: prefer hybrid X25519+ML-KEM-768 (NIST FIPS 203) where the external peer supports it; fall back to classical X25519 with the fallback recorded on every emitted event as `qsuite=classical-fallback`.
* Vault key wrap: ML-KEM-1024 (longer-strength variant for at-rest key encapsulation).
* **Long-term anchor**: every contract head and every chain-rolling FR snapshot is additionally signed with **SLH-DSA** (NIST FIPS 205) and stored in `tamper_evident.attestations[]`. SLH-DSA is hash-based and assumed durable against a far-horizon cryptanalytic break of lattice schemes; it is the doctrine's deepest line of defence.
* Inbound signature posture is recorded but never used to gate (we cannot force the outside world).
* Contract objects themselves are dual-signed at issuance (Ed25519 + ML-DSA-65) and SLH-DSA-anchored at termination/archival; verification on bind requires both per-event signatures, plus the SLH-DSA anchor when the contract is re-validated post-archive.

## 10. Refusal Posture Matrix

| Condition                                         | Adapter Behavior                                |
|---------------------------------------------------|-------------------------------------------------|
| No bound contract                                 | inert; refuse all; emit `contract.absent`       |
| Bound but not yet `valid_from`                    | inert; refuse all; emit `contract.pending`      |
| ACTIVE, action in `allowed_actions`               | execute; emit normal event                      |
| ACTIVE, action not in `allowed_actions`           | refuse; emit `contract.refused.verb`            |
| RFM-PENDING, action in prior scope                | execute; flag event `under_rfm=true`            |
| RFM-PENDING, action outside prior scope           | refuse; emit `contract.refused.rfm_scope`       |
| SUSPENDED                                         | inert; queue inbound to DLQ; refuse outbound    |
| TERMINATED                                        | inert; reject all; rotate vault keys            |
| Vault key revoked                                 | inert; refuse all; emit `contract.key_revoked`  |
| Doctrine version mismatch                         | inert; refuse all; emit `contract.doctrine_mismatch` |

## 11. FR Event Catalog (Common to All Adapters)

```
adapter.contract.draft
adapter.contract.cosigned
adapter.contract.bound
adapter.contract.activated
adapter.contract.suspended
adapter.contract.rfm_requested
adapter.contract.rfm_pending
adapter.contract.rfm_refused
adapter.contract.amended
adapter.contract.renewed
adapter.contract.terminated
adapter.contract.archived
adapter.contract.refused           (with reason taxonomy)
adapter.contract.absent
adapter.contract.bind_failed
adapter.contract.key_revoked
adapter.contract.doctrine_mismatch
adapter.contract.heartbeat
adapter.contract.head
```

Per-adapter cards MAY add domain-specific FR events under `adapter.<name>.*` but MUST NOT redefine the events above.

## 12. 360 QA Coverage (Pass 1–5)

Every adapter card v0.3 MUST be exercised by the build-card harness across five passes. The contract test set is shared across all 20 adapters and lives in the QA harness location recorded in project memory.

| Pass | Focus                                  | Adapter-Specific Tests                         |
|------|----------------------------------------|------------------------------------------------|
| 1    | Schema parity (card ↔ doctrine)        | section completeness, ordering                 |
| 2    | Capability matrix                      | inbound + outbound verbs vs `allowed_actions`  |
| 3    | Contract lifecycle                     | DRAFT→ACTIVE→AMENDED→TERMINATED                |
| 4    | Refusal posture                        | every row of the §10 matrix                    |
| 5    | RFM + Intent Object roundtrip          | scope expansion, residency change, revoke     |

DoD: 100/100 on `qa_all`, 100/100 on `qa_360`, 100/100 on each of `qa_pass3..5`, plus a clean run of `views_smoke` confirming every contract event renders correctly in the Directors Dashboard and FR Lifecycle view.

## 13. Cross-Reference

* **RGI 5-domain model** (canonical IDs and names, source: `D:\ADAM\ADAM Book New\ADAM - AGT-Plugin - FULL AGT Implementation v0.3\README.md`):

  | RGI ID  | Domain                  | How this contract honours it                                                  |
  |---------|-------------------------|-------------------------------------------------------------------------------|
  | RGI-01  | Policy Enforcement      | Pre-Action Gate (§5) refuses any verb / data-class / egress / rate breach     |
  | RGI-02  | Agent Identity          | Vault-handle binding (§2.1 `identity`) + permission attestation (§8.1)        |
  | RGI-03  | Execution Containment   | Egress allowlist + seccomp/CNI fence (§8.4); inert when contract not bound    |
  | RGI-04  | Telemetry Emission      | Dual-signed FR events (§11) carry contract head hash on every emission        |
  | RGI-05  | Tool/Plugin Governance  | Adapter is a "plugin" of ADAM; can never govern, only translate (§1, §8.10)   |

* Flight Recorder schema: `flight-recorder-schema.json` (`$id: https://adam.io/schemas/flight-recorder/v2.1`) in v0.3 SpecPack `schemas/`.
* Intent Object schema: `intent-object-schema.json` (`$id: https://adam.io/schemas/intent-object/v1.1`) in v0.3 SpecPack `schemas/`.
* BOSS Score: `boss-score-schema.json` and `boss-config.json` in v0.3 SpecPack; canonical numeric range **0..100**; routing tiers `soap | moderate | elevated | high | ohshat`. The `meta-stability` agent card is the runtime owner.
* Doctrinal Drift Sentinel: `meta-integrity` agent card.
* Vault: `wg-sec-vault` agent card; URI scheme `wg-sec-vault://<handle>` is the only way an adapter holds key material.
* Day-1 PQC suite: `Ed25519 + ML-DSA-65 + ML-KEM-768; SLH-DSA long-term anchor` (per `Build Cards\ADAM Agent Definitions\_INDEX.md` header). NIST FIPS 203 (ML-KEM), 204 (ML-DSA), 205 (SLH-DSA).

## 14. Build Plan (for the contract pattern itself)

1. Reify §2.1 schema as `external-adapter-contract-schema.json` under v0.3 SpecPack `schemas/`.
2. Implement Pre-Action Gate as a shared library `adam-adapter-contract-sdk` consumed by every adapter image.
3. Add `adapter.contract.*` topics to FR topic registry.
4. Add Intent Object classes from §7 to the Intent Object class registry.
5. Wire RFM flow into `hi-intent` and `orch-policy`.
6. Smoke-test the full lifecycle on `adapter-stripe` first; replicate to remaining 19.
7. Run `qa_all`, `qa_360`, `qa_pass3..5`; fix to green.

## 15. Definition of Done

* All 20 adapter cards v0.3 reference this card by ID.
* `external-adapter-contract-schema.json` is checked into the SpecPack and version-pinned.
* FR topic registry includes every event in §11.
* `adam-adapter-contract-sdk` is published and consumed by all 20 adapter images.
* Contract lifecycle smoke test passes on a representative adapter (Stripe).
* Directors Dashboard shows the Contract State for every adapter.
* `qa_all` 100/100; `views_smoke` 70/70; `qa_pass3..5` 100/100 each.
* Upgrade entry written to `D:\ADAM\upgrade_log\UPGRADE_LOG.md` (note: index update only — no doctrinal self-amendment).
