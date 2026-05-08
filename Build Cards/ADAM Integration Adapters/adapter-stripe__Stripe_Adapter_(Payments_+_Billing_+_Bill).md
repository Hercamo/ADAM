# Stripe Adapter — Payments + Billing + Bill (v0.3, Contract-Bound, Day-1 PQC)

**Card ID:** `adapter-stripe`
**Version:** v0.3 (contract-bound)
**Status:** build-ready
**Supersedes:** `adapter-stripe__Stripe_Adapter_(Payments_+_Billing_+_Bill).docx.BAK` (v0.2 — retained as old version)
**Contract pattern:** `_CONTRACT_SPEC.md`
**Used By:** `adamplus-ar-invoice`, `adamplus-ar-collections`, `adamplus-ar-credit`, `adamplus-ar-revrec`, `adamplus-fin-treasury`, `adamplus-fin-tax-calc`, `adamplus-ops-subscription`, `wg-fin-txn`, `wg-fin-recon`, `wg-fin-audit`

---

## 1. Target System

Stripe (Payments, Billing, Connect, Issuing, Treasury, Tax, Bill). REST API at `api.stripe.com`, Connect API for platform/marketplace flows, Webhooks v1 (signed `Stripe-Signature`), Sigma/Data Pipeline for analytics export, Stripe CLI deployed only in dev. Production scope: customers, invoices, subscriptions, payment intents, payouts, refunds, disputes, tax calculations, Bill payables. Out of scope by default: Stripe Connect onboarding for new sub-merchants, Issuing card creation, Atlas — those require RFM + ga-legal.

## 2. Inbound + Outbound Capabilities

**Outbound:**
* Customer create/update.
* PaymentIntent / SetupIntent create + confirm (off-session for saved methods only).
* Invoice create / finalize / send / void.
* Subscription create / update / cancel.
* Refund create.
* Payout create (only with `treasury` scope in contract).
* Bill payable create / pay (Stripe Bill).
* Tax calculation create.
* Sigma report query (read).

**Inbound:**
* Webhook receiver with HMAC-SHA256 (`Stripe-Signature` v1) and replay window 5 min.
* Data Pipeline pulls (S3-anchored) for offline analytics — read-only.

## 3. Auth + Identity

* Restricted API keys per scope, vaulted at `wg-sec-vault://stripe/<account>/restricted/<scope>`. No live keys ever leave vault; adapter holds a short-lived in-memory session.
* OAuth 2.0 for Stripe Connect (platform→connected-account), short-lived access tokens.
* Webhook signing secret in vault; rotation 90 d via RFM.
* Quantum lock: ML-KEM-1024 wrap, ML-DSA-65 dual-sign on bus emissions.
* mTLS server identity pinned to Stripe's published cert chain.

## 4. Schema Mapping

| Stripe Object        | ADAM Canonical Concept            | Notes                          |
|----------------------|-----------------------------------|--------------------------------|
| `Customer`           | `customer.organization`/`person`  | PII; metadata keyed on `external_id` |
| `Invoice`            | `ar.invoice`                      |                                |
| `InvoiceItem`        | `ar.invoice_line`                 |                                |
| `Subscription`       | `ar.subscription`                 |                                |
| `PaymentIntent`      | `treasury.payment_intent`         | PCI sensitive (PAN never seen) |
| `Charge`             | `treasury.charge`                 |                                |
| `Refund`             | `treasury.refund`                 |                                |
| `Payout`             | `treasury.payout`                 |                                |
| `Dispute`            | `treasury.dispute`                |                                |
| `TaxCalculation`     | `tax.calculation`                 |                                |
| `Payable` (Bill)     | `ap.payable`                      |                                |

PAN, CVV, full card data are NEVER seen by the adapter — Stripe Elements / Checkout tokenize at the edge. The contract forbids any verb that would handle raw PAN.

## 5. Idempotency

* Every outbound POST carries `Idempotency-Key: <uuid v7>`; key recorded in FR before send.
* Webhook inbound: dedup `(event.id)` 24 h window.
* On crash, journal reconciles before resuming; replay-safe by Stripe's idempotency contract.

## 6. Rate Limits

* Stripe live-mode default 100 read/s, 100 write/s — contract `rate_ceiling_per_min` set to 80% equivalent and enforced in-process.
* Search API tighter ceilings; honored per endpoint class.
* On 429: jittered backoff 8 min, then `rate_pressure` exception.

## 7. Error Handling

* Stripe error types (`api_error`, `card_error`, `idempotency_error`, `invalid_request_error`, `rate_limit_error`) mapped to canonical taxonomy.
* `card_error` is end-user feedback, NOT a system fault — surfaced through normal AR flow.
* `idempotency_error` indicates key reuse with different payload — adapter halts the verb and emits `idempotency.collision` for human review.

## 8. Residency

Stripe data is global; the contract pins `external_system.region` to one or more Stripe-supported regions and refuses customer creation in unlisted residency. EU customers route through EU data plane where contracted.

## 9. FR Events

```
adapter.stripe.customer.upsert.ok / .failed
adapter.stripe.invoice.created / .finalized / .voided
adapter.stripe.subscription.created / .updated / .canceled
adapter.stripe.payment_intent.created / .confirmed / .failed
adapter.stripe.refund.created
adapter.stripe.payout.submitted
adapter.stripe.dispute.received
adapter.stripe.tax.calculated
adapter.stripe.bill.paid
adapter.stripe.webhook.received / .invalid_signature / .replayed
adapter.stripe.idempotency.collision
adapter.stripe.rate.pressure
```

## 10. Configuration Schema

