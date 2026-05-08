# SAP S/4HANA Adapter (v0.3, Contract-Bound, Day-1 PQC)

**Card ID:** `adapter-sap-s4hana`
**Version:** v0.3 (contract-bound)
**Status:** build-ready
**Supersedes:** `adapter-sap-s4hana__SAP_S-4HANA_Adapter.docx.BAK` (v0.2 — retained as old version)
**Contract pattern:** `_CONTRACT_SPEC.md`
**Used By:** `wg-fin-txn`, `wg-fin-recon`, `wg-fin-budget`, `wg-fin-audit`, `adamplus-fin-gl`, `adamplus-ap-3way-match`, `adamplus-ap-vendor-invoice`, `adamplus-ap-payment-run`, `adamplus-ar-invoice`, `adamplus-ar-revrec`, `wg-ops-translate`

---

## 1. Target System

SAP S/4HANA (Cloud Public/Private and on-prem 2023+). Surfaces: SAP Gateway OData v2 + v4, SAP API Hub catalog, CDS-exposed entity sets, SAP Event Mesh (CloudEvents), IDoc inbound/outbound, BAPI via SOAP, Business Add-In (BAdI) custom OData, Job Scheduling Service. Production scope spans Finance (FI, CO), Materials (MM), Sales (SD), Production (PP), Plant Maintenance (PM), and Procurement (P2P). Out of scope by default: ABAP transport deploys, security role definitions, system configuration. Those require an RFM with `ga-security` + `ga-legal`.

## 2. Inbound + Outbound Capabilities

**Outbound (ADAM → SAP):**

* OData v4 deep-insert / patch / delete on permitted entity sets.
* IDoc post (ALE) for legacy financial/material flows.
* BAPI invocation via SOAP for protected business operations.
* Event Mesh publish for CloudEvents-shaped business events.
* Job submit to Job Scheduling Service for batch postings.

**Inbound (SAP → ADAM):**

* Event Mesh subscription on configured queues.
* Webhook receiver for SAP-emitted CloudEvents.
* Periodic OData delta polls with `$filter=ChangedAt gt …` cursors.
* IDoc inbound (ALE port) with ALE/EDI-grade signing.
* Job-result polling.

## 3. Auth + Identity

* OAuth 2.0 SAML Bearer Assertion + Client Credentials (app-to-app); BTP destination service-issued.
* mTLS client certs lifetime 90d, vault-handled at `wg-sec-vault://sap/<tenant>/mtls`.
* Communication Arrangement per scope; ADAM holds one Communication User per scope-class, never a privileged user.
* Quantum lock: ML-KEM-1024 wrap on cert private keys; ML-DSA-65 dual-sign on every emitted bus event.
* mTLS to `*.s4hana.cloud.sap`, `*.hana.ondemand.com`, on-prem `<host>:443/8443` per contract egress allowlist.

## 4. Schema Mapping (External ↔ ADAM)

| SAP Entity                    | ADAM Canonical Concept            | Notes                                 |
|-------------------------------|-----------------------------------|---------------------------------------|
| `BusinessPartner`             | `customer.organization` / `vendor`| Role distinguishes customer vs vendor |
| `JournalEntry` (`ACDOCA`)     | `finance.journal_entry`           | One-line ACDOCA rows                  |
| `JournalEntryItem`            | `finance.journal_line`            |                                       |
| `SupplierInvoice`             | `ap.invoice`                      | Drives 3-way match                    |
| `PurchaseOrder`               | `ap.po`                           |                                       |
| `GoodsMovement`               | `ap.grn`                          |                                       |
| `CustomerInvoice`             | `ar.invoice`                      |                                       |
| `Payment`                     | `treasury.payment`                | Outbound payment run                  |
| `MaterialDocument`            | `mm.material_document`            |                                       |
| `ProductionOrder`             | `pp.production_order`             |                                       |
| `MaintenanceRequest`          | `pm.work_request`                 |                                       |
| `Z*` custom CDS               | namespace `sap.<custom>`          | Per-tenant addendum                   |
| Event Mesh CloudEvent         | `bus.event.sap.<topic>`           | Bridged with re-signature             |
| IDoc                          | `bus.event.sap.idoc.<MestypIdoctyp>`| With ALE control record metadata    |

