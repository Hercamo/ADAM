# Salesforce Adapter (v0.3, Contract-Bound, Day-1 PQC)

**Card ID:** `adapter-salesforce`
**Version:** v0.3 (contract-bound)
**Status:** build-ready
**Supersedes:** `adapter-salesforce__Salesforce_Adapter.docx.BAK` (v0.2 — retained as old version)
**Doctrine binding:** ADAM Book New v0.3
**Contract pattern:** see `_CONTRACT_SPEC.md` (this directory)
**Used By:** `wg-market-customer`, `wg-market-partner`, `wg-market-demand`, `wg-market-reputation`, `adamplus-crm-360`, `adamplus-crm-lead`, `adamplus-crm-pipeline`, `adamplus-crm-success`, `adamplus-crm-cases`, `adamplus-ar-collections`, `adamplus-ar-credit`, `ai-external-stakeholder`

---

## 1. Target System

Salesforce Sales Cloud, Service Cloud, and Marketing Cloud Engagement. Multi-tenant SaaS; per-org `My Domain` URL. Versioned REST API (`v60.0+`), Bulk API 2.0, Streaming/CDC API (CometD), Pub/Sub API (gRPC), Apex REST custom endpoints, Connect REST for Chatter and Files, Tooling API for metadata.

Production scope: contacts, accounts, opportunities, leads, cases, campaigns, custom objects (`*__c`), platform events (`*__e`), and CDC events. Out of scope by default: Apex execution, metadata deploys, anything that mutates org-level configuration. Those require an RFM.

## 2. Inbound + Outbound Capabilities

**Outbound (ADAM → Salesforce):**

* Upsert contacts/accounts/leads/opportunities/cases/custom objects via REST (`/services/data/v60.0/sobjects/<obj>`), keyed by external ID.
* Bulk upsert/update/delete via Bulk API 2.0 ingest jobs.
* Compose REST tree creation for atomic parent/child insertion.
* Composite REST (subrequest graph) for multi-step transactions ≤25 sub-ops.
* SOQL/SOSL query execution (read).
* Attach files via Connect REST.
* Fire Platform Event publish.

**Inbound (Salesforce → ADAM):**

* Pub/Sub API gRPC subscription to CDC events on configured objects.
* Streaming API CometD subscription for legacy PushTopic/Generic Streaming feeds.
* Outbound Message HTTP receiver (signed callouts) for Workflow/Flow-driven events.
* Apex REST callbacks (custom inbound endpoints) for org-specific use cases.
* Bulk job result polling.

All inbound/outbound capabilities are gated by the adapter's bound contract. Verbs not in `contract.allowed_actions` are refused at the Pre-Action Gate and emitted as `adapter.contract.refused`.

## 3. Auth + Identity

* OAuth 2.0 JWT Bearer Flow (server-to-server). Connected App with certificate-pinned client assertion.
* Private key lives in `wg-sec-vault` under handle `wg-sec-vault://salesforce/<org_id>/jwt-signer`. Rotation: 90 days, with a 7-day RFM window for rollover.
* Refresh tokens NEVER stored long-term; access tokens cached in-memory only with TTL = token expiry minus 60 s.
* Per-org named user identity is `integration@<org-domain>` with a custom Profile that grants only the API objects/fields enumerated in `contract.allowed_actions`. Field-Level Security (FLS) is the second wall behind the contract.
* mTLS to `*.my.salesforce.com` and `*.salesforcecommerce.com` only. Egress allowlist is in `contract.egress_allowlist`.
* Quantum lock: ML-KEM-1024 wrap on the JWT signing key; ML-DSA-65 dual-sign on every event the adapter emits onto the ADAM bus.

## 4. Schema Mapping (External ↔ ADAM)

| Salesforce Object | ADAM Canonical Concept                | Notes                                            |
|-------------------|---------------------------------------|--------------------------------------------------|
| `Account`         | `customer.organization`               | `Id` ↔ `salesforce_id`; `external_id__c` is canonical link |
| `Contact`         | `customer.person`                     | PII data class; consent fields mirrored          |
| `Lead`            | `pipeline.lead`                       | Conversion tracked via `ConvertedAccountId` etc. |
| `Opportunity`     | `pipeline.opportunity`                | Stage transitions emitted as discrete events     |
| `Case`            | `service.case`                        | `Status`, `Priority`, `OwnerId`                  |
| `Campaign`        | `marketing.campaign`                  | Member changes streamed via CDC                  |
| `Task` / `Event`  | `activity.touchpoint`                 |                                                  |
| `User`            | `identity.salesforce_user`            | Read-only; identity-of-record is `adapter-okta`  |
| `Asset`           | `asset.installed_product`             |                                                  |
| `*__c` custom     | namespace `customer.<custom>`         | Mapped per-tenant in contract addendum           |
| Platform Event    | `bus.event.salesforce.<EventName__e>` | Bridged onto ADAM bus with re-signature          |
| CDC Event         | `bus.event.salesforce.cdc.<Object>`   | Includes `ChangeEventHeader` semantics           |

