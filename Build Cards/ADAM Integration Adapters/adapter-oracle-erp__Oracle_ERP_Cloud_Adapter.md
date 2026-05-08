# Oracle ERP Cloud Adapter (v0.3, Contract-Bound, Day-1 PQC)

**Card ID:** `adapter-oracle-erp`
**Version:** v0.3 (contract-bound)
**Status:** build-ready
**Supersedes:** `adapter-oracle-erp__Oracle_ERP_Cloud_Adapter.docx.BAK` (v0.2 — retained as old version)
**Contract pattern:** `_CONTRACT_SPEC.md`
**Used By:** `wg-fin-txn`, `wg-fin-recon`, `wg-fin-budget`, `wg-fin-audit`, `adamplus-fin-gl`, `adamplus-ap-vendor-invoice`, `adamplus-ap-payment-run`, `adamplus-ap-3way-match`, `adamplus-ar-invoice`, `adamplus-fin-tax-calc`

---

## 1. Target System

Oracle Fusion ERP Cloud (Financials, Procurement, Project, Risk, EPM). Surfaces: REST API (Financials, Procurement, Common), SOAP services for legacy/business operations, BI Publisher (BIP) reports, Oracle Integration Cloud (OIC) for event-driven, Files via UCM, ESS (Enterprise Scheduler Service) for batches.

## 2. Inbound + Outbound Capabilities

**Outbound:** REST upserts on permitted resources (`/fscmRestApi/resources/...`); SOAP invocation (gated); BIP report execution; ESS job submit; UCM file upload for FBDI loads (FBDI = File-Based Data Import).

**Inbound:** OIC integration triggers receiver; BIP report pull on schedule; UCM file pull.

## 3. Auth + Identity

OAuth 2.0 client credentials with assertion-grant; signing cert vaulted at `wg-sec-vault://oracle/<pod>/cert`. Per-scope IT Security Roles assigned to a service identity. mTLS to `*.oraclecloud.com`. Quantum lock: ML-KEM-1024 wrap, ML-DSA-65 dual-sign.

## 4. Schema Mapping

| Oracle Resource          | ADAM Canonical                |
|--------------------------|-------------------------------|
| `journalEntries`         | `finance.journal_entry`       |
| `journalEntryLines`      | `finance.journal_line`        |
| `invoices` (AP)          | `ap.invoice`                  |
| `purchaseOrders`         | `ap.po`                       |
| `receivingTransactions`  | `ap.grn`                      |
| `customerInvoices`       | `ar.invoice`                  |
| `payments`               | `treasury.payment`            |
| `suppliers`              | `vendor`                      |
| `customers`              | `customer.organization`       |
| FBDI bulk loads          | `fbdi.<entity>`               |

## 5. Idempotency

* REST: `Idempotency-Key` (UUID v7) recorded in FR; resource-level `External_System_Reference`.
* FBDI: filename includes UUID + sha256; ESS process tracks request id in FR.

## 6. Rate Limits

Oracle pod throughput limits; contract enforces 80%. ESS concurrency capped per pod.

## 7. Error Handling

`ZCA_*` business errors mapped to canonical taxonomy. `JBO-*` framework errors handled with backoff. Validation failures on FBDI ⇒ DLQ + auto-RFM if recurring schema drift.

## 8. Residency

Oracle pod region pinned (NA / EMEA / APAC). Cross-region forbidden without RFM. PII allowed; PCI requires Treasury addendum.

## 9. FR Events

```
adapter.oracle.rest.upsert.ok / .failed
adapter.oracle.fbdi.uploaded / .ess.completed / .ess.failed
adapter.oracle.bip.report.executed
adapter.oracle.oic.event.received
adapter.oracle.schema.drift.detected
adapter.oracle.lock.contention
adapter.oracle.rate.pressure
```

## 10. Configuration Schema

```yaml
adapter_oracle_erp:
  pod: "<pod-id>"
  base_url: "https://<pod>.oraclecloud.com"
  vault_handle: "wg-sec-vault://oracle/<pod>/cert"
  scopes: ["AP", "AR", "GL", "PO", "Procurement"]
  oic_listener: "https://adam.<tenant>/adapters/oracle/oic"
  contract_id: "adapter-oracle-erp-contract"
```