Schema-drift detector watches CDS metadata; deltas trigger auto-RFM.

## 5. Idempotency

* Outbound: `Adam-Idempotency-Key` header (UUID v7) recorded in FR before submit; OData entities also stamped on a custom field `Z_IDEM__c` where present.
* IDoc: external ID `EDI_DC40-DOCNUM` echoed back from SAP; adapter dedupes on `(SNDPRT, MESCOD, DOCNUM)`.
* Inbound CloudEvents: dedup window 24 h on `(source, id)`.
* Restart: idempotency journal reconciles against FR before any POST.

## 6. Rate Limits

* Per-tenant Communication Arrangement throttle plus an in-process `rate_ceiling_per_min` from contract.
* Bulk OData via batched `$batch` requests; size cap 100 sub-ops, serialized per scope.
* Event Mesh quota per queue; backpressure honored via consumer flow control.
* On 429 / `RATE_LIMITED` / `MAX_CONCURRENT_SESSIONS`: jittered backoff to 8 min, then `rate_pressure` exception.

## 7. Error Handling

* Map SAP error classes (`businessError`, `lockTableOverflow`, `transportError`, `permission`) to canonical taxonomy.
* `LOCK_TABLE_OVERFLOW` / `ENQUEUE_REJECTED` → retry with backoff, never break ordering of journal entries.
* Validation errors on FI postings → DLQ + auto-RFM if schema delta is the cause.
* Every error is dual-signed onto the ADAM bus.

## 8. Residency

S/4HANA Cloud regions explicitly listed in contract (e.g., `eu10`, `us10`, `jp10`); on-prem hosts pinned by hostname. Cross-region data flow requires RFM. PII data in `BusinessPartner` is allowed; PCI in payment data requires `pci` data class to be in `contract.data_classes_allowed`.

## 9. FR Events (adapter-specific)

```
adapter.sap.odata.write.ok / .failed
adapter.sap.odata.read.ok
adapter.sap.idoc.posted / .received / .malformed
adapter.sap.bapi.invoked
adapter.sap.eventmesh.published / .received
adapter.sap.job.submitted / .completed / .failed
adapter.sap.schema.drift.detected
adapter.sap.lock.contention
adapter.sap.rate.pressure
```

Plus all common `adapter.contract.*` events.

## 10. Configuration Schema

```yaml
adapter_sap_s4hana:
  tenant_id: "<tenant>"
  base_url: "https://my<tenant>.s4hana.cloud.sap"
  vault_handle: "wg-sec-vault://sap/<tenant>/mtls"
  comm_arrangement: "SAP_COM_<n>"
  scopes: ["FI", "MM", "SD", "P2P"]
  event_mesh:
    queues: ["JournalEntry/Created", "SupplierInvoice/Posted"]
  contract_id: "adapter-sap-s4hana-contract"
```

## 11. Schemas Spoken

* OData v2 + v4 with CDS annotations.
* IDoc ALE (`EDI_DC40` + segments).
* SOAP/BAPI WSDLs.
* CloudEvents 1.0 over Event Mesh (AMQP 1.0/MQTT/HTTP).
* Job Scheduling Service REST.

## 12. Day-1 PQC Posture

* Bus emissions: hybrid Ed25519 + ML-DSA-65.
* SAP→adapter mTLS: classical X25519 + ECDSA P-256 (SAP roadmap-pending for hybrid). `qsuite=classical-fallback` recorded.
* Vault wrap: ML-KEM-1024.
* IDoc ALE secure transport via mTLS only; SNC/PSE classical until SAP exposes hybrid.

## 13. Resource Profile

* CPU: 2 vCPU steady, 6 vCPU burst (FI bulk close).
* Memory: 2 GB steady, 6 GB burst.
* Disk: 30 GB ephemeral.
* Network: ≤800 Mbps egress; per-tenant long-lived AMQP.

