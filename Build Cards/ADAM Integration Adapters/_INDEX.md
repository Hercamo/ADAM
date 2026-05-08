# ADAM Integration Adapters (v0.3, Contract-Bound, Day-1 PQC)

21 adapter cards (20 vendor/protocol adapters + 1 observability projection
adapter). Adapters bridge ADAM to external systems and standards-based
projection surfaces. They translate external schemas to canonical ADAM
intents/events, or project canonical ADAM events to standards-compliant
external surfaces; **never govern; never escape governance**. Every
adapter binds to an **External-Adapter-Contract** recorded in the Flight
Recorder before it can act; absent or invalid contract ⇒ inert. Used by
listed ADAMPLUS or base agents — every adapter has a `Used By` list;
consistency is enforced bidirectionally.

## File-naming convention (v0.3)

The v0.3 contract-bound `.md` cards have been renamed to match the long
filenames of the original v0.2 cards (extension changed `.docx` → `.md`).
The original v0.2 binaries have been renamed `.docx` → `.docx.BAK` and are
retained in the directory as old-version backups; they are not loaded by
the build harness. The naming pattern is:

```
adapter-<short-id>__<Long_Display_Name>.md         # v0.3 authoritative card
adapter-<short-id>__<Long_Display_Name>.docx.BAK   # v0.2 archive (read-only)
```

For example: `adapter-stripe__Stripe_Adapter_(Payments_+_Billing_+_Bill).md`
and `adapter-stripe__Stripe_Adapter_(Payments_+_Billing_+_Bill).docx.BAK`.

The short-id (`adapter-stripe`) is canonical for cross-references and for
the Card-ID field at the top of each card.

## Card set

