# Adyen Adapter — Payments + Marketplaces (v0.3, Contract-Bound, Day-1 PQC)

**Card ID:** `adapter-adyen`
**Version:** v0.3 (contract-bound)
**Status:** build-ready
**Supersedes:** `adapter-adyen__Adyen_Adapter_(Payments_+_Marketplaces).docx.BAK` (v0.2 — retained as old version)
**Contract pattern:** `_CONTRACT_SPEC.md`
**Used By:** `adamplus-ar-invoice`, `adamplus-ar-collections`, `adamplus-fin-treasury`, `adamplus-ops-subscription`, `wg-fin-txn`, `wg-fin-recon`

---

## 1. Target System

Adyen Checkout API, Payments API, Modifications API, Reports API (CSV), Transfers API (balance platform), Adyen for Platforms (marketplace splits), Webhooks (HMAC-SHA256 signed). Production scope: payments authorization/capture/refund, payouts, account holders for marketplace, balance transfer.

## 2. Inbound + Outbound Capabilities

**Outbound:**
* `/payments` create, `/payments/details` resolve.
* `/payments/{id}/captures`, `/refunds`, `/reversals`.
* Transfers API for balance moves.
* Account holder create/update (marketplace) — gated by RFM.

**Inbound:**
* Webhook receiver with HMAC and additional `Adyen-Signature` HTTP header.
* Reports API daily-fetch (CSV) for reconciliation.

## 3. Auth + Identity

* API key per merchant account vaulted at `wg-sec-vault://adyen/<merchant>/api-key`.
* HMAC secret for webhooks vaulted separately.
* Client-side encryption keys (CSE) for Drop-in / Components — adapter never handles raw card data.
* Quantum lock: ML-KEM-1024 wrap, ML-DSA-65 dual-sign.
* mTLS to `*.adyen.com` egress allowlist.

## 4. Schema Mapping

| Adyen Object         | ADAM Canonical                  | Notes                          |
|----------------------|---------------------------------|--------------------------------|
| `Payment`            | `treasury.payment_intent`       | PCI-token only                 |
| `Capture`            | `treasury.charge`               |                                |
| `Refund`             | `treasury.refund`               |                                |
| `Reversal`           | `treasury.reversal`             |                                |
| `Transfer`           | `treasury.transfer`             |                                |
| `AccountHolder`      | `marketplace.account_holder`    | KYC-bearing                    |
| `BalanceAccount`     | `marketplace.balance_account`   |                                |

## 5. Idempotency

* `Idempotency-Key` header on every POST (UUID v7); recorded in FR before send.
* Webhook dedup `(eventCode, pspReference)` 24 h.

## 6. Rate Limits

* Per-merchant TPS cap; contract `rate_ceiling_per_min` enforced in-process.
* Reports API daily; CSV pull windowed.

## 7. Error Handling

* `validation` (10*), `restriction` (11*), `acquirer` (8*) error classes mapped to canonical.
* `idempotency-conflict` halts verb chain and emits `idempotency.collision`.
* Webhook signature failure ⇒ `webhook.invalid_signature` event, never processed.

## 8. Residency

Adyen processing region pinned (EU, US, AU, IN). Cross-region forbidden without RFM. PII allowed; PCI-token only — raw PAN never accepted.

## 9. FR Events

```
adapter.adyen.payment.authorized / .captured / .refunded / .reversed
adapter.adyen.transfer.submitted / .completed
adapter.adyen.account_holder.created / .updated
adapter.adyen.webhook.received / .invalid_signature / .replayed
adapter.adyen.report.fetched
adapter.adyen.idempotency.collision
adapter.adyen.rate.pressure
```

## 10. Configuration Schema

```yaml
adapter_adyen:
  merchant_account: "<MerchantAcct>"
  endpoints:
    checkout: "https://checkout-live.adyen.com/v71"
    pal:      "https://pal-live.adyen.com"
    transfers:"https://balanceplatform-api-live.adyen.com"
  vault_handles:
    api_key: "wg-sec-vault://adyen/<merchant>/api-key"
    hmac:    "wg-sec-vault://adyen/<merchant>/hmac"
  webhook_url: "https://adam.<tenant>/adapters/adyen/webhook"
  contract_id: "adapter-adyen-contract"
```