```yaml
adapter_stripe:
  account_id: "acct_<n>"
  api_version: "2024-11-20.acacia"
  endpoints:
    api: "https://api.stripe.com"
    files: "https://files.stripe.com"
  vault_handles:
    payments: "wg-sec-vault://stripe/<account>/restricted/payments"
    billing:  "wg-sec-vault://stripe/<account>/restricted/billing"
    treasury: "wg-sec-vault://stripe/<account>/restricted/treasury"
    webhook:  "wg-sec-vault://stripe/<account>/webhook-signing"
  webhook_url: "https://adam.<tenant>/adapters/stripe/webhook"
  contract_id: "adapter-stripe-contract"
```

## 11. Schemas Spoken

* Stripe REST (`application/x-www-form-urlencoded`).
* Stripe Webhooks v1 (HMAC-SHA256, t=…,v1=…).
* Sigma SQL (read).
* Stripe Connect OAuth.

## 12. Day-1 PQC Posture

* Bus emissions: hybrid Ed25519 + ML-DSA-65.
* Stripe TLS: classical X25519 + ECDSA P-256. `qsuite=classical-fallback` recorded.
* Webhook HMAC: SHA-256 (Stripe protocol; not adapter-controlled). Adapter additionally re-signs every webhook event onto the bus with hybrid PQC.
* Vault wrap: ML-KEM-1024.

## 13. Resource Profile

* CPU: 1 vCPU steady, 3 vCPU burst.
* Memory: 1 GB.
* Disk: 10 GB ephemeral.
* Network: ≤200 Mbps egress.

## 14. Dependencies

`wg-sec-vault`, FR, `hi-intent`, `orch-policy`, `meta-stability`, `meta-integrity`, `wg-fin-txn`, `wg-fin-recon`, `adam-adapter-contract-sdk`.

## 15. SLOs

* Customer/invoice write p95 ≤ 800 ms.
* Webhook ingestion p95 ≤ 200 ms (signature verify + emit).
* Adapter availability ≥ 99.95%.
* Refusal latency p99 ≤ 30 ms.

## 16. Build Plan

1. Pre-Action Gate via SDK.
2. Restricted-key issuance and vault rotation runbook.
3. REST client with idempotency-key emission and FR pre-write.
4. Webhook receiver with replay window + signature verify.
5. Connect OAuth flow for platform mode (gated by RFM).
6. Reconciliation job against Stripe Sigma daily.
7. QA pass1..5 + 360.

## 17. Definition of Done

* `qa_all` / `qa_360` / `qa_pass3..5` 100/100 each.
* Contract lifecycle green.
* Webhook signature negative test passes (replay > 5 min refused).
* Reconciliation report green for a sample day.
* `views_smoke` 70/70.
* Index entry updated.

---

## 18. Contract Binding

* `contract_id`: `adapter-stripe-contract`
* `boss_score_floor`: **82** (high financial materiality + PCI proximity; canonical 0..100 BOSS scale).
* `data_classes_allowed`: `pii`, `internal`, `restricted`, `pci-token` (tokenized references only). Raw PAN forbidden — no verb may accept it.
* `egress_allowlist`: `api.stripe.com:443`, `files.stripe.com:443`, `q.stripe.com:443`.
* `allowed_actions` (default): `customer.upsert`, `invoice.create`, `invoice.finalize`, `invoice.void`, `subscription.create`, `subscription.update`, `subscription.cancel`, `payment_intent.create`, `payment_intent.confirm.off_session`, `refund.create`, `tax.calculate`, `webhook.receive`, `sigma.query`, `bill.payable.create`, `bill.payable.pay`.
* `forbidden_actions`: `card.create_with_pan`, `connect.account.create`, `issuing.card.create`, `treasury.financial_account.create`, `payout.create` (default forbidden; `treasury` scope addendum required).

## 19. RFM Triggers

* Promoting `payout.create` from forbidden to allowed.
* Adding Connect platform mode.
* Issuing or Treasury scope.
* New region (e.g., adding EU residency).
* Lifting rate ceiling.
* New webhook endpoint.

## 20. Smart-Adapter Behaviors

* Refuses any verb that includes a `pan` field; even if upstream callers attempt to pass one.
* Validates `Stripe-Signature` t= within 5-min window; outside window ⇒ `webhook.replayed` exception.
* Daily reconciliation: pulls Sigma BalanceTransaction set, compares to adapter's emitted `treasury.*` events, emits `recon.divergence` on mismatch.
* On `dispute` webhook, raises priority and notifies `wg-fin-audit` immediately — never silently auto-replies.
* Auto-RFM on Stripe API version deprecation notices read from `Stripe-Version-Deprecation` header.
* On `idempotency_error`, halts that verb chain and surfaces to human; never blindly retries with a new key.

## 21. 360 QA Coverage

| Test ID                          | Pass | Outcome                                       |
|----------------------------------|------|-----------------------------------------------|
| stripe.contract.bind.happy       | 3    | Activates after dual-sign verified            |
| stripe.contract.refuse.pan       | 4    | Refuses payload containing `pan`              |
| stripe.contract.refuse.payout    | 4    | `payout.create` refused without treasury scope|
| stripe.contract.webhook.replay   | 4    | Webhook outside 5-min window refused          |
| stripe.contract.recon.divergence | 5    | Daily recon flags injected divergence         |
| stripe.contract.rfm.connect      | 5    | Connect addendum runs full RFM                |
| stripe.contract.rate_ceiling     | 4    | In-process throttle holds                     |
| stripe.contract.api.deprecation  | 5    | Auto-RFM on deprecation header                |
| stripe.contract.terminate        | 3    | Restricted keys rotated; webhook secret void  |
