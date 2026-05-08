# Microsoft Dynamics 365 Adapter (v0.3, Contract-Bound, Day-1 PQC)

**Card ID:** `adapter-dynamics`
**Version:** v0.3 (contract-bound)
**Status:** build-ready
**Supersedes:** `adapter-dynamics__Microsoft_Dynamics_365_Adapter.docx.BAK` (v0.2 — retained as old version)
**Contract pattern:** `_CONTRACT_SPEC.md`
**Used By:** `wg-market-customer`, `wg-market-partner`, `wg-fin-txn`, `wg-fin-recon`, `adamplus-crm-360`, `adamplus-crm-lead`, `adamplus-crm-pipeline`, `adamplus-crm-success`, `adamplus-crm-cases`, `adamplus-fin-gl`, `adamplus-ar-invoice`, `wg-data-quality`

---

## 1. Target System

Microsoft Dynamics 365 — Sales, Customer Service, Field Service, Finance & Operations (F&O), Supply Chain, Business Central. APIs: Dataverse Web API (OData v4), Dual-write events, Power Automate cloud flows (excluded by default), F&O OData/SOAP, Business Events (Dataverse), Event Grid bridge, Files in Dataverse.

## 2. Inbound + Outbound Capabilities

**Outbound:** Entity create/upsert/delete on permitted Dataverse entity sets; F&O OData posting (sales orders, journals); Business Central API; FetchXML query (read).

**Inbound:** Dataverse Webhook subscription, Business Events via Event Grid, F&O business events via service bus.

## 3. Auth + Identity

App-only auth via Entra ID (Azure AD) client credentials with certificate, vaulted at `wg-sec-vault://dynamics/<tenant>/<env>/cert`. Service Principal granted least-privilege Application Users in each environment. mTLS to `*.crm.dynamics.com`, `*.dynamics.com`. Quantum lock: ML-KEM-1024 wrap, ML-DSA-65 dual-sign.

## 4. Schema Mapping

| Dynamics Entity         | ADAM Canonical                    |
|-------------------------|-----------------------------------|
| `account` / `contact`   | `customer.organization` / `person`|
| `opportunity`           | `pipeline.opportunity`            |
| `incident` (case)       | `service.case`                    |
| `salesorder`            | `sales.order`                     |
| `invoice`               | `ar.invoice`                      |
| `purchaseorder` (F&O)   | `ap.po`                           |
| `journal_header` (F&O)  | `finance.journal_entry`           |
| Business Central items  | `inventory.item`                  |

## 5. Idempotency

* Outbound: custom column `adam_idem` (UUID v7) + `If-Match: *` header semantics; FR pre-write.
* Inbound webhook dedup `(eventId, recordId)` 24 h.
* F&O batch jobs keyed by `BatchJobId` recorded in FR.

## 6. Rate Limits

Dataverse service protection limits enforced 80%. F&O concurrency caps honored. Power Automate flows are NOT used by default.

## 7. Error Handling

`InvalidEntityName`, `DuplicateRecord`, `OperationLimitExceeded` mapped to canonical taxonomy. Plugin failures on the Dynamics side ⇒ DLQ; never auto-retry plugin-related failures (unsafe).

## 8. Residency

Per-environment Azure region pinned (e.g., `crm.dynamics.com`, `crm4.dynamics.com` (EMEA)). Cross-region forbidden without RFM.

## 9. FR Events

```
adapter.dynamics.entity.upsert.ok / .failed
adapter.dynamics.fo.journal.posted
adapter.dynamics.bc.entity.upsert.ok
adapter.dynamics.businessevent.received
adapter.dynamics.webhook.received / .invalid_signature
adapter.dynamics.schema.drift.detected
adapter.dynamics.rate.pressure
```

## 10. Configuration Schema

```yaml
adapter_dynamics:
  tenant: "<entra tenant>"
  environments:
    - name: "ce-prod"
      url: "https://<org>.crm.dynamics.com"
      kind: "dataverse"
    - name: "fo-prod"
      url: "https://<org>.operations.dynamics.com"
      kind: "fo"
  vault_handle: "wg-sec-vault://dynamics/<tenant>/cert"
  app_id: "<entra app>"
  contract_id: "adapter-dynamics-contract"
```

