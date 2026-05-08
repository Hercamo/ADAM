# FIX Protocol Adapter — Trading (v0.3, Contract-Bound, Day-1 PQC)

**Card ID:** `adapter-fix`
**Version:** v0.3 (contract-bound)
**Status:** build-ready
**Supersedes:** `adapter-fix__FIX_Protocol_Adapter_(Trading).docx.BAK` (v0.2 — retained as old version)
**Contract pattern:** `_CONTRACT_SPEC.md`
**Used By:** `wg-fin-txn`, `wg-fin-recon`, `wg-fin-audit`, `adamplus-fin-treasury`, `adamplus-fin-fx`, `adamplus-ops-trading`, `wg-risk-monitor`, `wg-gov-filing`

---

## 1. Target System

FIX 4.4 / FIX 5.0 SP2 / FIXT.1.1 sessions over TCP+TLS, with optional FAST encoding for market data. Counterparties: brokers, ECNs, exchanges. Production scope: order entry (NewOrderSingle), cancel/replace, executions, market-data subscriptions (limited), drop copy. Algos and SOR routing logic live elsewhere — this adapter is a session+wire bridge.

## 2. Inbound + Outbound Capabilities

**Outbound:** `D` NewOrderSingle, `F` OrderCancelRequest, `G` OrderCancelReplaceRequest, `AB` NewOrderMultileg, `AF` OrderMassStatusRequest, `MarketDataRequest` (V).
**Inbound:** `8` ExecutionReport (executions, acks, rejects, cancels), `9` OrderCancelReject, `W`/`X` MarketData snapshot/incremental, drop-copy reports.

## 3. Auth + Identity

FIX session-level authentication via `Username`/`Password` (Logon 35=A) + mTLS to counterparty endpoint. SenderCompID/TargetCompID pinned per session. Per-session SSL identity vaulted at `wg-sec-vault://fix/<sender>/<target>/cert`. Logon credentials rotated per counterparty schedule. Quantum lock: ML-KEM-1024 wrap, ML-DSA-65 dual-sign.

## 4. Schema Mapping

| FIX Concept              | ADAM Canonical                  |
|--------------------------|---------------------------------|
| `NewOrderSingle` (`D`)   | `trading.order.new`             |
| `OrderCancelRequest`(`F`)| `trading.order.cancel`          |
| `OrderCancelReplace`(`G`)| `trading.order.replace`         |
| `ExecutionReport`(`8`)   | `trading.execution`             |
| `OrderCancelReject`(`9`) | `trading.order.cancel_reject`   |
| `MarketData` (`W`/`X`)   | `trading.marketdata.<symbol>`   |
| Drop copy report         | `trading.dropcopy.execution`    |

## 5. Idempotency

* `ClOrdID` (UUID v7-derived) per order; FR pre-write before send.
* Sequence-number-based replay-safe via FIX `34` MsgSeqNum + persistent session log.
* `OrigClOrdID` chains tracked for cancel/replace stories.

## 6. Rate Limits

Per-counterparty TPS limits enforced 80%; market-data subscriptions windowed by symbol set.

## 7. Error Handling

`SessionLevelReject` (`3`) ⇒ canonical `protocol.reject`. `BusinessMessageReject` (`j`) ⇒ canonical `business.reject`. Dropped session ⇒ FIX heartbeat watchdog + automatic resend with proper SeqNum reset only after Intent Object approval.

## 8. Residency

Per-counterparty colo / region pinned. Cross-region sessions never share state. Non-clearing data classes only — adapter handles trade order PII (account number masked) but not customer PII broadly.

## 9. FR Events

```
adapter.fix.session.logon.ok / .reject
adapter.fix.session.logout
adapter.fix.session.gap.detected / .resend.requested
adapter.fix.order.new.sent / .acked
adapter.fix.order.cancel.sent / .acked / .reject
adapter.fix.order.replace.sent / .acked / .reject
adapter.fix.execution.received
adapter.fix.marketdata.received
adapter.fix.dropcopy.received
adapter.fix.heartbeat.missed
adapter.fix.protocol.reject
adapter.fix.business.reject
```

## 10. Configuration Schema

```yaml
adapter_fix:
  sessions:
    - session_id: "ME-FIX-1"
      sender_comp_id: "ADAMME"
      target_comp_id: "BROKER1"
      host: "fix.broker1.example:9876"
      protocol: "FIX.4.4"
      tls: true
      vault_handle: "wg-sec-vault://fix/ADAMME/BROKER1/cert"
      heartbeat_int: 30
  contract_id: "adapter-fix-contract"
```