| Domain            | v0.3 (authoritative, contract-bound)                                         | v0.2 (retained as `.docx.BAK` old version)                                  |
|-------------------|------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| Spec (shared)     | `_CONTRACT_SPEC.md`                                                          | (new in v0.3)                                                                |
| QA log            | `_QA_LOG.md`                                                                 | (new in v0.3 — Pass A→D 360° audit record + clean-pass attestation)          |
| CRM/Sales         | `adapter-salesforce__Salesforce_Adapter.md`                                  | `adapter-salesforce__Salesforce_Adapter.docx.BAK`                            |
|                   | `adapter-hubspot__HubSpot_Adapter_(Marketing_+_CRM).md`                      | `adapter-hubspot__HubSpot_Adapter_(Marketing_+_CRM).docx.BAK`                |
|                   | `adapter-dynamics__Microsoft_Dynamics_365_Adapter.md`                        | `adapter-dynamics__Microsoft_Dynamics_365_Adapter.docx.BAK`                  |
| ERP/Finance       | `adapter-sap-s4hana__SAP_S-4HANA_Adapter.md`                                 | `adapter-sap-s4hana__SAP_S-4HANA_Adapter.docx.BAK`                           |
|                   | `adapter-oracle-erp__Oracle_ERP_Cloud_Adapter.md`                            | `adapter-oracle-erp__Oracle_ERP_Cloud_Adapter.docx.BAK`                      |
| HR/Identity       | `adapter-workday__Workday_Adapter_(HCM_+_Payroll).md`                        | `adapter-workday__Workday_Adapter_(HCM_+_Payroll).docx.BAK`                  |
|                   | `adapter-bamboohr__BambooHR_Adapter.md`                                      | `adapter-bamboohr__BambooHR_Adapter.docx.BAK`                                |
|                   | `adapter-okta__Okta_Adapter_(SSO_+_SCIM).md`                                 | `adapter-okta__Okta_Adapter_(SSO_+_SCIM).docx.BAK`                           |
| Banking/Payments  | `adapter-stripe__Stripe_Adapter_(Payments_+_Billing_+_Bill).md`              | `adapter-stripe__Stripe_Adapter_(Payments_+_Billing_+_Bill).docx.BAK`        |
|                   | `adapter-adyen__Adyen_Adapter_(Payments_+_Marketplaces).md`                  | `adapter-adyen__Adyen_Adapter_(Payments_+_Marketplaces).docx.BAK`            |
|                   | `adapter-plaid__Plaid_Adapter_(Banking_Data_Aggregation).md`                 | `adapter-plaid__Plaid_Adapter_(Banking_Data_Aggregation).docx.BAK`           |
|                   | `adapter-swift-iso20022__SWIFT_-_ISO_20022_Adapter.md`                       | `adapter-swift-iso20022__SWIFT_-_ISO_20022_Adapter.docx.BAK`                 |
| Healthcare        | `adapter-hl7-fhir__HL7_v2_+_FHIR_R4-R5_Adapter.md`                           | `adapter-hl7-fhir__HL7_v2_+_FHIR_R4-R5_Adapter.docx.BAK`                     |
| Manufacturing     | `adapter-opcua__OPC-UA_Adapter_(Manufacturing_OT).md`                        | `adapter-opcua__OPC-UA_Adapter_(Manufacturing_OT).docx.BAK`                  |
| Media (sovereign) | `adapter-netstreamx-cms__NetStreamX_Media_CMS_Adapter.md`                    | `adapter-netstreamx-cms__NetStreamX_Media_CMS_Adapter.docx.BAK`              |
| ITSM              | `adapter-servicenow__ServiceNow_Adapter_(ITSM).md`                           | `adapter-servicenow__ServiceNow_Adapter_(ITSM).docx.BAK`                     |
| Procurement       | `adapter-coupa__Coupa_-_SAP_Ariba_Adapter_(Procurement).md`                  | `adapter-coupa__Coupa_-_SAP_Ariba_Adapter_(Procurement).docx.BAK`            |
| Trading           | `adapter-fix__FIX_Protocol_Adapter_(Trading).md`                             | `adapter-fix__FIX_Protocol_Adapter_(Trading).docx.BAK`                       |
| Messaging         | `adapter-twilio-sendgrid__Twilio_+_SendGrid_Messaging_Adapter.md`            | `adapter-twilio-sendgrid__Twilio_+_SendGrid_Messaging_Adapter.docx.BAK`      |
| Support           | `adapter-zendesk__Zendesk_Support_Adapter.md`                                | `adapter-zendesk__Zendesk_Support_Adapter.docx.BAK`                          |
| Observability     | `adapter-otel__OTEL_Integration_Adapter_(Observability).md`                  | (new in v0.3 — no v0.2 predecessor; dual-emit FR/BOSS → OTLP projection)     |

The v0.3 `.md` cards are **authoritative**. The v0.2 `.docx.BAK` files are
kept as old-version backups for historical reference and are not loaded by
the build harness.

## v0.3 — what changed

The v0.2 cards already covered: target system; inbound + outbound
capabilities; auth + identity; **Schema Mapping table** (External ↔ ADAM
concept); idempotency; rate limits; error handling; residency; FR events;
configuration schema; **Schemas Spoken**; Day-1 PQC posture; resource
profile; dependencies; SLOs; build plan; DoD.

v0.3 adds, for every adapter, four new build-ready sections:

* **§18 Contract Binding** — `contract_id`, `boss_score_floor`,
  `data_classes_allowed`, `egress_allowlist`, `allowed_actions`,
  `forbidden_actions`, all per-adapter and machine-checkable.
* **§19 RFM Triggers** — the events that require a Request-for-Modification
  (Intent Object + governor co-sign) before the adapter may change scope.
* **§20 Smart-Adapter Behaviors** — the minimum smartness required for the
  adapter to honor the contract (schema-drift detection, permission
  attestation, refusal-first posture, reconciliation jobs, consent gates).
* **§21 360 QA Coverage** — adapter-specific contract test set tied to the
  five-pass harness.

The shared rules (contract object schema, lifecycle states, Pre-Action
Gate, RFM flow, Intent Object linkage, refusal posture matrix, common FR
events, PQC posture) live once in `_CONTRACT_SPEC.md`. Per-adapter cards
reference it instead of restating.

