# Workday Adapter — HCM + Payroll (v0.3, Contract-Bound, Day-1 PQC)

**Card ID:** `adapter-workday`
**Version:** v0.3 (contract-bound)
**Status:** build-ready
**Supersedes:** `adapter-workday__Workday_Adapter_(HCM_+_Payroll).docx.BAK` (v0.2 — retained as old version)
**Contract pattern:** `_CONTRACT_SPEC.md`
**Used By:** `adamplus-hr-onboarding`, `adamplus-hr-offboarding`, `adamplus-hr-payroll`, `adamplus-hr-benefits`, `adamplus-hr-time`, `adamplus-hr-performance`, `adamplus-hr-compliance`, `wg-data-pii`, `wg-gov-compliance`, `ai-external-stakeholder`

---

## 1. Target System

Workday HCM, Payroll, Recruiting, Time Tracking, Absence. Surfaces: Workday SOAP Web Services (WWS) v40+, REST API (RaaS reports / Inbound Strategic Sourcing), Workday Studio integrations (event-driven), Workday Extend (custom apps), Core Connector framework (file-based).

## 2. Inbound + Outbound Capabilities

**Outbound:**
* SOAP `Put_Worker`, `Hire_Employee`, `Terminate_Employee`, `Change_Job`, `Edit_Position` (all under contract scope).
* RaaS report execution.
* Payroll input file submission via SFTP-anchored Core Connector.
* Custom Workday Extend POST.

**Inbound:**
* Workday Studio outbound webhook receiver (signed).
* RaaS report pull on schedule.
* Workday Event Subscription Service for change events (`*.WorkerEvent`).

## 3. Auth + Identity

* OAuth 2.0 with x509 private-key JWT for service integrations; ISU (Integration System User) per scope, with field-level Domain Security policy mirroring contract.
* mTLS to `*.workday.com` and tenant-specific endpoints.
* SFTP for Core Connector via SSH key vaulted at `wg-sec-vault://workday/<tenant>/sftp`.
* Quantum lock: ML-KEM-1024 wrap, ML-DSA-65 dual-sign.

## 4. Schema Mapping

| Workday Object       | ADAM Canonical Concept            | Notes                         |
|----------------------|-----------------------------------|-------------------------------|
| `Worker`             | `identity.worker`                 | PII; SoR for HR identity      |
| `Position`           | `org.position`                    |                               |
| `Job_Profile`        | `org.role`                        |                               |
| `Organization`       | `org.unit`                        |                               |
| `Compensation`       | `comp.package`                    | PII + financial               |
| `Time_Off_Plan`      | `time.absence_plan`               |                               |
| `Payroll_Result`     | `payroll.result`                  | PII + PCI possible (bank acct)|
| `Worker_Event`       | `bus.event.workday.worker`        | Onboard/term/move             |

PHI is forbidden by default unless contract addendum explicitly enables (rare; Workday is not a PHI store).

## 5. Idempotency

* SOAP outbound: `Adam-Idem` SOAP header (UUID v7) recorded in FR; Workday's `External_ID` field used for upsert.
* Core Connector files: filename includes UUID v7 + sha256; SFTP `.tmp`→rename pattern.
* Inbound events: dedup `(EventID, EffectiveDate)` 24 h window.

## 6. Rate Limits

* Workday's per-tenant SOAP concurrency cap; in-process `rate_ceiling_per_min` from contract.
* RaaS report queueing with concurrency 4.
* Studio webhook receiver: token-bucket on inbound to absorb bursts.

## 7. Error Handling

* `Validation_Error` → DLQ + auto-RFM if schema drift.
* `Concurrent_Modification` → retry with backoff.
* `Permission_Denied` → never retry; emit `permission.attestation.fail` and self-suspend (Domain Security drift).
* All errors dual-signed.

## 8. Residency

Workday tenant region (NA1, EMEA1, APAC1, etc.) pinned in contract. Cross-region replication forbidden without RFM. PII default; PCI requires explicit grant.

## 9. FR Events

```
adapter.workday.worker.upsert.ok / .failed
adapter.workday.hire.posted / .term.posted / .move.posted
adapter.workday.payroll.input.submitted
adapter.workday.payroll.result.received
adapter.workday.event.received
adapter.workday.report.executed
adapter.workday.permission.attestation.fail
adapter.workday.schema.drift.detected
adapter.workday.rate.pressure
```

## 10. Configuration Schema

```yaml
adapter_workday:
  tenant: "<tenant>"
  endpoints:
    soap: "https://wd5-impl-services1.workday.com/ccx/service/<tenant>/Human_Resources/v40.0"
    raas: "https://wd5-impl-services1.workday.com/ccx/service/customreport2/<tenant>/<owner>/<report>"
  vault_handle: "wg-sec-vault://workday/<tenant>/jwt"
  sftp_handle: "wg-sec-vault://workday/<tenant>/sftp"
  isu_user: "ISU_ADAM_<scope>"
  reports: ["AdamWorkerDelta", "AdamPayrollOutput"]
  contract_id: "adapter-workday-contract"
```