## 11. Schemas Spoken

FIX 4.4, FIX 5.0 SP2, FIXT.1.1, FIX FAST encoding (optional), FIX session protocol with mTLS.

## 12. Day-1 PQC Posture

Bus hybrid Ed25519 + ML-DSA-65. FIX TLS: classical (counterparty-controlled); `qsuite=classical-fallback`. Vault wrap ML-KEM-1024. Hybrid PQC for FIX requires counterparty support; tracked.

## 13. Resource Profile

CPU 2 / 6 burst, RAM 2 GB / 6 burst, Disk 50 GB (session log), Net ≤500 Mbps low-latency.

## 14. Dependencies

`wg-sec-vault`, FR, `hi-intent`, `orch-policy`, `meta-stability`, `meta-integrity`, `wg-fin-txn`, `wg-risk-monitor`, `adam-adapter-contract-sdk`.

## 15. SLOs

NewOrderSingle wire latency p95 ≤ 5 ms in-DC; ExecutionReport ingestion p95 ≤ 5 ms; session uptime ≥ 99.99% during market hours; refusal p99 ≤ 1 ms (must be cheap on the hot path).

## 16. Build Plan

1. Pre-Action Gate via SDK with hot-path-optimized refusal.
2. FIX session library (engine) with persistent SeqNum store.
3. mTLS with vault-bound certs.
4. Pre-trade risk gate hook (delegates to `wg-risk-monitor`).
5. Drop-copy reconciliation pipeline.
6. Gap recovery state machine.
7. QA pass1..5 + 360.

## 17. Definition of Done

`qa_all` / `qa_360` / `qa_pass3..5` 100/100; contract lifecycle green; gap-recovery negative test passes; SeqNum-reset RFM path verified; `views_smoke` 70/70.

---

## 18. Contract Binding

* `contract_id`: `adapter-fix-contract`
* `boss_score_floor`: **92** (trading materiality + irreversibility; canonical 0..100 BOSS scale).
* `data_classes_allowed`: `internal`, `restricted`, `pci-token` (account refs). PII limited.
* `egress_allowlist`: per-counterparty static IPs on FIX session ports (typical `<ip>:9876` to `<ip>:9999`), enumerated per session in the per-deployment addendum; no DNS resolution permitted.
* `allowed_actions` (default): `session.logon`, `session.logout`, `order.new`, `order.cancel`, `order.replace`, `marketdata.subscribe`, `marketdata.unsubscribe`, `dropcopy.consume`.
* `forbidden_actions`: `seqnum.reset.unilateral`, `session.disable_tls`, `counterparty.add`, `mass_cancel.unbounded` (mass cancel requires per-event Intent Object), `algo.publish` (out-of-scope).

## 19. RFM Triggers

* New counterparty session.
* Sequence-number reset (any).
* Mass cancel.
* New FIX dialect / message type.
* Crypto evolution.

## 20. Smart-Adapter Behaviors

* Pre-trade risk check on every NewOrderSingle: notional + symbol + position-delta vs `wg-risk-monitor` limit set; refuses if breach.
* SeqNum gap detected ⇒ resend request per protocol; SeqNum reset (35=4 with 123=Y or 35=A with 141=Y) requires fresh Intent Object — never unilateral.
* Heartbeat watchdog: missed `n*HeartBtInt` triggers session pause + alert; never silently re-establishes session under stress.
* Drop-copy reconciliation against primary execution stream; mismatch raises `recon.divergence`.
* Refuses orders that exceed contract-listed venues even if upstream caller targets them.

## 21. 360 QA Coverage

| Test ID                          | Pass | Outcome                                       |
|----------------------------------|------|-----------------------------------------------|
| fix.contract.bind.happy          | 3    | Activates after dual-sign                     |
| fix.contract.refuse.seq_reset    | 4    | Unilateral SeqNum reset refused               |
| fix.contract.refuse.mass_cancel  | 4    | Mass cancel without Intent Object refused     |
| fix.contract.risk.breach         | 4    | Order breaching risk limit refused            |
| fix.contract.gap.recover         | 4    | Gap recovery via resend works                 |
| fix.contract.dropcopy.recon      | 5    | Recon flags divergence                        |
| fix.contract.rfm.cpty_add        | 5    | New counterparty triggers RFM                 |
| fix.contract.terminate           | 3    | Sessions logged out cleanly; certs rotated    |