Schema mapping deltas detected by `wg-data-quality` against the contract trigger an automatic RFM (`schema_evolution`).

## 5. Idempotency

* Outbound: external ID `adam_idem__c` (UUID v7) on every upsert. The adapter writes this BEFORE the call and uses Salesforce's external-ID upsert semantics; retries are safe.
* Bulk API: each job is keyed by `Job-Idempotency-Key` (UUID v7) recorded in FR before the job is created; restart resumes by querying the job status, never by re-creating.
* Inbound: CDC and Platform Events are deduplicated by `(EventName, ReplayId)` window of 24h in the adapter's idempotency journal.
* Restart: on cold start the adapter reconciles its journal against FR and the latest committed `ReplayId` per channel before resuming Pub/Sub subscription.

## 6. Rate Limits

* Salesforce daily API call quota varies by edition; the contract's `rate_ceiling_per_min` is set to ≤80% of the per-minute equivalent of the org's quota and enforced in-process.
* Bulk API 2.0 ingest job size is capped at 150 MB per job; the adapter chunks larger payloads and serializes job submissions per-tenant.
* Pub/Sub gRPC backpressure: max 100 events/fetch; the adapter requests in batches sized by `boss_score`-derived burst headroom.
* On HTTP 429 / `REQUEST_LIMIT_EXCEEDED`: exponential backoff with jitter, ceiling 8 min, then file `rate_pressure` exception to `orch-exception`.

## 7. Error Handling

* Map Salesforce errors to canonical taxonomy: `validation`, `permission`, `lock`, `dup`, `quota`, `network`, `vendor`. Each is an FR event class.
* `INVALID_FIELD_FOR_INSERT_UPDATE` and `FIELD_INTEGRITY_EXCEPTION` → schema-drift evidence; auto-RFM if recurring.
* `UNABLE_TO_LOCK_ROW` → retry with backoff; never break ordering.
* `REQUIRED_FIELD_MISSING` from inbound CDC → refuse to translate; route to DLQ topic; emit `adapter.salesforce.cdc.malformed`.
* All errors are dual-signed events on the ADAM bus.

## 8. Residency

Per-org. The contract's `external_system.residency` lists allowed Salesforce Hyperforce regions for the bound org. Cross-region replication of records out of contract scope is refused. Data classes `pii`, `pci` (if present), and `phi` (rare in Salesforce, but possible in custom fields) require explicit listing in `contract.data_classes_allowed`.

## 9. FR Events (adapter-specific)

```
adapter.salesforce.upsert.ok
adapter.salesforce.upsert.failed
adapter.salesforce.bulk.job.created
adapter.salesforce.bulk.job.completed
adapter.salesforce.bulk.job.failed
adapter.salesforce.cdc.received
adapter.salesforce.cdc.malformed
adapter.salesforce.platformevent.received
adapter.salesforce.platformevent.published
adapter.salesforce.outboundmessage.received
adapter.salesforce.query.executed
adapter.salesforce.schema.drift.detected
adapter.salesforce.rate.pressure
```

Plus all common `adapter.contract.*` events from `_CONTRACT_SPEC.md` §11.

## 10. Configuration Schema

```yaml
adapter_salesforce:
  org_id: "<my-domain>"
  api_version: "v60.0"
  endpoints:
    rest: "https://<my-domain>.my.salesforce.com"
    pubsub: "api.pubsub.salesforce.com:7443"
  vault_handle: "wg-sec-vault://salesforce/<org_id>/jwt-signer"
  client_id: "<connected app id>"
  pubsub:
    topics: ["/data/AccountChangeEvent", "/event/Custom__e"]
    replay_preset: "LATEST"
  bulk:
    max_concurrent_jobs: 4
    job_size_bytes: 100_000_000
  contract_id: "adapter-salesforce-contract"
```

## 11. Schemas Spoken

* Salesforce REST API v60.0 (sObject + Composite + Tree + Query).
* Bulk API 2.0 (CSV ingest).
* Pub/Sub API (gRPC + Avro).
* CometD Streaming API (Bayeux).
* Outbound Message SOAP (legacy; HMAC-validated).
* SOQL, SOSL.
* CDC `ChangeEventHeader` schema.

## 12. Day-1 PQC Posture

* Adapter→bus emissions: hybrid Ed25519 + ML-DSA-65.
* Adapter→Salesforce mTLS: classical X25519 + ECDSA P-256 (Salesforce does not yet expose hybrid PQC suites). Every emitted event records `qsuite=classical-fallback` to mark the residual quantum exposure.
* Vault key wrap for JWT signer: ML-KEM-1024.
* When Salesforce exposes hybrid TLS in the Hyperforce roadmap, the contract is amended via RFM (`schema_evolution` is reused for crypto-suite evolution).

## 13. Resource Profile

* CPU: 1.5 vCPU steady, 4 vCPU burst.
* Memory: 1.5 GB steady, 4 GB burst (Bulk job staging).
* Disk: 20 GB ephemeral for chunked uploads + idempotency journal.
* Network: ≤500 Mbps egress; gRPC long-lived connection ×N tenants.