## 11. Schemas Spoken

* Workday Web Services (SOAP) v40+.
* RaaS REST.
* Core Connector flat-file specs.
* Workday Studio webhook payloads (XML/JSON).

## 12. Day-1 PQC Posture

* Bus emissions: hybrid Ed25519 + ML-DSA-65.
* Workday TLS: classical (Workday roadmap-pending). `qsuite=classical-fallback` recorded.
* SFTP: SSH ed25519 + classical KEX. PQC SSH KEX deferred to vendor support.
* Vault wrap: ML-KEM-1024.

## 13. Resource Profile

* CPU: 1 vCPU steady, 3 vCPU burst (payroll runs).
* Memory: 1 GB steady, 4 GB burst.
* Disk: 50 GB ephemeral (file staging).
* Network: ≤300 Mbps egress.

## 14. Dependencies

`wg-sec-vault`, FR, `hi-intent`, `orch-policy`, `meta-stability`, `meta-integrity`, `wg-data-pii`, `wg-data-residency`, `adam-adapter-contract-sdk`, `adapter-okta` (identity-of-record).

## 15. SLOs

* Worker upsert p95 ≤ 2.0 s.
* Payroll input file delivery within 5 min of trigger.
* Adapter availability ≥ 99.9%.
* Refusal latency p99 ≤ 50 ms.

## 16. Build Plan

1. Pre-Action Gate via SDK.
2. ISU + Domain Security template generation.
3. SOAP client with idempotency header.
4. RaaS pull scheduler with delta cursor in FR.
5. SFTP Core Connector with rename-pattern uploads.
6. Schema-drift detector on Workday Object Model.
7. QA pass1..5 + 360.

## 17. Definition of Done

* `qa_all` / `qa_360` / `qa_pass3..5` 100/100 each.
* Contract lifecycle smoke test green.
* Domain Security drift triggers self-suspend.
* `views_smoke` 70/70.
* Index entry updated.

---

## 18. Contract Binding

* `contract_id`: `adapter-workday-contract`
* `boss_score_floor`: **80** (high PII + financial sensitivity; canonical 0..100 BOSS scale).
* `data_classes_allowed`: `pii`, `internal`, `restricted`. PCI requires addendum (payroll bank fields). PHI forbidden.
* `egress_allowlist`: `*.workday.com:443`, `*.myworkday.com:443`, SFTP host(s) per addendum.
* `allowed_actions` (default): `worker.upsert`, `worker.read`, `hire.post`, `terminate.post`, `change_job.post`, `position.upsert`, `report.execute`, `payroll.input.submit`, `payroll.result.read`, `event.subscribe`.
* `forbidden_actions`: `domain_security.modify`, `isu.create`, `tenant.config.write`, `compensation.bulk_update` (without RFM), `report.create`.

## 19. RFM Triggers

* New ISU scope.
* Adding PCI data class for payroll.
* Cross-region replication.
* Adding a new tenant.
* Compensation bulk operations.
* Crypto suite evolution.

## 20. Smart-Adapter Behaviors

* On `Worker_Event` for termination, the adapter immediately notifies `adamplus-hr-offboarding` AND `adapter-okta` to revoke identity — refuses to suppress this even if asked.
* Detects Domain Security drift by comparing the ISU's effective Domain Security to the contract; mismatch ⇒ self-suspend + emit `permission.attestation.fail`.
* Refuses outbound `worker.upsert` if the `Worker.Person.Name` change includes legal-name fields without a corresponding consent record from `wg-data-pii`.
* Uses `External_ID` to enforce idempotent upsert; never relies on Workday-side dedup alone.
* Auto-RFM on Workday Object Model deltas detected via metadata reports.

## 21. 360 QA Coverage

| Test ID                       | Pass | Outcome                                          |
|-------------------------------|------|--------------------------------------------------|
| wd.contract.bind.happy        | 3    | Activates after dual-sign verified               |
| wd.contract.refuse.dom_sec    | 4    | Self-suspend on Domain Security drift            |
| wd.contract.refuse.legal_name | 4    | Refuses legal-name change without consent record |
| wd.contract.rfm.region_add    | 5    | Adding APAC1 triggers full RFM                   |
| wd.contract.term.cascade      | 4    | Term event cascades to Okta revoke               |
| wd.contract.payroll.pci       | 5    | PCI on payroll requires addendum                 |
| wd.contract.schema_drift      | 5    | Auto-RFM on object model change                  |
| wd.contract.terminate         | 3    | Vault keys rotated; SFTP keys revoked            |
