# Coupa / SAP Ariba Adapter — Procurement (v0.3, Contract-Bound, Day-1 PQC)

**Card ID:** `adapter-coupa`
**Version:** v0.3 (contract-bound)
**Status:** build-ready
**Supersedes:** `adapter-coupa__Coupa_-_SAP_Ariba_Adapter_(Procurement).docx.BAK` (v0.2 — retained as old version)
**Contract pattern:** `_CONTRACT_SPEC.md`
**Used By:** `adamplus-ap-vendor-invoice`, `adamplus-ap-payment-run`, `adamplus-ap-3way-match`, `adamplus-proc-sourcing`, `adamplus-proc-po`, `wg-fin-recon`, `wg-fin-audit`

---

## 1. Target System

Coupa BSM and SAP Ariba (Spend Management). Surfaces: Coupa Core API (REST), Ariba Network APIs (REST + cXML), Ariba Sourcing APIs, Ariba Invoice Management, Coupa Pay, Webhook callbacks, OAuth-OIDC. Production scope: requisitions, purchase orders, invoices, suppliers, contracts.

## 2. Inbound + Outbound Capabilities

**Outbound:** Requisition create, PO create/transmit, supplier upsert, invoice match write-back, contract reference create.
**Inbound:** PO acknowledgments, invoice receipts, supplier proposal events, payment status (Coupa Pay), webhook callbacks.

## 3. Auth + Identity

OAuth 2.0 client credentials with vaulted client secret + signing key at `wg-sec-vault://coupa/<instance>/oauth` and `wg-sec-vault://ariba/<realm>/oauth`. cXML peers signed with X.509; certs vaulted. mTLS to vendor endpoints. Quantum lock: ML-KEM-1024 wrap, ML-DSA-65 dual-sign.

## 4. Schema Mapping

| Procurement Object  | ADAM Canonical            |
|---------------------|---------------------------|
| Requisition         | `procurement.requisition` |
| Purchase Order      | `ap.po`                   |
| Invoice (vendor)    | `ap.invoice`              |
| Receipt / GRN       | `ap.grn`                  |
| Supplier            | `vendor`                  |
| Contract            | `procurement.contract`    |
| Payment             | `treasury.payment`        |

## 5. Idempotency

* Outbound: `Adam-Idem` header (UUID v7) recorded in FR.
* cXML payloads carry `payloadID`; dedup window 24 h.
* Webhook dedup `(eventId)` 24 h.

## 6. Rate Limits

Per-instance API limits enforced 80%. cXML peer-rate honored.

## 7. Error Handling

Standard 4xx mapped to canonical. cXML `Status` codes (200/4xx/5xx semantics) mapped. Repeated `ValidationError` triggers schema-drift evaluation.

## 8. Residency

Per Coupa instance / Ariba realm DC pinned in contract. Cross-DC forbidden.

## 9. FR Events

```
adapter.procurement.req.created
adapter.procurement.po.created / .transmitted / .acked
adapter.procurement.invoice.received / .matched / .rejected
adapter.procurement.supplier.upsert
adapter.procurement.contract.referenced
adapter.procurement.payment.status.received
adapter.procurement.cxml.payload.received
adapter.procurement.webhook.received / .invalid_signature
adapter.procurement.schema.drift.detected
adapter.procurement.rate.pressure
```

## 10. Configuration Schema

```yaml
adapter_coupa:
  coupa:
    instance_url: "https://<instance>.coupahost.com"
    vault_handle: "wg-sec-vault://coupa/<instance>/oauth"
  ariba:
    realm: "<realm>"
    network_url: "https://api.ariba.com"
    vault_handle: "wg-sec-vault://ariba/<realm>/oauth"
  cxml:
    peers: [{ name: "supplier-1", endpoint: "https://supplier1/cxml", cert_handle: "wg-sec-vault://cxml/supplier-1/cert" }]
  contract_id: "adapter-coupa-contract"
```