## 11. Schemas Spoken

REST `/fscmRestApi/resources/*`, SOAP business services (WSDL), BIP XML/CSV, FBDI file specs, ESS REST.

## 12. Day-1 PQC Posture

Bus: hybrid Ed25519 + ML-DSA-65. Oracle TLS: classical; `qsuite=classical-fallback`. Vault wrap ML-KEM-1024.

## 13. Resource Profile

CPU 2 / 6 burst, RAM 2 GB / 6 burst, Disk 50 GB (FBDI staging), Net ≤500 Mbps.

## 14. Dependencies

`wg-sec-vault`, FR, `hi-intent`, `orch-policy`, `meta-stability`, `meta-integrity`, `wg-fin-recon`, `wg-fin-audit`, `wg-data-quality`, `adam-adapter-contract-sdk`.

## 15. SLOs

REST write p95 ≤ 1.5 s; FBDI ESS round-trip p95 ≤ 5 min; availability ≥ 99.9%; refusal p99 ≤ 50 ms.

## 16. Build Plan

1. Pre-Action Gate via SDK.
2. OAuth client-credentials with assertion grant.
3. REST client with idempotency-key + ESR.
4. FBDI uploader to UCM with sha256-named files.
5. ESS submitter + status poller.
6. OIC inbound listener.
7. QA pass1..5 + 360.

## 17. Definition of Done

`qa_all` / `qa_360` / `qa_pass3..5` 100/100; contract lifecycle green; FBDI staging cleanup verified; `views_smoke` 70/70.

---

## 18. Contract Binding

* `contract_id`: `adapter-oracle-erp-contract`
* `boss_score_floor`: **80** (canonical 0..100 BOSS scale; financial materiality across AP/AR/GL).
* `data_classes_allowed`: `pii`, `internal`, `restricted`. PCI by addendum.
* `egress_allowlist`: `*.oraclecloud.com:443`, pod-specific FQDNs.
* `allowed_actions` (default): `journal.post`, `journal.read`, `ap_invoice.create`, `ap_payment.run`, `ar_invoice.create`, `po.read`, `po.create` (limited), `supplier.upsert`, `customer.upsert`, `fbdi.upload`, `ess.submit`, `bip.execute`, `oic.event.receive`.
* `forbidden_actions`: `role.modify`, `flexfield.modify`, `period.open_close`, `setup.task.run`, `personalization.deploy`, `report.create`.

## 19. RFM Triggers

* New scope (e.g., Project Portfolio).
* New pod or region.
* Lifting period-close restriction.
* PCI addendum.
* Crypto evolution.

## 20. Smart-Adapter Behaviors

* Detects period-close events and self-quiesces FI postings during close window unless contract grants close-window posting (rare).
* Refuses to submit ESS jobs whose process names are not in addendum.
* FBDI files validated against latest published schema before upload; refuses upload on schema drift and files auto-RFM.
* On `JBO-*` lock errors, retries with backoff while preserving FR-anchored ordering.
* Reconciles GL trial balance daily against ADAM's mirrored ledger; emits `recon.divergence` on mismatch.

## 21. 360 QA Coverage

| Test ID                              | Pass | Outcome                                |
|--------------------------------------|------|----------------------------------------|
| oracle.contract.bind.happy           | 3    | Activates after dual-sign              |
| oracle.contract.refuse.role          | 4    | `role.modify` refused                  |
| oracle.contract.refuse.period_closed | 4    | Posting refused during close           |
| oracle.contract.fbdi.schema          | 5    | Auto-RFM on FBDI schema drift          |
| oracle.contract.recon.gl             | 5    | Daily GL recon flags divergence        |
| oracle.contract.rfm.scope            | 5    | New scope triggers RFM                 |
| oracle.contract.rate_ceiling         | 4    | In-process throttle holds              |
| oracle.contract.terminate            | 3    | OAuth client revoked; vault rotated    |
