# NetStreamX Media CMS Adapter (v0.3, Contract-Bound, Day-1 PQC)

**Card ID:** `adapter-netstreamx-cms`
**Version:** v0.3 (contract-bound)
**Status:** build-ready
**Supersedes:** `adapter-netstreamx-cms__NetStreamX_Media_CMS_Adapter.docx.BAK` (v0.2 — retained as old version)
**Contract pattern:** `_CONTRACT_SPEC.md`
**Used By:** `wg-market-customer`, `wg-market-demand`, `wg-market-reputation`, `adamplus-ops-content-catalog`, `adamplus-ops-streaming`, `adamplus-ops-subscription`, `ai-data-pipeline`, `ai-external-stakeholder`, `wg-data-rights`. UI surface: NetStreamX Directors Dashboard (not an agent ID — listed for routing context).

---

## 1. Target System

NetStreamX Media CMS (the customer-facing back-end this ADAM instance fronts). Surfaces: NetStreamX Public REST API, internal bus events, SQLite root DB (read-only contract surface for ADAM), Director-facing endpoints, LIVE/DEMO toggle. Production scope: titles, episodes, assets, rights/licensing windows, viewer events, billing events. Out of scope by default: schema migrations on the customer DB and any write to the LIVE/DEMO toggle.

## 2. Inbound + Outbound Capabilities

**Outbound:** Publish title metadata, ingest viewer event normalizers, post director-dashboard sync events, write rights/license records (RFM-gated for new license types).

**Inbound:** Viewer events stream, billing events stream, content-state changes, customer-facing page events, director-action events.

## 3. Auth + Identity

mTLS to NetStreamX internal endpoints; service identity issued by `wg-sec-vault`. The customer-facing back-end and ADAM are co-resident on the same physical server, so adapter uses Unix-domain sockets where possible plus loopback mTLS for processes that require TCP. Vault handle: `wg-sec-vault://netstreamx/cms/svc-cert`. Quantum lock: ML-KEM-1024 wrap, ML-DSA-65 dual-sign on bus.

## 4. Schema Mapping

| NetStreamX Object   | ADAM Canonical                |
|---------------------|-------------------------------|
| `Title`             | `media.title`                 |
| `Episode`           | `media.episode`               |
| `Asset` (video)     | `media.asset`                 |
| `RightsWindow`      | `media.rights_window`         |
| `ViewerEvent`       | `bus.event.netstreamx.viewer` |
| `BillingEvent`      | `bus.event.netstreamx.billing`|
| `DirectorAction`    | `bus.event.netstreamx.director`|

## 5. Idempotency

* Outbound: `Idempotency-Key` (UUID v7) recorded in FR.
* Inbound viewer events: dedup `(session_id, sequence)` 24 h.
* Director actions: action id is FR-anchored; replay is refused.

## 6. Rate Limits

Set per environment (LIVE vs DEMO); LIVE has tighter ceilings and contract enforces them; DEMO permits burst for synthetic load tests.

## 7. Error Handling

`ContentLockedException`, `RightsWindowExpired`, `BillingDeclined` are first-class events surfaced upward. Network errors retry with backoff; integrity errors never auto-retry.

## 8. Residency

Co-resident with the customer back-end on the physical sovereign server. Cross-host replication forbidden; off-host egress refused at CNI level.

## 9. FR Events

```
adapter.netstreamx.title.upsert.ok / .failed
adapter.netstreamx.episode.upsert.ok
adapter.netstreamx.asset.upsert.ok
adapter.netstreamx.rights_window.created
adapter.netstreamx.viewer.event.received
adapter.netstreamx.billing.event.received
adapter.netstreamx.director.action.received
adapter.netstreamx.live_demo.toggle.refused
adapter.netstreamx.schema.drift.detected
adapter.netstreamx.rate.pressure
```

## 10. Configuration Schema

```yaml
adapter_netstreamx_cms:
  endpoints:
    api:        "unix:///var/run/netstreamx/cms.sock"
    api_tcp:    "https://localhost:8443"
  vault_handle: "wg-sec-vault://netstreamx/cms/svc-cert"
  environment: "LIVE"   # LIVE | DEMO
  topics:
    - "viewer.event"
    - "billing.event"
    - "director.action"
  contract_id: "adapter-netstreamx-cms-contract"
```