## Cross-cutting invariants (unchanged from v0.2)

Adapter credentials live in `wg-sec-vault`, rotated on schedule. Every
event the adapter publishes onto the ADAM bus is dual-signed Ed25519 +
ML-DSA-65; inbound source signature posture is recorded on each event.
Single-signed inbound payloads from the external world ARE accepted (we
cannot force the world to dual-sign), but they are flagged on every
emitted event. Adapters never govern, never escape governance.

## Cross-cutting invariants (new in v0.3)

* No adapter performs any action without a currently-bound, valid
  contract. Absent contract ⇒ adapter is inert and emits
  `adapter.contract.absent`.
* Every action passes the synchronous in-process Pre-Action Gate
  (allow-list verb, allow-list data-class, in-window rate, in-allowlist
  egress, BOSS-Score-floor) before any external call or bus emission.
* Every contract change — scope, residency, rate ceiling, key rotation,
  termination — flows through an Intent Object and a co-signed RFM. No
  adapter self-amends.
* Doctrine never self-amends; an RFM that would require doctrinal change
  is refused regardless of governor consent.
* Every emitted event includes the adapter's current contract head hash;
  silent contract divergence is detectable from the bus.

## Build harness

QA across all 20 cards runs the five-pass harness:

* Pass 1 — Schema parity (card ↔ doctrine).
* Pass 2 — Capability matrix (verbs vs `allowed_actions`).
* Pass 3 — Contract lifecycle (`DRAFT → ACTIVE → AMENDED → TERMINATED`).
* Pass 4 — Refusal posture (every row of `_CONTRACT_SPEC.md` §10).
* Pass 5 — RFM + Intent Object roundtrip (scope expansion, residency
  change, revoke).

DoD: 100/100 on `qa_all`, 100/100 on `qa_360`, 100/100 on each of
`qa_pass3..5`, 70/70 on `views_smoke`.

QA target (current build): **21/21 cards passing all five passes; 0
failures.** (20 vendor/protocol adapters + 1 observability projection
adapter `adapter-otel`.) Detailed adapter test ids live in §21 of each
card.

Note on the observability adapter: `adapter-otel` is a one-way
projection adapter — its "external system" is the in-cluster
`adam-otel-collector` (and any standards-compliant downstream the
operator wires it to). The Flight Recorder remains the source of truth;
OTEL is the open-standard projection. The adapter holds an FR
`subscribe-only` capability token and is structurally incapable of
mutating the chain. See `adapter-otel__OTEL_Integration_Adapter_(Observability).md`.

## Reading order (suggested)

1. `_CONTRACT_SPEC.md` — read first; it is referenced by every card.
2. `adapter-okta__Okta_Adapter_(SSO_+_SCIM).md` — identity-of-record
   adapter; many other adapters cascade against Okta deactivation.
3. `adapter-stripe__Stripe_Adapter_(Payments_+_Billing_+_Bill).md` and
   `adapter-swift-iso20022__SWIFT_-_ISO_20022_Adapter.md` — illustrate the
   strictest financial contract postures (PCI-token, non-repudiation).
4. `adapter-hl7-fhir__HL7_v2_+_FHIR_R4-R5_Adapter.md` and
   `adapter-opcua__OPC-UA_Adapter_(Manufacturing_OT).md` — illustrate
   regulated-data and OT-safety postures.
5. `adapter-netstreamx-cms__NetStreamX_Media_CMS_Adapter.md` — sovereign
   loopback adapter; the only one running hybrid-PQC mTLS end-to-end on
   Day 1.
6. `adapter-otel__OTEL_Integration_Adapter_(Observability).md` — the
   one-way projection adapter; FR/BOSS dual-emit to OTLP using the
   ADAM-prefixed `agent_scope.*` semantic-convention namespace.
7. Remaining adapters in the order their owning ADAMPLUS/base agent
   appears in the agent index.
