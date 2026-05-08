# Twilio + SendGrid Messaging Adapter (v0.3, Contract-Bound, Day-1 PQC)

**Card ID:** `adapter-twilio-sendgrid`
**Version:** v0.3 (contract-bound)
**Status:** build-ready
**Supersedes:** `adapter-twilio-sendgrid__Twilio_+_SendGrid_Messaging_Adapter.docx.BAK` (v0.2 — retained as old version)
**Contract pattern:** `_CONTRACT_SPEC.md`
**Used By:** `wg-market-customer`, `wg-gov-stakeholder`, `wg-sec-incident` (alerts), `ai-external-stakeholder`, `ai-external-regulatory` (notifications), `adamplus-ar-collections`, `adamplus-crm-cases`

---

## 1. Target System

Twilio (Programmable Messaging — SMS, WhatsApp Business, Voice, Verify, Conversations) and SendGrid (transactional email + Marketing Campaigns). Surfaces: Twilio REST + Webhooks (signed `X-Twilio-Signature`), SendGrid v3 REST + Webhooks (signed `X-Twilio-Email-Event-Webhook-Signature`).

## 2. Inbound + Outbound Capabilities

**Outbound:** SMS/MMS/WhatsApp send, voice TwiML invocation (RFM-gated for IVR), email send, template-based send, suppression list updates.
**Inbound:** Twilio inbound message webhooks, status callbacks (delivered/failed/read), SendGrid event webhooks (open/click/bounce/spam — only the deliverability ones; click+open content rendering excluded by default for privacy).

## 3. Auth + Identity

Twilio Account SID + Auth Token vaulted at `wg-sec-vault://twilio/<acct>/auth-token`; API Keys preferred where allowed. SendGrid API Key vaulted at `wg-sec-vault://sendgrid/<acct>/api-key`. Webhook signing keys separately vaulted. mTLS to vendor endpoints. Quantum lock: ML-KEM-1024 wrap, ML-DSA-65 dual-sign on bus.

## 4. Schema Mapping

| Vendor Concept           | ADAM Canonical                  |
|--------------------------|---------------------------------|
| Twilio `Message`         | `messaging.sms` / `messaging.wa`|
| Twilio `Call`            | `messaging.voice`               |
| Twilio `VerifyAttempt`   | `identity.verify_attempt`       |
| SendGrid `Send`          | `messaging.email`               |
| SendGrid Event           | `bus.event.email.<event_type>`  |
| Suppression entry        | `messaging.suppression`         |

## 5. Idempotency

* Twilio: `Idempotency-Key` header (where supported) + adapter-side dedup on `(to, from, body_hash, window=5min)`; FR pre-write.
* SendGrid: `X-Idempotency-Key` (vendor extension) recorded in FR; dedup on `(to, template_id, payload_hash, window=5min)`.
* Webhook dedup on vendor `MessageSid` / `event_id` 24 h.

## 6. Rate Limits

Twilio per-number TPS, SendGrid per-IP / per-account ceilings — contract enforces 80%. Country-specific SMS regulations (e.g., 10DLC throughput) honored.

## 7. Error Handling

Twilio error codes (e.g., 21610 unsubscribed, 30007 carrier filter) mapped canonical and routed to `messaging.suppression` workflow. SendGrid bounces split soft vs hard; hard bounces auto-add to suppression.

## 8. Residency

Per-region setup: Twilio Frankfurt/Sydney/SP if provisioned; SendGrid SE/EU if provisioned. Cross-region forbidden without RFM. PII allowed; PHI requires HIPAA BAA + addendum.

## 9. FR Events

```
adapter.messaging.sms.sent / .delivered / .failed
adapter.messaging.wa.sent / .delivered / .read
adapter.messaging.voice.initiated / .completed
adapter.messaging.email.sent / .delivered / .bounced / .spam_reported
adapter.messaging.suppression.added / .removed
adapter.messaging.webhook.received / .invalid_signature
adapter.messaging.unsub.detected
adapter.messaging.rate.pressure
```

## 10. Configuration Schema

```yaml
adapter_twilio_sendgrid:
  twilio:
    account_sid: "AC<...>"
    api_key_handle: "wg-sec-vault://twilio/<acct>/api-key"
    webhook_secret_handle: "wg-sec-vault://twilio/<acct>/webhook"
    senders: ["+15551234567", "MG<msg_svc>"]
  sendgrid:
    api_key_handle: "wg-sec-vault://sendgrid/<acct>/api-key"
    webhook_pubkey_handle: "wg-sec-vault://sendgrid/<acct>/webhook-pubkey"
    domains: ["mail.<tenant>.com"]
  contract_id: "adapter-twilio-sendgrid-contract"
```