## 14. Dependencies

`wg-sec-vault`, FR, `hi-intent`, `orch-policy`, `meta-stability`, `meta-integrity`, `wg-data-quality`, `adam-adapter-contract-sdk`, `wg-fin-recon` (for posting reconciliation).

## 15. SLOs

* Outbound write p95 ≤ 1.5 s.
* Event Mesh fan-out p95 ≤ 1.0 s.
* Adapter availability ≥ 99.9%.
* Refusal latency p99 ≤ 50 ms.
* Contract bind/amend roundtrip ≤ 30 s.

## 16. Build Plan

1. Pre-Action Gate via SDK.
2. Communication Arrangement provisioning template (per scope).
3. OData client with `$batch` and `$filter` cursors.
4. Event Mesh consumer with checkpoint into FR.
5. IDoc ALE inbound port.
6. Schema-drift detector hooked to CDS metadata.
7. QA pass1..5 + 360.

## 17. Definition of Done

* `qa_all` 100/100, `qa_360` 100/100, `qa_pass3..5` 100/100 each.
* Contract lifecycle smoke test green.
* Schema-drift auto-RFM verified.
* Egress allowlist enforced at CNI.
* `views_smoke` 70/70.
* Index entry updated.

---

## 18. Contract Binding

* `contract_id`: `adapter-sap-s4hana-contract`
* `boss_score_floor`: **78** (financial materiality; canonical 0..100 BOSS scale).
* `data_classes_allowed`: `pii`, `internal`, `restricted`, `pci` (only with ga-financial co-sign in addendum).
* `egress_allowlist`: `*.s4hana.cloud.sap:443`, `*.hana.ondemand.com:443`, on-prem hosts per addendum.
* `allowed_actions` (default): `journal.post`, `journal.read`, `supplier_invoice.post`, `customer_invoice.post`, `purchase_order.read`, `goods_movement.post`, `payment.run.submit`, `bp.upsert`, `eventmesh.subscribe`, `eventmesh.publish`, `idoc.post`, `idoc.receive`, `bapi.invoke.<allowlisted>`.
* `forbidden_actions`: `abap.transport`, `role.modify`, `system.config.write`, `gl_account.modify`, `period.open_close` (these belong to humans + Finance Governor through RFM).

## 19. RFM Triggers

* New scope (e.g., adding PP).
* Crossing region boundary.
* New BAPI to allowlist.
* Lifting data class to include `pci`.
* Adding a new on-prem host.
* Crypto suite evolution.

## 20. Smart-Adapter Behaviors

* Refuses any FI posting where `BukrsCompanyCode` is not in contract scope.
* Detects period-open/close events and self-quiesces during close window unless contract grants close-window posting (rare).
* Enforces 4-eyes on payment runs above threshold by routing through `wg-fin-txn` policy gate before submit.
* Auto-RFM on CDS view shape drift (added/removed fields, type changes).
* Records ALE acknowledgment (`ALEAUD`) and reconciles against FR; mismatch triggers `recon.divergence` exception.

## 21. 360 QA Coverage

| Test ID                          | Pass | Outcome                                            |
|----------------------------------|------|----------------------------------------------------|
| sap.contract.bind.happy          | 3    | Activates after dual-sign verified                 |
| sap.contract.refuse.role         | 4    | Refuses `role.modify` even if requested            |
| sap.contract.rfm.scope_pp        | 5    | Adding PP scope triggers full RFM                  |
| sap.contract.refuse.period       | 4    | Refuses post during closed period unless granted   |
| sap.contract.idoc.recon          | 4    | ALE ack mismatch raises `recon.divergence`         |
| sap.contract.schema_drift        | 5    | Auto-RFM filed on CDS shape change                 |
| sap.contract.rate_ceiling        | 4    | In-process throttle holds at ceiling               |
| sap.contract.terminate           | 3    | Vault rotation; comm arr left for human deactivate |
