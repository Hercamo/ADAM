# Zendesk Support Adapter (v0.3, Contract-Bound, Day-1 PQC)

**Card ID:** `adapter-zendesk`
**Version:** v0.3 (contract-bound)
**Status:** build-ready
**Supersedes:** `adapter-zendesk__Zendesk_Support_Adapter.docx.BAK` (v0.2 — retained as old version)
**Contract pattern:** `_CONTRACT_SPEC.md`
**Used By:** `wg-market-customer`, `wg-market-reputation`, `wg-ops-translate`, `wg-data-quality`, `adamplus-crm-cases`, `adamplus-itsm-incident`, `ai-external-stakeholder`

---

## 1. Target System

Zendesk Support, Guide (knowledge base), Talk (voice — excluded by default), Chat. Surfaces: Zendesk REST API v2, Webhooks (signed `X-Zendesk-Webhook-Signature`), Triggers and Automations (read-only by default), Sunshine Conversations.

## 2. Inbound + Outbound Capabilities

**Outbound:** Ticket create/update/comment, user upsert, organization upsert, KB article publish (RFM-gated), macro execution (default forbidden).
**Inbound:** Webhook events, ticket export jobs, comment events, satisfaction survey results.

## 3. Auth + Identity

OAuth 2.0 service app or API token + email vaulted at `wg-sec-vault://zendesk/<subdomain>/api-token`. Webhook signing key separately vaulted. mTLS to `<subdomain>.zendesk.com`. Quantum lock: ML-KEM-1024 wrap, ML-DSA-65 dual-sign.

## 4. Schema Mapping

| Zendesk Object   | ADAM Canonical                |
|------------------|-------------------------------|
| `Ticket`         | `service.case`                |
| `Comment`        | `service.case.comment`        |
| `User`           | `customer.person`             |
| `Organization`   | `customer.organization`       |
| `Article` (Guide)| `kb.article`                  |
| `Webhook event`  | `bus.event.zendesk.<type>`    |

## 5. Idempotency

* Outbound: `Idempotency-Key` (where supported) + `external_id` field on tickets/users; FR pre-write.
* Webhook dedup `(event_id)` 24 h.

## 6. Rate Limits

Zendesk per-tenant + per-endpoint enforced 80%. Ticket export uses incremental cursor.

## 7. Error Handling

`422 Validation` ⇒ DLQ + auto-RFM if recurring. `403 InvalidPermission` ⇒ self-suspend. `429` ⇒ backoff.

## 8. Residency

Per Zendesk pod (US, EU, AU). Cross-pod forbidden without RFM. PII allowed; PCI/PHI by addendum.

## 9. FR Events

```
adapter.zendesk.ticket.create / .update / .close
adapter.zendesk.ticket.comment.added
adapter.zendesk.user.upsert
adapter.zendesk.org.upsert
adapter.zendesk.kb.article.upsert
adapter.zendesk.satisfaction.received
adapter.zendesk.webhook.received / .invalid_signature
adapter.zendesk.export.cursor.advanced
adapter.zendesk.schema.drift.detected
adapter.zendesk.rate.pressure
```

## 10. Configuration Schema

```yaml
adapter_zendesk:
  subdomain: "<sub>"
  base_url: "https://<sub>.zendesk.com"
  vault_handles:
    api: "wg-sec-vault://zendesk/<sub>/api-token"
    webhook: "wg-sec-vault://zendesk/<sub>/webhook"
  webhook_url: "https://adam.<tenant>/adapters/zendesk/webhook"
  contract_id: "adapter-zendesk-contract"
```

## 11. Schemas Spoken

Zendesk REST v2 (JSON), Zendesk Webhooks (HMAC-SHA256), Incremental Export API, Sunshine Conversations API.

## 12. Day-1 PQC Posture

Bus hybrid Ed25519 + ML-DSA-65. Zendesk TLS classical; `qsuite=classical-fallback`. Vault wrap ML-KEM-1024.

## 13. Resource Profile

CPU 1 / 3 burst, RAM 1 GB, Disk 20 GB (export staging), Net ≤200 Mbps.

## 14. Dependencies

`wg-sec-vault`, FR, `hi-intent`, `orch-policy`, `meta-stability`, `meta-integrity`, `wg-data-pii`, `adam-adapter-contract-sdk`.

## 15. SLOs

Ticket write p95 ≤ 800 ms; webhook p95 ≤ 200 ms; availability ≥ 99.9%; refusal p99 ≤ 30 ms.

## 16. Build Plan

1. Pre-Action Gate via SDK.
2. REST client with `external_id` + idempotency.
3. Webhook receiver with HMAC.
4. Incremental export cursor in FR.
5. Schema-drift detector on ticket fields.
6. Permission attestation on each restart.
7. QA pass1..5 + 360.

## 17. Definition of Done

`qa_all` / `qa_360` / `qa_pass3..5` 100/100; contract lifecycle green; webhook negative test passes; `views_smoke` 70/70.

---

## 18. Contract Binding

* `contract_id`: `adapter-zendesk-contract`
* `boss_score_floor`: **74** (canonical 0..100 BOSS scale; PII via support cases).
* `data_classes_allowed`: `pii`, `internal`, `restricted`. PCI/PHI by addendum.
* `egress_allowlist`: `<sub>.zendesk.com:443`, `*.zendesk.com:443`.
* `allowed_actions` (default): `ticket.create`, `ticket.update`, `ticket.comment.add`, `user.upsert`, `org.upsert`, `kb.article.read`, `webhook.receive`, `export.cursor`, `satisfaction.consume`.
* `forbidden_actions`: `macro.execute`, `trigger.create`, `automation.create`, `app.install`, `permission.modify`, `kb.article.publish` (default forbidden until addendum).

## 19. RFM Triggers

* New custom field on tickets.
* New trigger/automation integration.
* New pod.
* PCI/PHI addendum.
* Crypto evolution.

## 20. Smart-Adapter Behaviors

* Mirrors ticket state into `service.case` canonical and reconciles for drift.
* Refuses to expose customer-internal-only ticket comments outside ADAM trust boundary.
* Detects schema delta on Zendesk ticket fields via metadata.
* Permission attestation on each restart.
* On webhook event for `user.merge`, broadcasts identity-merge to other adapters that hold the merged user's keys.

## 21. 360 QA Coverage

| Test ID                          | Pass | Outcome                                       |
|----------------------------------|------|-----------------------------------------------|
| zd.contract.bind.happy           | 3    | Activates after dual-sign                     |
| zd.contract.refuse.macro         | 4    | Macro execution refused                       |
| zd.contract.refuse.kb_publish    | 4    | KB publish refused default                    |
| zd.contract.user.merge.cascade   | 4    | Identity merge propagates                     |
| zd.contract.webhook.hmac         | 4    | Bad HMAC ⇒ `invalid_signature`                |
| zd.contract.rfm.custom_field     | 5    | New custom field triggers RFM                 |
| zd.contract.schema_drift         | 5    | Auto-RFM on field schema delta                |
| zd.contract.terminate            | 3    | API token revoked; webhook secret void        |