## 11. Schemas Spoken

Dataverse Web API (OData v4), F&O OData + SOAP, Business Central API, FetchXML, Business Events (Event Grid + Service Bus), Webhooks.

## 12. Day-1 PQC Posture

Bus: hybrid Ed25519 + ML-DSA-65. Microsoft TLS: classical (TLS 1.3 ECDHE+ECDSA); `qsuite=classical-fallback`. Vault wrap ML-KEM-1024. Auto-RFM when Microsoft publishes hybrid PQC cipher suites in the official roadmap.

## 13. Resource Profile

CPU 2 / 5 burst, RAM 2 GB / 6 burst, Disk 30 GB, Net ≤500 Mbps.

## 14. Dependencies

`wg-sec-vault`, FR, `hi-intent`, `orch-policy`, `meta-stability`, `meta-integrity`, `wg-fin-recon`, `wg-data-quality`, `adam-adapter-contract-sdk`, `adapter-okta` (Entra ID may federate to Okta).

## 15. SLOs

Dataverse write p95 ≤ 1.0 s; F&O posting p95 ≤ 2.0 s; webhook p95 ≤ 200 ms; availability ≥ 99.9%.

## 16. Build Plan

1. Pre-Action Gate via SDK.
2. App-only auth with vault-bound cert.
3. Dataverse client (OData) with `adam_idem` + If-Match.
4. F&O client with batch-job idempotency.
5. Business Events via Event Grid + Service Bus.
6. Schema-drift detector via Dataverse metadata.
7. QA pass1..5 + 360.

## 17. Definition of Done

`qa_all` / `qa_360` / `qa_pass3..5` 100/100; contract lifecycle green; cross-env negative test passes; `views_smoke` 70/70.

---

## 18. Contract Binding

* `contract_id`: `adapter-dynamics-contract`
* `boss_score_floor`: **78** (canonical 0..100 BOSS scale; financial materiality via F&O scope).
* `data_classes_allowed`: `pii`, `internal`, `restricted`. PCI requires F&O addendum (rare).
* `egress_allowlist`: `*.crm.dynamics.com:443`, `*.dynamics.com:443`, `<org>.operations.dynamics.com:443`, Event Grid + Service Bus FQDNs per environment.
* `allowed_actions` (default): `dataverse.entity.upsert`, `dataverse.entity.read`, `fo.journal.post`, `fo.salesorder.post`, `bc.entity.upsert`, `fetchxml.query`, `webhook.receive`, `businessevent.subscribe`.
* `forbidden_actions`: `power_automate.execute`, `plugin.deploy`, `solution.import`, `permission.modify`, `environment.config.write`, `dual_write.config.modify`.

## 19. RFM Triggers

* New environment.
* New entity outside schema mapping.
* Permitting `power_automate.execute`.
* Crypto evolution.
* Cross-region.

## 20. Smart-Adapter Behaviors

* Detects Dataverse plugin chains that would mutate the record post-write; if a custom plugin is detected on a permitted entity, contract refuses write until plugin chain is logged in addendum.
* Auto-RFM on Dataverse metadata schema delta.
* For F&O journal postings, refuses to bypass the Finance Governor's posting-window policy.
* Records dual-write configuration hash on each restart and refuses to start if hash drifts from contract-recorded baseline.

## 21. 360 QA Coverage

| Test ID                          | Pass | Outcome                                       |
|----------------------------------|------|-----------------------------------------------|
| dyn.contract.bind.happy          | 3    | Activates after dual-sign                     |
| dyn.contract.refuse.flow         | 4    | Power Automate execution refused              |
| dyn.contract.refuse.plugin_chain | 4    | Refuses write to entity with unlogged plugin  |
| dyn.contract.rfm.entity_add      | 5    | New entity triggers RFM                       |
| dyn.contract.dualwrite.drift     | 4    | Dual-write hash mismatch ⇒ refuse start       |
| dyn.contract.schema_drift        | 5    | Auto-RFM on metadata change                   |
| dyn.contract.terminate           | 3    | App credentials revoked; vault rotated        |