## 11. Schemas Spoken

* Adyen Checkout v71 REST (JSON).
* Adyen Webhooks (HMAC-SHA256).
* Reports API CSV.
* Adyen Balance Platform API.

## 12. Day-1 PQC Posture

* Bus emissions: hybrid Ed25519 + ML-DSA-65.
* Adyen TLS: classical. `qsuite=classical-fallback` recorded.
* Webhook HMAC SHA-256 (vendor protocol); adapter re-signs onto bus.
* Vault wrap: ML-KEM-1024.

## 13. Resource Profile

CPU 1 vCPU / 3 burst, RAM 1 GB, Disk 10 GB, Net ≤200 Mbps.

## 14. Dependencies

`wg-sec-vault`, FR, `hi-intent`, `orch-policy`, `meta-stability`, `meta-integrity`, `wg-fin-txn`, `wg-fin-recon`, `adam-adapter-contract-sdk`.

## 15. SLOs

Auth p95 ≤ 800 ms; webhook p95 ≤ 200 ms; availability ≥ 99.95%; refusal p99 ≤ 30 ms.

## 16. Build Plan

1. Pre-Action Gate via SDK.
2. Vault-resident API key + HMAC.
3. Checkout v71 client with idempotency-key.
4. Webhook receiver with replay window + signature verify.
5. Reports API daily reconciliation job.
6. QA pass1..5 + 360.

## 17. Definition of Done

`qa_all` / `qa_360` / `qa_pass3..5` 100/100; contract lifecycle green; webhook negative test passes; reconciliation report green; `views_smoke` 70/70; index updated.

---

## 18. Contract Binding

* `contract_id`: `adapter-adyen-contract`
* `boss_score_floor`: **82** (canonical 0..100 BOSS scale; high financial materiality + PCI-token surface).
* `data_classes_allowed`: `pii`, `internal`, `restricted`, `pci-token`. Raw PAN forbidden.
* `egress_allowlist`: `*.adyen.com:443` (live endpoints only).
* `allowed_actions` (default): `payment.create`, `payment.capture`, `refund.create`, `reversal.create`, `transfer.create`, `webhook.receive`, `report.fetch`.
* `forbidden_actions`: `account_holder.create` (marketplace), `balance_account.create`, `payout.create`, `card.create_with_pan`, `merchant_account.modify`.

## 19. RFM Triggers

* Marketplace mode (account holders).
* New region.
* Lifting rate ceiling.
* New webhook endpoint.
* Crypto evolution.

## 20. Smart-Adapter Behaviors

* Refuses payloads containing raw `cardNumber`, `cvc`, `expiryMonth`/`expiryYear` outside Drop-in/Components flow.
* Validates Adyen HMAC + replay window 5 min.
* Daily reconciliation against Reports API; mismatches emit `recon.divergence`.
* Marketplace KYC outcomes never auto-published — they wait for `ga-legal` co-sign through Intent Object.
* Auto-RFM on Adyen API deprecation notices.

## 21. 360 QA Coverage

| Test ID                          | Pass | Outcome                                  |
|----------------------------------|------|------------------------------------------|
| adyen.contract.bind.happy        | 3    | Activates after dual-sign                |
| adyen.contract.refuse.pan        | 4    | Raw PAN refused                          |
| adyen.contract.refuse.marketplace| 4    | `account_holder.create` refused default  |
| adyen.contract.webhook.hmac      | 4    | Bad HMAC ⇒ `invalid_signature`           |
| adyen.contract.recon.divergence  | 5    | Daily recon flags divergence             |
| adyen.contract.rfm.region        | 5    | New region triggers RFM                  |
| adyen.contract.rate_ceiling      | 4    | In-process throttle holds                |
| adyen.contract.terminate         | 3    | Keys rotated; HMAC voided                |
