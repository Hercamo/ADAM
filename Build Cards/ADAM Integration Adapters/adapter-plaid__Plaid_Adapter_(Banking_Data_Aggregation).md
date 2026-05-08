# Plaid Adapter — Banking Data Aggregation (v0.3, Contract-Bound, Day-1 PQC)

**Card ID:** `adapter-plaid`
**Version:** v0.3 (contract-bound)
**Status:** build-ready
**Supersedes:** `adapter-plaid__Plaid_Adapter_(Banking_Data_Aggregation).docx.BAK` (v0.2 — retained as old version)
**Contract pattern:** `_CONTRACT_SPEC.md`
**Used By:** `adamplus-fin-treasury`, `adamplus-ar-credit`, `wg-fin-recon`, `wg-fin-audit`, `wg-data-pii`

---

## 1. Target System

Plaid Link + Plaid API (Auth, Transactions, Identity, Balance, Assets, Income, Investments, Liabilities, Transfer, Signal). Webhooks for product readiness + transaction updates. Production scope: read-only aggregation of bank accounts the end-user has explicitly linked. Plaid Transfer requires RFM (it moves money).

## 2. Inbound + Outbound Capabilities

**Outbound:**
* `link/token/create` (Link initialization).
* `item/public_token/exchange` → access_token (vaulted).
* `transactions/sync`, `auth/get`, `identity/get`, `balance/get`, `liabilities/get`, `investments/holdings/get`.
* `signal/evaluate` for ACH risk scoring.
* `transfer/create` (only if `transfer` scope in contract).

**Inbound:**
* Webhook receiver with JWT-signed payloads (Plaid `Plaid-Verification` header).

## 3. Auth + Identity

* `client_id` + `secret` per environment, vaulted at `wg-sec-vault://plaid/<env>/secret`.
* Per-Item `access_token` vaulted with end-user binding label.
* Webhook JWT public key fetched from Plaid `webhook_verification_key/get`, cached and rotated.
* Quantum lock: ML-KEM-1024 wrap, ML-DSA-65 dual-sign.
* mTLS to `production.plaid.com` (or `sandbox.plaid.com` in dev).

## 4. Schema Mapping

| Plaid Object       | ADAM Canonical                  | Notes                              |
|--------------------|---------------------------------|------------------------------------|
| `Item`             | `banking.linked_item`           | Per end-user link                  |
| `Account`          | `banking.account`               | Masked routing/account             |
| `Transaction`      | `banking.transaction`           | PII + financial                    |
| `Identity`         | `banking.identity`              | PII                                |
| `Balance`          | `banking.balance`               |                                    |
| `Liability`        | `banking.liability`             |                                    |
| `Holding`          | `banking.holding`               |                                    |
| `Transfer`         | `treasury.transfer.ach`         | Money-moving; RFM-gated            |

## 5. Idempotency

* Outbound: client-generated `idempotency_key` for endpoints that accept one (e.g., transfers); recorded in FR.
* Webhook dedup `(item_id, webhook_type, webhook_code, environment, sequence)` 24 h.
* `transactions/sync` uses opaque cursor persisted to FR; never reprocess past cursor.

## 6. Rate Limits

* Plaid per-Item rate ceilings; in-process `rate_ceiling_per_min` honored.
* Bulk historical pull throttled to avoid bank-source backpressure.

## 7. Error Handling

* `ITEM_LOGIN_REQUIRED` → emit `consent.expired` event; do not retry; surface to user via owning agent.
* `RATE_LIMIT_EXCEEDED` → backoff.
* `INVALID_INPUT` → DLQ + auto-RFM if recurring (schema drift).

## 8. Residency

US/CA/EU per environment; contract pins. PII + PCI (account number) classes required for Auth product; cross-residency forbidden.

## 9. FR Events

```
adapter.plaid.item.linked / .updated / .removed
adapter.plaid.transactions.sync.cursor_advanced
adapter.plaid.identity.fetched
adapter.plaid.balance.fetched
adapter.plaid.liabilities.fetched
adapter.plaid.investments.holdings.fetched
adapter.plaid.transfer.created       (only if scope)
adapter.plaid.webhook.received / .invalid_signature
adapter.plaid.consent.expired
adapter.plaid.rate.pressure
```

## 10. Configuration Schema

