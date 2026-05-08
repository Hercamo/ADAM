# Okta Adapter — SSO + SCIM (v0.3, Contract-Bound, Day-1 PQC)

**Card ID:** `adapter-okta`
**Version:** v0.3 (contract-bound)
**Status:** build-ready
**Supersedes:** `adapter-okta__Okta_Adapter_(SSO_+_SCIM).docx.BAK` (v0.2 — retained as old version)
**Contract pattern:** `_CONTRACT_SPEC.md`
**Used By:** `wg-sec-access`, `wg-sec-vault`, `wg-data-pii`, `wg-gov-compliance`, `adamplus-hr-onboarding`, `adamplus-hr-offboarding`, `adamplus-hr-compliance`, `ai-external-stakeholder`. Identity-of-record adapter for the platform.

---

## 1. Target System

Okta Identity Cloud (Workforce + Customer Identity). Surfaces: Okta Management API (REST), SCIM 2.0 provisioning, OIDC + SAML for SSO, System Log API (read), Event Hooks, Inline Hooks (RFM-gated), Workflows (excluded by default), Universal Directory.

## 2. Inbound + Outbound Capabilities

**Outbound:** SCIM 2.0 user/group create-update-deactivate, group membership management, app assignments, factor enrollment management, password reset flows.
**Inbound:** Event Hooks (HMAC-signed), System Log polling, Inline Hook receivers (only with addendum).

## 3. Auth + Identity

OAuth 2.0 service apps with private-key JWT (`token_endpoint_auth_method=private_key_jwt`); EC P-256 keys vaulted at `wg-sec-vault://okta/<org>/jwt-signer`. Scoped `okta.users.manage`, `okta.groups.manage`, `okta.apps.read` per role. mTLS to `<org>.okta.com`. Quantum lock: ML-KEM-1024 wrap, ML-DSA-65 dual-sign on bus.

## 4. Schema Mapping

| Okta Resource         | ADAM Canonical                |
|-----------------------|-------------------------------|
| `User`                | `identity.principal`          |
| `Group`               | `identity.group`              |
| `Application`         | `identity.app`                |
| `Factor`              | `identity.mfa_factor`         |
| `LogEvent`            | `bus.event.okta.log`          |
| `EventHookEvent`      | `bus.event.okta.event_hook`   |

Okta is the **identity-of-record adapter**: every other adapter's user-bound principal references this canonical store.

## 5. Idempotency

* SCIM PATCH/PUT: `Adam-Idem` header (UUID v7); FR pre-write.
* Event Hook dedup `(eventId)` 24 h.
* User/Group ops dedup by Okta `id` + version etag.

## 6. Rate Limits

Per-org rate ceiling enforced 80%; org-wide vs per-endpoint ceilings respected. System Log polling windowed by `published gt`.

## 7. Error Handling

`E0000007` (not found), `E0000011` (invalid token), `E0000056` (rate limit) etc. mapped canonical. Token-expiry ⇒ vault refresh; persistent ⇒ self-suspend.

## 8. Residency

Okta cell (US, EMEA, AU, etc.) pinned in contract. Cross-cell forbidden.

## 9. FR Events

```
adapter.okta.user.create / .update / .deactivate
adapter.okta.group.upsert / .member.add / .member.remove
adapter.okta.app.assignment.upsert
adapter.okta.factor.enroll / .reset
adapter.okta.event_hook.received / .invalid_signature
adapter.okta.log.event.received
adapter.okta.permission.attestation.fail
adapter.okta.schema.drift.detected
adapter.okta.rate.pressure
```

## 10. Configuration Schema

```yaml
adapter_okta:
  org_id: "<org>"
  base_url: "https://<org>.okta.com"
  vault_handle: "wg-sec-vault://okta/<org>/jwt-signer"
  scim_endpoint: "https://<org>.okta.com/scim/v2"
  event_hook_url: "https://adam.<tenant>/adapters/okta/event-hook"
  contract_id: "adapter-okta-contract"
```

