# HL7 v2 + FHIR R4/R5 Adapter (v0.3, Contract-Bound, Day-1 PQC)

**Card ID:** `adapter-hl7-fhir`
**Version:** v0.3 (contract-bound)
**Status:** build-ready
**Supersedes:** `adapter-hl7-fhir__HL7_v2_+_FHIR_R4-R5_Adapter.docx.BAK` (v0.2 — retained as old version)
**Contract pattern:** `_CONTRACT_SPEC.md`
**Used By:** healthcare deployments; `wg-data-pii`, `wg-legal-compliance`, `wg-data-residency`, `adamplus-ops-ehr`, `ai-external-stakeholder`

---

## 1. Target System

HL7 v2.x (MLLP/SMTP/file) and FHIR R4 + R5 (REST + Bulk Data + Subscriptions). Production scope: ADT (admit/discharge/transfer), ORU (observations/results), ORM (orders), DFT (charge), SIU (scheduling) for HL7 v2; Patient, Encounter, Observation, Procedure, MedicationRequest, Appointment, DocumentReference, Coverage, Claim for FHIR. SMART-on-FHIR support for app-launch flows.

## 2. Inbound + Outbound Capabilities

**Outbound:** FHIR `create`/`update`/`patch`/`search`/`$everything`; FHIR Bulk Export pull; HL7 v2 send via MLLP with ACK/NACK; transactional Bundle.

**Inbound:** MLLP listener with low-level acknowledgments; FHIR Subscription receiver (REST hooks or `$subscription-events`); SMART-on-FHIR launch handler; Bulk Data $export pull-and-emit.

## 3. Auth + Identity

OAuth 2.0 SMART-on-FHIR with backend-services profile (asymmetric JWT signed with EC P-384) for system-to-system, vaulted at `wg-sec-vault://fhir/<endpoint>/jwt-signer`. mTLS with peer certificate pinning. MLLP encapsulated in TLS only — never plain TCP; mTLS to all v2 peers. Quantum lock: ML-KEM-1024 wrap, ML-DSA-65 dual-sign on bus.

## 4. Schema Mapping

| FHIR / v2 Resource     | ADAM Canonical                     |
|------------------------|------------------------------------|
| `Patient` / ADT-PID    | `health.patient` (PHI)             |
| `Encounter` / ADT-PV1  | `health.encounter`                 |
| `Observation` / ORU-OBX| `health.observation`               |
| `Procedure`            | `health.procedure`                 |
| `MedicationRequest` / ORM | `health.med_request`            |
| `Appointment` / SIU    | `health.appointment`               |
| `Coverage`             | `health.coverage`                  |
| `Claim`                | `health.claim`                     |
| `DocumentReference`    | `health.document_reference`        |

## 5. Idempotency

* FHIR: `If-None-Exist` for conditional create; `If-Match` ETag for update; idempotency key in `meta.tag` recorded in FR.
* HL7 v2: MSH-10 message control id; ACK reconciled into FR; duplicates per (MSH-3, MSH-4, MSH-10) 7-day window.

## 6. Rate Limits

Per-endpoint contract ceilings; bulk export staggered. MLLP listener with backpressure to upstream HIS via NACK (AR — application reject) when overloaded.

## 7. Error Handling

FHIR `OperationOutcome` mapped by `severity`/`code`. v2 ACK NACK codes (AA/AE/AR) routed canonical. PHI-bearing errors NEVER include resource bodies in events — only resource type + id.

## 8. Residency

PHI residency is regulated (HIPAA/HHS, GDPR, country-specific). Contract pins jurisdiction(s); cross-jurisdiction routing strictly forbidden. PHI is mandatory in `data_classes_allowed` only when contract addendum cosigned by `ga-legal` + `ga-security`.

## 9. FR Events

```
adapter.fhir.create.ok / .failed
adapter.fhir.update.ok
adapter.fhir.patch.ok
adapter.fhir.bulk.export.requested / .ready / .ingested
adapter.fhir.subscription.notification.received
adapter.hl7v2.message.sent / .ack / .nack
adapter.hl7v2.message.received
adapter.hl7v2.duplicate.detected
adapter.fhir.smart.launch.received
adapter.fhir.schema.drift.detected
adapter.hl7.rate.pressure
```

## 10. Configuration Schema

```yaml
adapter_hl7_fhir:
  fhir:
    base_url: "https://fhir.<provider>.org/r4"
    version: "R4"   # R4 | R5
    smart_backend_jwks: "wg-sec-vault://fhir/<endpoint>/jwks"
  v2:
    listener_addr: "0.0.0.0:2575"
    peers:
      - { name: "lab-1", host: "lab1.<provider>.local", port: 6661, mtls: true }
  vault_handle: "wg-sec-vault://fhir/<endpoint>/jwt-signer"
  contract_id: "adapter-hl7-fhir-contract"
```

## 11. Schemas Spoken

