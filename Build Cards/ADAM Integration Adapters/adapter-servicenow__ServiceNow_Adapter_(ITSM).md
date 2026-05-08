# ServiceNow Adapter — ITSM (v0.3, Contract-Bound, Day-1 PQC)

**Card ID:** `adapter-servicenow`
**Version:** v0.3 (contract-bound)
**Status:** build-ready
**Supersedes:** `adapter-servicenow__ServiceNow_Adapter_(ITSM).docx.BAK` (v0.2 — retained as old version)
**Contract pattern:** `_CONTRACT_SPEC.md`
**Used By:** `wg-ops-translate`, `wg-ops-recovery`, `wg-ops-bc`, `wg-sec-incident`, `wg-data-quality`, `wg-gov-compliance`, `adamplus-itsm-incident`, `adamplus-itsm-change`, `ai-external-stakeholder`

---

## 1. Target System

ServiceNow (ITSM, ITOM, SecOps, GRC). Surfaces: Table API, Aggregate API, Import Set API, Scripted REST, MID Server (for on-prem peers), Event API, IntegrationHub flows (excluded by default), CMDB CI Class API.

## 2. Inbound + Outbound Capabilities

**Outbound:** Create/update incidents, problems, changes, requests, tasks, CIs (CMDB), knowledge articles. Aggregate queries.
**Inbound:** Business Rule webhook receiver, Scripted REST callbacks, Event API ingestion.

## 3. Auth + Identity

OAuth 2.0 password-grant deprecated; ADAM uses JWT bearer (`oauth_jwt_provider`) with vaulted RSA/EC private key at `wg-sec-vault://servicenow/<instance>/jwt-signer`. ACL-bound integration user with least-privilege roles. mTLS to `*.service-now.com`. Quantum lock: ML-KEM-1024 wrap, ML-DSA-65 dual-sign.

## 4. Schema Mapping

| ServiceNow Table       | ADAM Canonical              |
|------------------------|-----------------------------|
| `incident`             | `service.incident`          |
| `problem`              | `service.problem`           |
| `change_request`       | `service.change`            |
| `sc_request` / `_item` | `service.request`           |
| `task`                 | `service.task`              |
| `cmdb_ci_*`            | `cmdb.ci`                   |
| `kb_knowledge`         | `kb.article`                |
| `sn_si_incident` (Sec) | `security.incident`         |

## 5. Idempotency

* Outbound: `x_adam_idem` field (UUID v7) on every create/update; FR pre-write.
* Inbound webhook dedup `(table, sys_id, sys_updated_on)` 24 h.
* Import Set staging tables consumed once per `sys_import_state_comment` recorded in FR.

## 6. Rate Limits

Per-instance and per-table API limits enforced 80%. MID Server queue capacity respected for on-prem CIs.

## 7. Error Handling

`StatusCode 4xx` mapped by `error.detail`. `WriteRecord_Failed` with ACL denial ⇒ self-suspend (ACL drift). `403` w/o ACL match ⇒ raise to `ga-security`.

## 8. Residency

Per ServiceNow datacenter pinned in contract. Cross-DC forbidden.

## 9. FR Events

```
adapter.servicenow.incident.create / .update / .close
adapter.servicenow.change.create / .approve / .schedule
adapter.servicenow.cmdb.ci.upsert
adapter.servicenow.kb.upsert
adapter.servicenow.security_incident.received
adapter.servicenow.event.received
adapter.servicenow.webhook.received
adapter.servicenow.acl.drift.detected
adapter.servicenow.rate.pressure
```

## 10. Configuration Schema

```yaml
adapter_servicenow:
  instance: "<instance>"
  base_url: "https://<instance>.service-now.com"
  vault_handle: "wg-sec-vault://servicenow/<instance>/jwt-signer"
  oauth:
    client_id: "<id>"
    jwt_provider: "<jwt_provider_sys_id>"
  contract_id: "adapter-servicenow-contract"
```

## 11. Schemas Spoken

Table API REST, Aggregate API, Import Set API, Scripted REST, Event API, MID Server protocol.

## 12. Day-1 PQC Posture

Bus hybrid Ed25519 + ML-DSA-65. ServiceNow TLS classical; `qsuite=classical-fallback`. Vault wrap ML-KEM-1024.

## 13. Resource Profile

CPU 1 / 3 burst, RAM 1 GB, Disk 10 GB, Net ≤200 Mbps.

## 14. Dependencies

`wg-sec-vault`, FR, `hi-intent`, `orch-policy`, `meta-stability`, `meta-integrity`, `wg-sec-incident`, `wg-ops-recovery`, `adam-adapter-contract-sdk`.

## 15. SLOs

Record write p95 ≤ 1.0 s; webhook p95 ≤ 200 ms; availability ≥ 99.9%; refusal p99 ≤ 30 ms.

## 16. Build Plan

1. Pre-Action Gate via SDK.
2. JWT-bearer OAuth with vault key.
3. Table API client with idempotency field.
4. Scripted REST callback receiver.
5. ACL attestation on each restart.
6. Schema-drift detector.
7. QA pass1..5 + 360.

## 17. Definition of Done

`qa_all` / `qa_360` / `qa_pass3..5` 100/100; contract lifecycle green; ACL drift triggers self-suspend; `views_smoke` 70/70.

---

## 18. Contract Binding

* `contract_id`: `adapter-servicenow-contract`
* `boss_score_floor`: **76** (canonical 0..100 BOSS scale; ITSM + SecOps surface).
* `data_classes_allowed`: `pii`, `internal`, `restricted`. PCI/PHI by addendum (rare).
* `egress_allowlist`: `*.service-now.com:443`.
* `allowed_actions` (default): `incident.create`, `incident.update`, `change.create`, `change.update`, `task.upsert`, `cmdb.ci.upsert`, `kb.upsert`, `security_incident.consume`, `event.consume`, `webhook.receive`, `aggregate.query`.
* `forbidden_actions`: `flow.execute`, `script_include.deploy`, `acl.modify`, `update_set.commit`, `mid_server.config.write`, `instance.config.write`.

## 19. RFM Triggers

* New table.
* New role.
* PCI/PHI addendum.
* New instance.
* Crypto evolution.

## 20. Smart-Adapter Behaviors

* On create/close incident, mirrors state into ADAM `service.case` canonical and reconciles to detect drift.
* For changes, refuses to bypass ServiceNow Change Advisory Board (CAB) approval flag — never auto-approves.
* ACL attestation on each restart: hashes integration user's effective ACL set; mismatch ⇒ self-suspend.
* Auto-RFM on table schema delta from `sys_dictionary`.

## 21. 360 QA Coverage

| Test ID                          | Pass | Outcome                                       |
|----------------------------------|------|-----------------------------------------------|
| snow.contract.bind.happy         | 3    | Activates after dual-sign                     |
| snow.contract.refuse.flow        | 4    | IntegrationHub flow execution refused         |
| snow.contract.refuse.cab_bypass  | 4    | Auto-approve of change refused                |
| snow.contract.acl.drift          | 4    | Self-suspend on ACL mismatch                  |
| snow.contract.rfm.table_add      | 5    | New table triggers RFM                        |
| snow.contract.schema_drift       | 5    | Auto-RFM on dictionary change                 |
| snow.contract.terminate          | 3    | OAuth keys rotated; client deactivated        |