## 11. Schemas Spoken

Coupa Core API REST, Ariba Network REST + cXML 1.2.x, Ariba SOAP services where required, Webhook payloads (signed).

## 12. Day-1 PQC Posture

Bus hybrid Ed25519 + ML-DSA-65. Vendor TLS classical; `qsuite=classical-fallback`. Vault wrap ML-KEM-1024.

## 13. Resource Profile

CPU 1.5 / 4 burst, RAM 1.5 GB / 4 burst, Disk 30 GB (cXML staging), Net ≤300 Mbps.

## 14. Dependencies

`wg-sec-vault`, FR, `hi-intent`, `orch-policy`, `meta-stability`, `meta-integrity`, `wg-fin-recon`, `wg-fin-audit`, `adam-adapter-contract-sdk`.

## 15. SLOs

PO transmission p95 ≤ 1.5 s; cXML ack p95 ≤ 500 ms; availability ≥ 99.9%; refusal p99 ≤ 50 ms.

## 16. Build Plan

1. Pre-Action Gate via SDK.
2. OAuth clients for Coupa + Ariba.
3. cXML signer + verifier with peer cert pinning.
4. PO/Invoice/Receipt clients.
5. Webhook receiver with signature verify.
6. 3-way-match reconciliation hooks.
7. QA pass1..5 + 360.

## 17. Definition of Done

`qa_all` / `qa_360` / `qa_pass3..5` 100/100; contract lifecycle green; cXML negative test passes; `views_smoke` 70/70.

---

## 18. Contract Binding

* `contract_id`: `adapter-coupa-contract` (covers both Coupa BSM and SAP Ariba surfaces in this adapter; per spec convention `adapter-<card-id>-contract`)
* `boss_score_floor`: **78** (canonical 0..100 BOSS scale; procurement + 3-way match materiality).
* `data_classes_allowed`: `pii`, `internal`, `restricted`, `pci-token` (vendor banking refs only).
* `egress_allowlist`: `*.coupahost.com:443`, `api.ariba.com:443`, plus cXML peer endpoints (each `<host>:443` listed in per-deployment addendum).
* `allowed_actions` (default): `req.create`, `po.create`, `po.transmit`, `invoice.match`, `invoice.receive`, `supplier.upsert`, `contract.reference.create`, `payment.status.consume`, `webhook.receive`, `cxml.send`, `cxml.receive`.
* `forbidden_actions`: `policy.modify`, `approval_chain.write`, `instance.config.write`, `payment.execute` (sits with treasury adapters).

## 19. RFM Triggers

* New cXML peer.
* New Coupa instance / Ariba realm.
* New approval-chain integration.
* Crypto evolution.

## 20. Smart-Adapter Behaviors

* Validates PO totals against requisition sum-of-lines before transmit; refuses on mismatch.
* Reconciles incoming invoices against ADAM's `ap.po` + `ap.grn` for 3-way match; mismatch raises `recon.divergence`.
* Verifies cXML signatures and pins to peer certs on file; refuses unsigned cXML.
* Auto-RFM on Coupa/Ariba schema delta detected via metadata.

## 21. 360 QA Coverage

| Test ID                              | Pass | Outcome                                  |
|--------------------------------------|------|------------------------------------------|
| proc.contract.bind.happy             | 3    | Activates after dual-sign                |
| proc.contract.refuse.unsigned_cxml   | 4    | Unsigned cXML refused                    |
| proc.contract.refuse.policy_modify   | 4    | Policy mod refused                       |
| proc.contract.po.req.match           | 4    | PO refused on req mismatch               |
| proc.contract.recon.3way             | 5    | 3-way mismatch raises divergence         |
| proc.contract.rfm.peer_add           | 5    | New cXML peer triggers RFM               |
| proc.contract.terminate              | 3    | OAuth + cXML certs rotated               |