```yaml
adapter_plaid:
  environment: "production"
  endpoints:
    api: "https://production.plaid.com"
  vault_handle: "wg-sec-vault://plaid/production/secret"
  products: ["transactions", "auth", "identity", "balance"]
  webhook_url: "https://adam.<tenant>/adapters/plaid/webhook"
  contract_id: "adapter-plaid-contract"
```

## 11. Schemas Spoken

* Plaid REST (JSON).
* Plaid Webhooks (JWT-signed).
* Plaid Link initialization.

## 12. Day-1 PQC Posture

* Bus emissions: hybrid Ed25519 + ML-DSA-65.
* Plaid TLS: classical. `qsuite=classical-fallback` recorded.
* Webhook JWT: ES256 (vendor protocol); adapter re-signs to bus.
* Vault wrap: ML-KEM-1024.

## 13. Resource Profile

CPU 1 vCPU / 3 burst, RAM 1 GB, Disk 10 GB, Net ≤200 Mbps.

## 14. Dependencies

`wg-sec-vault`, FR, `hi-intent`, `orch-policy`, `meta-stability`, `meta-integrity`, `wg-data-pii`, `wg-fin-recon`, `adam-adapter-contract-sdk`.

## 15. SLOs

Sync read p95 ≤ 1.0 s; webhook p95 ≤ 200 ms; availability ≥ 99.9%; refusal p99 ≤ 30 ms.

## 16. Build Plan

1. Pre-Action Gate via SDK.
2. Link initialization endpoint (server-side `link/token/create`).
3. Item lifecycle (exchange + vault binding).
4. `transactions/sync` cursor management in FR.
5. Webhook receiver with JWT verification.
6. Consent state machine with explicit user re-auth flow.
7. QA pass1..5 + 360.

## 17. Definition of Done

`qa_all` / `qa_360` / `qa_pass3..5` 100/100; contract lifecycle green; consent expiry path verified; cursor never replays; `views_smoke` 70/70.

---

## 18. Contract Binding

* `contract_id`: `adapter-plaid-contract`
* `boss_score_floor`: **85** (high PII + financial + consent surface; canonical 0..100 BOSS scale).
* `data_classes_allowed`: `pii`, `pci`, `internal`, `restricted`. PHI forbidden.
* `egress_allowlist`: `production.plaid.com:443` (or sandbox in dev only).
* `allowed_actions` (default): `link_token.create`, `item.exchange`, `transactions.sync`, `auth.get`, `identity.get`, `balance.get`, `liabilities.get`, `investments.holdings.get`, `signal.evaluate`, `webhook.receive`.
* `forbidden_actions`: `transfer.create`, `transfer.cancel`, `processor_token.create`, `assets.report.create` (until addendum), `bank_transfer.*` (deprecated path).

## 19. RFM Triggers

* Adding `transfer` product (money-moving).
* Adding new region.
* New product class (e.g., Income, Assets).
* Crypto evolution.

## 20. Smart-Adapter Behaviors

* Treats every `Item` as scoped to the end-user identity that linked it; refuses cross-user reads.
* On `ITEM_LOGIN_REQUIRED`, halts that Item, emits `consent.expired`, and queues a re-link prompt; never retries silently.
* Verifies webhook JWT signature against current Plaid public-key set; rotates cached set on any mismatch.
* Cursor for `transactions/sync` is FR-anchored; on restart, never replays committed transactions.
* Refuses to log full account numbers — masks to last 4 in events; full digits live only in vault-bound payload.

## 21. 360 QA Coverage

| Test ID                          | Pass | Outcome                                |
|----------------------------------|------|----------------------------------------|
| plaid.contract.bind.happy        | 3    | Activates after dual-sign              |
| plaid.contract.refuse.transfer   | 4    | `transfer.create` refused default      |
| plaid.contract.consent.expired   | 4    | Item halts + `consent.expired` emitted |
| plaid.contract.cursor.no_replay  | 4    | Restart resumes from FR cursor         |
| plaid.contract.webhook.jwt       | 4    | Bad JWT ⇒ `invalid_signature`          |
| plaid.contract.rfm.transfer      | 5    | Adding transfer product runs RFM       |
| plaid.contract.cross_user        | 4    | Cross-user read refused                |
| plaid.contract.terminate         | 3    | Tokens revoked; vault keys rotated     |
