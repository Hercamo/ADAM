# HubSpot Adapter — Marketing + CRM (v0.3, Contract-Bound, Day-1 PQC)

**Card ID:** `adapter-hubspot`
**Version:** v0.3 (contract-bound)
**Status:** build-ready
**Supersedes:** `adapter-hubspot__HubSpot_Adapter_(Marketing_+_CRM).docx.BAK` (v0.2 — retained as old version)
**Contract pattern:** `_CONTRACT_SPEC.md`
**Used By:** `wg-market-customer`, `wg-market-demand`, `wg-market-reputation`, `adamplus-crm-360`, `adamplus-crm-lead`, `adamplus-crm-pipeline`, `adamplus-crm-success`, `adamplus-crm-cases`, `ai-external-stakeholder`

---

## 1. Target System

HubSpot CRM, Marketing Hub, Service Hub. APIs: CRM v3 (Objects, Properties, Pipelines, Associations), Marketing v3 (Forms, Campaigns, Emails, Lists), Webhooks v3, Custom Code in Workflows (excluded by default), Files API. Production scope: contacts, companies, deals, tickets, marketing lists, campaigns, forms.

## 2. Inbound + Outbound Capabilities

**Outbound:** Object create/update/delete, batch upsert via `/batch/upsert`, list membership management, form submissions (server-side), property creation (RFM-gated).

**Inbound:** Webhook receiver (HMAC-SHA256), CRM Search polls for delta windows, list change notifications.

## 3. Auth + Identity

Private App access tokens per portal, vaulted at `wg-sec-vault://hubspot/<portal>/access-token`. Webhook signing secret separately vaulted. mTLS to `*.hubapi.com`. Quantum lock: ML-KEM-1024 wrap, ML-DSA-65 dual-sign.

## 4. Schema Mapping

| HubSpot Object | ADAM Canonical               | Notes                          |
|----------------|------------------------------|--------------------------------|
| `contacts`     | `customer.person`            | PII; consent properties mirrored |
| `companies`    | `customer.organization`      |                                |
| `deals`        | `pipeline.opportunity`       |                                |
| `tickets`      | `service.case`               |                                |
| `lists`        | `marketing.list`             |                                |
| `campaigns`    | `marketing.campaign`         |                                |
| `forms`        | `marketing.form`             |                                |
| custom objects | namespace `hubspot.<custom>` | Per-portal addendum            |

## 5. Idempotency

* Custom property `adam_idem` (UUID v7) on every upsert; FR pre-write.
* Webhook dedup `(subscriptionType, objectId, eventId)` 24 h.

## 6. Rate Limits

HubSpot per-app daily + per-second; contract enforces 80%. Search API stricter; honored separately.

## 7. Error Handling

`VALIDATION_ERROR` → DLQ + auto-RFM if recurring schema-shape change. `RATE_LIMIT` → backoff. `OAUTH_TOKEN_EXPIRED` → vault refresh; on persistent fail, self-suspend.

## 8. Residency

HubSpot data center pinned (US/EU). Cross-residency forbidden without RFM.

## 9. FR Events

```
adapter.hubspot.contact.upsert.ok / .failed
adapter.hubspot.company.upsert.ok
adapter.hubspot.deal.upsert.ok
adapter.hubspot.ticket.upsert.ok
adapter.hubspot.list.member.added / .removed
adapter.hubspot.form.submitted
adapter.hubspot.webhook.received / .invalid_signature / .replayed
adapter.hubspot.schema.drift.detected
adapter.hubspot.rate.pressure
```

## 10. Configuration Schema

```yaml
adapter_hubspot:
  portal_id: <int>
  endpoints:
    api: "https://api.hubapi.com"
  vault_handles:
    token: "wg-sec-vault://hubspot/<portal>/access-token"
    webhook: "wg-sec-vault://hubspot/<portal>/webhook-secret"
  webhook_url: "https://adam.<tenant>/adapters/hubspot/webhook"
  contract_id: "adapter-hubspot-contract"
```

## 11. Schemas Spoken

CRM v3 REST, Marketing v3 REST, Webhooks v3 (HMAC-SHA256), Files API.

## 12. Day-1 PQC Posture

Bus: hybrid Ed25519 + ML-DSA-65. HubSpot TLS classical; `qsuite=classical-fallback`. Vault wrap ML-KEM-1024.

## 13. Resource Profile

CPU 1 / 3 burst, RAM 1 GB, Disk 10 GB, Net ≤200 Mbps.

## 14. Dependencies

`wg-sec-vault`, FR, `hi-intent`, `orch-policy`, `meta-stability`, `meta-integrity`, `wg-data-pii`, `adam-adapter-contract-sdk`.

## 15. SLOs

Object write p95 ≤ 800 ms; webhook p95 ≤ 200 ms; availability ≥ 99.9%; refusal p99 ≤ 30 ms.

## 16. Build Plan

1. Pre-Action Gate via SDK.
2. Private App token issuance + vault binding.
3. CRM v3 client with batch upsert and idempotency property.
4. Webhook receiver with HMAC + replay window.
5. Schema-drift detector on object schemas.
6. QA pass1..5 + 360.

## 17. Definition of Done

`qa_all` / `qa_360` / `qa_pass3..5` 100/100; contract lifecycle green; webhook negative test passes; `views_smoke` 70/70.

---

## 18. Contract Binding

* `contract_id`: `adapter-hubspot-contract`
* `boss_score_floor`: **74** (canonical 0..100 BOSS scale; PII + marketing-consent surface).
* `data_classes_allowed`: `pii`, `internal`, `restricted`. No PCI/PHI.
* `egress_allowlist`: `*.hubapi.com:443`, `*.hubspot.com:443`.
* `allowed_actions` (default): `contact.upsert`, `company.upsert`, `deal.upsert`, `ticket.upsert`, `list.member.add`, `list.member.remove`, `form.submit.server`, `webhook.receive`, `search.query`.
* `forbidden_actions`: `property.create`, `pipeline.modify`, `workflow.execute`, `oauth.app.create`, `portal.config.write`.

## 19. RFM Triggers

* New custom object/property.
* Pipeline modification.
* New portal.
* Crypto evolution.

## 20. Smart-Adapter Behaviors

* Mirrors HubSpot consent properties (`hs_legal_basis`, `hs_marketable_status`) into every emitted event so downstream marketing agents respect consent state.
* Detects schema delta on object property metadata; auto-RFM filed.
* Refuses to add a contact to a list whose `legal_basis` is missing.
* On `OAUTH_TOKEN_EXPIRED`, attempts vault refresh once; on persistent fail, self-suspend + raise to `ga-security`.

## 21. 360 QA Coverage

| Test ID                          | Pass | Outcome                              |
|----------------------------------|------|--------------------------------------|
| hs.contract.bind.happy           | 3    | Activates after dual-sign            |
| hs.contract.refuse.no_consent    | 4    | List-add refused without legal basis |
| hs.contract.refuse.workflow      | 4    | Workflow execution refused           |
| hs.contract.webhook.hmac         | 4    | Bad HMAC ⇒ `invalid_signature`       |
| hs.contract.rfm.custom_property  | 5    | New property triggers RFM            |
| hs.contract.schema_drift         | 5    | Auto-RFM on object schema delta      |
| hs.contract.terminate            | 3    | Token revoked; webhook secret void   |