FHIR R4 + R5 (JSON + XML), HL7 v2.5/2.6/2.8 (MLLP), SMART-on-FHIR (backend services + EHR launch), CDA (read for DocumentReference), FHIR Bulk Data NDJSON.

## 12. Day-1 PQC Posture

Bus: hybrid Ed25519 + ML-DSA-65. FHIR/MLLP TLS: hybrid X25519 + ML-KEM-768 where peer supports it (rare); else classical with `qsuite=classical-fallback`. Vault wrap ML-KEM-1024. Auto-RFM as PQC TLS profiles emerge in HL7/FHIR connectathons.

## 13. Resource Profile

CPU 2 / 6 burst, RAM 2 GB / 8 burst (bulk export), Disk 100 GB (NDJSON staging), Net ≤500 Mbps.

## 14. Dependencies

`wg-sec-vault`, FR, `hi-intent`, `orch-policy`, `meta-stability`, `meta-integrity`, `wg-data-pii`, `wg-data-residency`, `wg-legal-compliance`, `adam-adapter-contract-sdk`.

## 15. SLOs

FHIR write p95 ≤ 1.0 s; MLLP ACK p95 ≤ 100 ms; bulk ingest p95 ≤ 30 s/GB; availability ≥ 99.95%; refusal p99 ≤ 30 ms.

## 16. Build Plan

1. Pre-Action Gate via SDK.
2. SMART backend-services JWT signer with vault key.
3. FHIR client with conditional-create + ETag.
4. Bulk Data $export client with staged NDJSON.
5. MLLP listener (TLS-only) with peer cert pinning.
6. Subscription receiver and reconciler.
7. PHI-stripping event emitter (never embed PHI in events).
8. QA pass1..5 + 360.

## 17. Definition of Done

`qa_all` / `qa_360` / `qa_pass3..5` 100/100; contract lifecycle green; PHI-emission negative test passes; cross-jurisdiction negative test passes; `views_smoke` 70/70.

---

## 18. Contract Binding

* `contract_id`: `adapter-hl7-fhir-contract`
* `boss_score_floor`: **92** (PHI + regulated; canonical 0..100 BOSS scale).
* `data_classes_allowed`: `pii`, `phi` (only with addendum), `internal`, `restricted`. PCI forbidden.
* `egress_allowlist`: per-peer FQDN/IP on standard healthcare ports (FHIR over `<host>:443`, MLLP-over-TLS on `<host>:6661` or `<host>:2575`), enumerated in the per-deployment addendum; default-deny all others.
* `allowed_actions` (default): `fhir.create`, `fhir.update`, `fhir.patch`, `fhir.search`, `fhir.bulk.export.read`, `fhir.subscription.consume`, `hl7v2.send`, `hl7v2.receive`, `smart.launch.consume`.
* `forbidden_actions`: `fhir.delete` (default), `hl7v2.send.unencrypted`, `phi.embed_in_event`, `peer.add_at_runtime`, `crypto.suite.downgrade`.

## 19. RFM Triggers

* Adding PHI data class (every PHI engagement).
* New peer (HIS, lab, payer).
* New jurisdiction.
* Bulk export to a new bucket.
* Crypto evolution.

## 20. Smart-Adapter Behaviors

* Strips PHI from every emitted bus event — only resource type + id + non-PHI metadata. PHI bodies live behind vault-bound retrieval.
* Refuses MLLP over plain TCP no matter what the peer offers.
* Detects schema drift (FHIR profile changes via CapabilityStatement) and files RFM.
* On bulk export, mints a single-use access token, downloads NDJSON to encrypted volume, and shreds on completion; never stages to disk unencrypted.
* Treats every duplicate v2 message control id as evidence of upstream restart loop and surfaces a `duplicate.detected` event.
* Verifies SMART launch context against contract-permitted scopes; refuses launches whose `aud` or `iss` aren't allow-listed.

## 21. 360 QA Coverage

| Test ID                          | Pass | Outcome                                          |
|----------------------------------|------|--------------------------------------------------|
| fhir.contract.bind.happy         | 3    | Activates after dual-sign                        |
| fhir.contract.phi.no_emit        | 4    | Event payload contains no PHI body               |
| fhir.contract.refuse.plain_mllp  | 4    | Plain-TCP MLLP refused                           |
| fhir.contract.refuse.delete      | 4    | `fhir.delete` refused default                    |
| fhir.contract.bulk.shred         | 4    | NDJSON shredded on completion                    |
| fhir.contract.rfm.peer_add       | 5    | New peer triggers RFM with ga-legal + ga-security|
| fhir.contract.smart.launch       | 4    | Launch with off-allowlist `aud` refused          |
| fhir.contract.schema_drift       | 5    | Auto-RFM on CapabilityStatement change           |
| fhir.contract.terminate          | 3    | JWT keys rotated; peer mTLS revoked              |