## 14. Dependencies

* `wg-sec-vault` — JWT signer, mTLS materials.
* Flight Recorder — append-only event log.
* `hi-intent` + `orch-policy` — RFM lifecycle.
* `meta-stability` — BOSS Score floor evaluation.
* `meta-integrity` — doctrine drift gate on amendments.
* `wg-data-quality` — schema-drift detector that files RFMs.
* `adam-adapter-contract-sdk` — shared Pre-Action Gate library.

## 15. SLOs

* Outbound write p95 ≤ 1.2 s end-to-end (excluding vendor outage).
* CDC fan-out p95 ≤ 800 ms from Salesforce commit to ADAM bus.
* Adapter availability ≥ 99.9% measured by heartbeat with contract attestation.
* Refusal latency p99 ≤ 50 ms (refusals must be cheap).
* Contract bind/amend roundtrip ≤ 30 s on the happy path.

## 16. Build Plan

1. Implement Pre-Action Gate via `adam-adapter-contract-sdk`.
2. Implement the verb registry mapping every action in §2 to a canonical contract verb.
3. Wire OAuth JWT Bearer with vault-handle-only access to the signing key.
4. Implement Pub/Sub gRPC consumer with replay-id checkpoint persisted to FR.
5. Implement Bulk 2.0 ingest pipeline with idempotency journal.
6. Implement schema-drift detector emitting auto-RFM events.
7. Wire all events in §9 onto the ADAM bus, dual-signed.
8. Run `qa_pass1..5` and `qa_360`; fix to green.

## 17. Definition of Done

* `qa_all` 100/100, `qa_360` 100/100, `qa_pass3..5` 100/100 each.
* Contract lifecycle smoke test passes (`DRAFT→ACTIVE→AMENDED→TERMINATED`).
* Refusal posture matrix from `_CONTRACT_SPEC.md` §10 fully exercised.
* `views_smoke` 70/70 — adapter shows in Directors Dashboard, FR Lifecycle, Agent + Intent overlays.
* Schema-drift auto-RFM verified end-to-end with an injected synthetic drift.
* Egress allowlist enforced at CNI/seccomp level; verified by negative test.
* Index entry in `_INDEX.md` updated.

---

## 18. Contract Binding (this adapter's contract surface)

* `contract_id`: `adapter-salesforce-contract`
* `boss_score_floor`: **74** (above platform default of 72 because of PII volume; canonical 0..100 BOSS scale).
* `data_classes_allowed`: `pii`, `internal`, `restricted`. `pci` and `phi` forbidden by default; require RFM with ga-legal + ga-financial co-sign.
* `egress_allowlist`: `*.my.salesforce.com:443`, `api.pubsub.salesforce.com:7443`, `*.documentforce.com:443`.
* `allowed_actions` (default): `account.upsert`, `contact.upsert`, `lead.upsert`, `opportunity.upsert`, `case.upsert`, `query.soql`, `bulk.ingest`, `cdc.subscribe`, `platformevent.publish`, `platformevent.subscribe`.
* `forbidden_actions`: `apex.execute`, `metadata.deploy`, `user.create`, `permissionset.assign`, `org.config.write`.

## 19. RFM Triggers (this adapter)

* Adding any object outside the schema mapping table.
* Lifting `rate_ceiling_per_min` above the org-quota-derived ceiling.
* Adding a new Salesforce org (multi-org expansion).
* Permitting `pci` or `phi` data classes.
* Crypto-suite evolution to hybrid TLS.
* Promoting a custom Apex REST endpoint to a contract verb.

## 20. Smart-Adapter Behaviors (this adapter)

* Treats every Salesforce field with `__pci` or `__hipaa` suffix as forbidden until contract amends explicitly.
* Detects when a custom object's metadata changes (via Tooling API watch) and files RFM with the diff.
* Refuses to translate a CDC event whose `ChangeEventHeader.changeType` is unknown — emits `cdc.malformed`, never reshapes.
* Periodic Profile audit: reads its own permission set every 24h, hashes it, and emits a `permission.attestation` event; mismatch with contract triggers self-suspend.

## 21. 360 QA Coverage (contract-specific tests)

| Test ID                          | Pass | Outcome                                     |
|----------------------------------|------|---------------------------------------------|
| sf.contract.bind.happy           | 3    | Adapter activates after dual-sign verified  |
| sf.contract.refuse.unbound       | 4    | All verbs refused before bind               |
| sf.contract.refuse.forbidden     | 4    | `apex.execute` refused even if requested    |
| sf.contract.rfm.scope_expand     | 5    | Adding `Asset` triggers Intent Object       |
| sf.contract.rfm.crypto_evolve    | 5    | Hybrid TLS amendment runs full RFM          |
| sf.contract.rate_ceiling         | 4    | In-process throttle holds at ceiling        |
| sf.contract.schema_drift         | 5    | Auto-RFM filed on injected drift            |
| sf.contract.permission_drift     | 4    | Self-suspend on Profile mismatch            |
| sf.contract.terminate            | 3    | Vault keys rotated; adapter inert           |