## 11. Schemas Spoken

Okta Management API (REST), SCIM 2.0 (RFC 7643/7644), OIDC, SAML 2.0, Event Hooks (HMAC-SHA256), System Log API.

## 12. Day-1 PQC Posture

Bus hybrid Ed25519 + ML-DSA-65. Okta TLS: classical; `qsuite=classical-fallback`. Vault wrap ML-KEM-1024. Auto-RFM when Okta publishes hybrid PQC suites.

## 13. Resource Profile

CPU 1 / 3 burst, RAM 1 GB, Disk 10 GB, Net ≤200 Mbps.

## 14. Dependencies

`wg-sec-vault`, FR, `hi-intent`, `orch-policy`, `meta-stability`, `meta-integrity`, `wg-sec-access`, `adam-adapter-contract-sdk`.

## 15. SLOs

User write p95 ≤ 800 ms; Event Hook p95 ≤ 200 ms; availability ≥ 99.95%; refusal p99 ≤ 30 ms.

## 16. Build Plan

1. Pre-Action Gate via SDK.
2. Service app + private-key JWT.
3. SCIM client with idempotency header.
4. Event Hook receiver with HMAC.
5. Permission attestation on each restart.
6. Schema-drift detector (custom user profile schemas).
7. QA pass1..5 + 360.

## 17. Definition of Done

`qa_all` / `qa_360` / `qa_pass3..5` 100/100; contract lifecycle green; permission-attestation negative test passes; `views_smoke` 70/70.

---

## 18. Contract Binding

* `contract_id`: `adapter-okta-contract`
* `boss_score_floor`: **88** (identity is critical surface; canonical 0..100 BOSS scale).
* `data_classes_allowed`: `pii`, `internal`, `restricted`. No PCI/PHI.
* `egress_allowlist`: `<org>.okta.com:443`, `*.oktapreview.com:443` (preview only in dev).
* `allowed_actions` (default): `user.create`, `user.update`, `user.deactivate`, `group.upsert`, `group.member.add`, `group.member.remove`, `app.assignment.upsert`, `factor.reset`, `event_hook.receive`, `log.poll`.
* `forbidden_actions`: `inline_hook.execute`, `workflow.execute`, `policy.modify`, `authorization_server.modify`, `app.create`, `org.config.write`.

## 19. RFM Triggers

* New scope on service app.
* Inline Hook enablement.
* New custom profile attribute.
* Cross-cell expansion.
* Crypto evolution.

## 20. Smart-Adapter Behaviors

* Mirrors Okta deactivation into all downstream adapters that hold session-bound credentials (Workday, BambooHR, Salesforce, etc.); broadcasts `identity.revoke` event.
* On Event Hook with `user.session.start` from off-allowlist IPs, raises priority and notifies `wg-sec-incident`.
* Permission attestation: hashes effective scopes vs contract; mismatch ⇒ self-suspend.
* Refuses to elevate group membership to Okta admin roles — only humans through the Okta admin console may.
* Auto-RFM on Universal Directory profile schema delta.

## 21. 360 QA Coverage

| Test ID                          | Pass | Outcome                                  |
|----------------------------------|------|------------------------------------------|
| okta.contract.bind.happy         | 3    | Activates after dual-sign                |
| okta.contract.refuse.admin       | 4    | Admin-role membership refused            |
| okta.contract.refuse.inline      | 4    | Inline Hook execution refused            |
| okta.contract.deactivate.cascade | 4    | Deact cascades to other adapters         |
| okta.contract.event_hook.hmac    | 4    | Bad HMAC ⇒ `invalid_signature`           |
| okta.contract.attest.fail        | 4    | Self-suspend on scope mismatch           |
| okta.contract.rfm.profile_attr   | 5    | Profile attr triggers RFM                |
| okta.contract.terminate          | 3    | Service app revoked; vault rotated       |