## 11. Schemas Spoken

NetStreamX REST (JSON), internal bus event envelopes, SQLite read-only views.

## 12. Day-1 PQC Posture

Bus: hybrid Ed25519 + ML-DSA-65. Internal mTLS hybrid X25519 + ML-KEM-768 supported (co-resident, fully PQC). Vault wrap ML-KEM-1024. This adapter is the **first** to run hybrid PQC end-to-end because the peer is sovereign.

## 13. Resource Profile

CPU 1 / 3 burst, RAM 1 GB / 3 burst, Disk 20 GB (event archive), Net loopback only.

## 14. Dependencies

`wg-sec-vault`, FR, `hi-intent`, `orch-policy`, `meta-stability`, `meta-integrity`, `wg-data-rights`, `adam-adapter-contract-sdk`, NetStreamX customer app, Directors Dashboard.

## 15. SLOs

Title write p95 ≤ 200 ms (loopback); event ingestion p95 ≤ 50 ms; availability ≥ 99.99% (sovereign host); refusal p99 ≤ 20 ms.

## 16. Build Plan

1. Pre-Action Gate via SDK.
2. UDS + loopback mTLS.
3. Bus event subscriber with FR checkpoint.
4. Director-action verifier (role-aware, idempotent).
5. Rights-window engine with expiry alerts.
6. Hybrid PQC mTLS suites enabled and exercised.
7. QA pass1..5 + 360.

## 17. Definition of Done

`qa_all` / `qa_360` / `qa_pass3..5` 100/100; contract lifecycle green; LIVE/DEMO toggle refusal verified; hybrid PQC suites verified; `views_smoke` 70/70.

---

## 18. Contract Binding

* `contract_id`: `adapter-netstreamx-cms-contract`
* `boss_score_floor`: **85** (sovereign customer-facing surface; canonical 0..100 BOSS scale).
* `data_classes_allowed`: `pii`, `internal`, `restricted`. PCI handled only by `adapter-stripe`/`adapter-adyen` — NetStreamX adapter never touches payment instruments.
* `egress_allowlist`: loopback only (`127.0.0.1`, `::1`, UDS).
* `allowed_actions` (default): `title.upsert`, `episode.upsert`, `asset.upsert`, `rights_window.create`, `viewer.event.consume`, `billing.event.consume`, `director.action.consume`, `dashboard.sync`.
* `forbidden_actions`: `live_demo.toggle.write`, `db.schema.migrate`, `customer_app.config.write`, `cms.user.create`.

## 19. RFM Triggers

* New rights/license type.
* New environment (e.g., STAGING beyond LIVE/DEMO).
* Crypto suite evolution (already hybrid PQC; future negotiation policy changes still need RFM).
* New event topic.

## 20. Smart-Adapter Behaviors

* Refuses to write the LIVE/DEMO toggle. Even with contract amendment, this is human-only via Directors Dashboard.
* Detects rights-window expiry and emits `rights.expiry.imminent` 7 days ahead.
* Reconciles emitted billing events against `adapter-stripe`/`adapter-adyen` `treasury.charge` events daily; mismatch ⇒ `recon.divergence`.
* For director-action consumption, verifies the action's signer chain belongs to the role permitted in the contract addendum.

## 21. 360 QA Coverage

| Test ID                              | Pass | Outcome                                       |
|--------------------------------------|------|-----------------------------------------------|
| nsx.contract.bind.happy              | 3    | Activates after dual-sign                     |
| nsx.contract.refuse.toggle           | 4    | LIVE/DEMO toggle write refused                |
| nsx.contract.refuse.egress           | 4    | Off-loopback egress refused at CNI            |
| nsx.contract.recon.billing           | 5    | Recon flags injected mismatch with payments   |
| nsx.contract.rfm.rights              | 5    | New license type triggers RFM                 |
| nsx.contract.pqc.hybrid              | 4    | mTLS handshake verified hybrid PQC            |
| nsx.contract.director.signer         | 4    | Bad signer chain refused                      |
| nsx.contract.terminate               | 3    | Sovereign cleanup; vault rotated              |
