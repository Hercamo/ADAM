# BambooHR Adapter (v0.3, Contract-Bound, Day-1 PQC)

**Card ID:** `adapter-bamboohr`
**Version:** v0.3 (contract-bound)
**Status:** build-ready
**Supersedes:** `adapter-bamboohr__BambooHR_Adapter.docx.BAK` (v0.2 — retained as old version)
**Contract pattern:** `_CONTRACT_SPEC.md`
**Used By:** `adamplus-hr-onboarding`, `adamplus-hr-offboarding`, `adamplus-hr-benefits`, `adamplus-hr-time`, `adamplus-hr-performance`, `adamplus-hr-compliance`, `wg-data-pii`, `wg-gov-compliance`

---

## 1. Target System

BambooHR REST API, custom reports, Webhooks. Production scope: employees, time-off, training, custom tables.

## 2. Inbound + Outbound Capabilities

**Outbound:** Employee create/update, custom-table writes, time-off request creation.
**Inbound:** Webhook events for employee changes, scheduled custom-report pulls.

## 3. Auth + Identity

API key per company subdomain, vaulted at `wg-sec-vault://bamboohr/<subdomain>/api-key`. mTLS to `*.bamboohr.com`. Quantum lock: ML-KEM-1024 wrap, ML-DSA-65 dual-sign.

## 4. Schema Mapping

| BambooHR Object  | ADAM Canonical            |
|------------------|---------------------------|
| `Employee`       | `identity.worker`         |
| `TimeOffRequest` | `time.absence_request`    |
| `Training`       | `learning.training_record`|
| Custom tables    | namespace `bamboo.<table>`|

## 5. Idempotency

Outbound writes carry `Adam-Idem` (UUID v7) custom field; FR pre-write. Webhook dedup `(eventType, employeeId, hash)` 24 h.

## 6. Rate Limits

Per-company API quota; contract enforces 80%. Reports queued.

## 7. Error Handling

`401`/`403` ⇒ vault refresh; persistent fail ⇒ self-suspend. `400 ValidationError` ⇒ DLQ + auto-RFM if recurring.

## 8. Residency

Per BambooHR data center; contract pins.

## 9. FR Events

```
adapter.bamboohr.employee.upsert.ok / .failed
adapter.bamboohr.timeoff.created
adapter.bamboohr.training.upserted
adapter.bamboohr.webhook.received / .invalid_signature
adapter.bamboohr.report.fetched
adapter.bamboohr.schema.drift.detected
adapter.bamboohr.rate.pressure
```

## 10. Configuration Schema

```yaml
adapter_bamboohr:
  subdomain: "<company>"
  endpoint: "https://api.bamboohr.com/api/gateway.php/<subdomain>"
  vault_handle: "wg-sec-vault://bamboohr/<subdomain>/api-key"
  webhook_url: "https://adam.<tenant>/adapters/bamboohr/webhook"
  contract_id: "adapter-bamboohr-contract"
```

## 11. Schemas Spoken

BambooHR REST (XML/JSON), Webhooks, Custom Reports CSV.

## 12. Day-1 PQC Posture

Bus hybrid Ed25519 + ML-DSA-65. BambooHR TLS classical; `qsuite=classical-fallback`. Vault wrap ML-KEM-1024.

## 13. Resource Profile

CPU 0.5 / 2 burst, RAM 512 MB, Disk 5 GB, Net ≤100 Mbps.

## 14. Dependencies

`wg-sec-vault`, FR, `hi-intent`, `orch-policy`, `meta-stability`, `meta-integrity`, `wg-data-pii`, `adam-adapter-contract-sdk`, `adapter-okta` (identity-of-record).

## 15. SLOs

Employee write p95 ≤ 1.0 s; webhook p95 ≤ 200 ms; availability ≥ 99.9%; refusal p99 ≤ 30 ms.

## 16. Build Plan

1. Pre-Action Gate via SDK.
2. API client with vault-bound key.
3. Webhook receiver with signature verify.
4. Custom report scheduler.
5. Schema-drift detector.
6. QA pass1..5 + 360.

## 17. Definition of Done

`qa_all` / `qa_360` / `qa_pass3..5` 100/100; contract lifecycle green; `views_smoke` 70/70.

---

## 18. Contract Binding

* `contract_id`: `adapter-bamboohr-contract`
* `boss_score_floor`: **78** (PII-heavy; canonical 0..100 BOSS scale).
* `data_classes_allowed`: `pii`, `internal`, `restricted`. No PCI/PHI.
* `egress_allowlist`: `*.bamboohr.com:443`.
* `allowed_actions` (default): `employee.upsert`, `employee.read`, `timeoff.create`, `training.upsert`, `report.fetch`, `webhook.receive`.
* `forbidden_actions`: `company.config.write`, `permission.modify`, `custom_table.create`, `payroll.write` (BambooHR has limited payroll surface — not used here).

## 19. RFM Triggers

* New custom table.
* New subdomain.
* Crypto evolution.

## 20. Smart-Adapter Behaviors

* Cascades termination to `adapter-okta` and `adamplus-hr-offboarding` on hire-status change.
* Refuses to write a `legalName` change without consent record.
* Auto-RFM on schema drift in custom tables.

## 21. 360 QA Coverage

| Test ID                          | Pass | Outcome                                |
|----------------------------------|------|----------------------------------------|
| bamboo.contract.bind.happy       | 3    | Activates after dual-sign              |
| bamboo.contract.refuse.legal_name| 4    | Refused without consent record         |
| bamboo.contract.term.cascade     | 4    | Term cascades to Okta + offboarding    |
| bamboo.contract.rfm.custom_table | 5    | New table triggers RFM                 |
| bamboo.contract.schema_drift     | 5    | Auto-RFM on table delta                |
| bamboo.contract.terminate        | 3    | Key rotated; webhook secret void       |