## 11. Schemas Spoken

Twilio REST (`application/x-www-form-urlencoded`), Twilio Webhooks (HMAC-SHA1 with `X-Twilio-Signature`), SendGrid v3 REST (JSON), SendGrid Event Webhook (Ed25519 signed).

## 12. Day-1 PQC Posture

Bus hybrid Ed25519 + ML-DSA-65. Vendor TLS classical; `qsuite=classical-fallback`. SendGrid webhook uses Ed25519 (good — already PQC-adjacent). Vault wrap ML-KEM-1024.

## 13. Resource Profile

CPU 1 / 3 burst, RAM 1 GB, Disk 10 GB, Net ≤200 Mbps.

## 14. Dependencies

`wg-sec-vault`, FR, `hi-intent`, `orch-policy`, `meta-stability`, `meta-integrity`, `wg-data-pii`, `wg-data-rights`, `adam-adapter-contract-sdk`.

## 15. SLOs

Send p95 ≤ 800 ms; webhook p95 ≤ 200 ms; availability ≥ 99.95%; refusal p99 ≤ 30 ms.

## 16. Build Plan

1. Pre-Action Gate via SDK.
2. Twilio + SendGrid clients with vaulted credentials.
3. Webhook receivers (HMAC-SHA1 + Ed25519).
4. Suppression sync on bounce/spam/unsub events.
5. Country/carrier rule engine for outbound SMS.
6. Consent gate referencing `wg-data-rights`.
7. QA pass1..5 + 360.

## 17. Definition of Done

`qa_all` / `qa_360` / `qa_pass3..5` 100/100; contract lifecycle green; consent + suppression gates verified; `views_smoke` 70/70.

---

## 18. Contract Binding

* `contract_id`: `adapter-twilio-sendgrid-contract` (covers both Twilio and SendGrid surfaces; per spec convention `adapter-<card-id>-contract`)
* `boss_score_floor`: **76** (canonical 0..100 BOSS scale; messaging consent + reputation surface).
* `data_classes_allowed`: `pii`, `internal`, `restricted`. PHI requires BAA addendum (HIPAA).
* `egress_allowlist`: `*.twilio.com:443`, `api.sendgrid.com:443`, `mx.sendgrid.net:443`.
* `allowed_actions` (default): `sms.send`, `wa.send`, `email.send`, `verify.create`, `suppression.add`, `suppression.remove`, `webhook.receive`, `event.consume`.
* `forbidden_actions`: `voice.outbound.dial` (default; IVR addendum required), `marketing.bulk_send` (template+segment requires consent attestation), `domain.authentication.modify`, `phone_number.purchase`, `messaging_service.modify`.

## 19. RFM Triggers

* IVR voice flows.
* Marketing bulk sends with new segment criteria.
* New sender domain or phone number.
* HIPAA BAA addendum (PHI in messaging).
* New region.
* Crypto evolution.

## 20. Smart-Adapter Behaviors

* Refuses to send to any recipient on `messaging.suppression` regardless of caller.
* Verifies consent attestation hash (from `wg-data-rights`) on every send; mismatch ⇒ refuse + emit `consent.missing`.
* On unsubscribe (HELP/STOP for SMS, `mailto:list-unsubscribe` for email), immediately adds to suppression and confirms — never silently drops the unsub.
* Country-aware: refuses SMS to numbers in countries not listed in addendum (e.g., 10DLC US-only profile won't send to AU).
* Treats SendGrid Ed25519 verification failure as a high-priority security event.

## 21. 360 QA Coverage

| Test ID                              | Pass | Outcome                                  |
|--------------------------------------|------|------------------------------------------|
| msg.contract.bind.happy              | 3    | Activates after dual-sign                |
| msg.contract.refuse.suppressed       | 4    | Send to suppressed recipient refused     |
| msg.contract.refuse.no_consent       | 4    | Send without consent attestation refused |
| msg.contract.refuse.cross_country    | 4    | Off-allowlist country refused            |
| msg.contract.unsub.honored           | 4    | STOP/unsub added to suppression          |
| msg.contract.webhook.ed25519         | 4    | Bad Ed25519 ⇒ `invalid_signature`        |
| msg.contract.rfm.ivr                 | 5    | IVR enablement triggers RFM              |
| msg.contract.terminate               | 3    | API keys rotated; webhook secrets void   |
