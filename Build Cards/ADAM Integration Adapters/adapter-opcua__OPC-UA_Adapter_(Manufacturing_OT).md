# OPC-UA Adapter — Manufacturing OT (v0.3, Contract-Bound, Day-1 PQC)

**Card ID:** `adapter-opcua`
**Version:** v0.3 (contract-bound)
**Status:** build-ready
**Supersedes:** `adapter-opcua__OPC-UA_Adapter_(Manufacturing_OT).docx.BAK` (v0.2 — retained as old version)
**Contract pattern:** `_CONTRACT_SPEC.md`
**Used By:** `wg-ops-translate`, `wg-ops-dependency`, `wg-ops-recovery`, `wg-ops-bc`, `adamplus-ops-mes`, `twin-operational`, `ai-data-pipeline`

---

## 1. Target System

OPC-UA servers (PLCs, SCADA, MES gateways, Aveva/Rockwell/Siemens stacks). Surfaces: OPC-UA Binary (port 4840) and OPC-UA HTTPS, Subscriptions/MonitoredItems, Methods (with strict allow-list), AlarmsAndConditions, HistoricalAccess. Production scope is read-heavy; writes only to allow-listed nodes.

## 2. Inbound + Outbound Capabilities

**Outbound:** Browse, Read, Write (allow-listed nodes), Method calls (allow-listed), HistoryRead.

**Inbound:** Subscription with MonitoredItems for tag changes; Alarms/Conditions; Server status notifications.

## 3. Auth + Identity

OPC-UA SecurityPolicy `Aes256_Sha256_RsaPss` minimum; certificate-based user token; per-server certs vaulted at `wg-sec-vault://opcua/<server-id>/cert`. The adapter publishes its own certificate for trust pinning at the OT side. Quantum lock: ML-KEM-1024 wrap, ML-DSA-65 dual-sign on bus emissions.

## 4. Schema Mapping

| OPC-UA Concept        | ADAM Canonical                  |
|-----------------------|---------------------------------|
| `NodeId`              | `ot.node`                       |
| `Variable` value      | `ot.tag.sample`                 |
| `Method` call         | `ot.method.invocation`          |
| `Event` (Alarm/Cond)  | `bus.event.ot.alarm`            |
| `HistoryReadResult`   | `ot.history.window`             |

Tag taxonomy is mapped per-deployment in contract addendum (every customer site is unique).

## 5. Idempotency

* Writes: client-generated correlation id recorded in FR; OPC-UA server-side write is idempotent only if tag semantics are idempotent — non-idempotent setpoint writes require contract addendum approval per node.
* Subscriptions: monotonic `ServerTimestamp` per MonitoredItem; checkpoints in FR.

## 6. Rate Limits

Per-server publishing interval respected (typical 250 ms–1 s); contract enforces per-node sample-rate ceiling and aggregates burstiness into batch events.

## 7. Error Handling

`Bad_*` status codes mapped to canonical taxonomy. Critical: `Bad_NotConnected`, `Bad_DeviceFailure`, `Bad_OutOfRange` raise `ot.alert.<class>` events at high priority; never silently retried.

## 8. Residency

OT-air-gap is the default. Adapter runs co-located with the cell or the plant DMZ. Cross-site replication forbidden; all egress to corporate IT goes through the ADAM bus only — never direct from OT.

## 9. FR Events

```
adapter.opcua.subscription.started / .stopped
adapter.opcua.tag.sample.received
adapter.opcua.tag.write.ok / .failed
adapter.opcua.method.invoked
adapter.opcua.alarm.received
adapter.opcua.history.read
adapter.opcua.server.disconnected / .reconnected
adapter.opcua.cert.rotated
adapter.opcua.rate.pressure
```

## 10. Configuration Schema

```yaml
adapter_opcua:
  servers:
    - server_id: "site1-line2-plc1"
      endpoint_url: "opc.tcp://10.50.12.30:4840"
      security_policy: "Aes256_Sha256_RsaPss"
      message_security_mode: "SignAndEncrypt"
      vault_handle: "wg-sec-vault://opcua/site1-line2-plc1/cert"
  subscriptions:
    - server_id: "site1-line2-plc1"
      publishing_interval_ms: 500
      monitored_items: ["ns=2;s=Press.Temp", "ns=2;s=Press.Force"]
  contract_id: "adapter-opcua-contract"
```

## 11. Schemas Spoken

OPC-UA Binary (TCP 4840), OPC-UA HTTPS, NodeSet2 XML for type imports, AlarmsAndConditions, HistoricalAccess, Pub/Sub UADP (where deployed).

## 12. Day-1 PQC Posture

Bus: hybrid Ed25519 + ML-DSA-65. OPC-UA SecurityPolicy: classical RSA/ECDSA (vendor-controlled). When OPC-UA publishes PQC SecurityPolicies, contract amends via RFM. `qsuite=classical-fallback` recorded on every event. Vault wrap ML-KEM-1024.

## 13. Resource Profile

CPU 2 / 4 burst, RAM 2 GB / 4 burst, Disk 30 GB (history cache), Net ≤200 Mbps OT-side.

## 14. Dependencies

`wg-sec-vault`, FR, `hi-intent`, `orch-policy`, `meta-stability`, `meta-integrity`, `wg-ops-recovery`, `wg-ops-bc`, `twin-operational`, `adam-adapter-contract-sdk`.

## 15. SLOs

Tag sample latency p95 ≤ 200 ms (OT to bus); reconnect MTTR ≤ 5 s; availability ≥ 99.99%; refusal p99 ≤ 20 ms.

## 16. Build Plan

1. Pre-Action Gate via SDK.
2. OPC-UA client with cert pinning + SecurityPolicy floor.
3. Subscription manager with FR-anchored checkpoints.
4. Method invocation gate per allow-listed node id.
5. Alarms emitter with priority routing.
6. Cert rotation runbook (OT certs are usually long-lived; rotation triggers Method-stop).
7. QA pass1..5 + 360.

## 17. Definition of Done

`qa_all` / `qa_360` / `qa_pass3..5` 100/100; contract lifecycle green; SecurityPolicy floor verified; setpoint write requires per-node addendum; `views_smoke` 70/70.

---

## 18. Contract Binding

* `contract_id`: `adapter-opcua-contract`
* `boss_score_floor`: **88** (OT safety surface; canonical 0..100 BOSS scale).
* `data_classes_allowed`: `internal`, `restricted`. No PII/PCI/PHI under default profile (OT data is non-personal).
* `egress_allowlist`: only OT cell endpoints on OPC-UA Binary `<host>:4840` (or HTTPS `<host>:443` per server profile), enumerated in the per-deployment addendum; corporate IT egress goes through ADAM bus, never direct.
* `allowed_actions` (default): `browse`, `read`, `subscription.start`, `subscription.stop`, `history.read`, `alarm.consume`.
* `forbidden_actions`: `node.write` (default deny — every writeable node requires addendum), `method.invoke` (default deny — every method requires addendum), `cert.replace.runtime`, `securitypolicy.downgrade`.

## 19. RFM Triggers

* Adding a writeable node.
* Adding a callable method.
* New OPC-UA server.
* Crypto evolution (PQC SecurityPolicy adoption).
* SecurityPolicy change.

## 20. Smart-Adapter Behaviors

* SecurityPolicy floor enforced per session; if a server presents only weaker policies, adapter refuses to connect and emits `securitypolicy.too_weak`.
* On `Bad_DeviceFailure` from a primary node, raises high-priority `ot.alert.device_failure` directly to `wg-ops-recovery`.
* For setpoint writes, requires a same-FR-batch attestation that the upstream agent had `boss_score >= 0.92` for that specific node — extra scrutiny over the global floor.
* Rejects history-read requests for windows beyond contract retention policy.
* Treats every reconnect as a fresh session; replays subscription configuration deterministically from FR-anchored state.

## 21. 360 QA Coverage

| Test ID                              | Pass | Outcome                                       |
|--------------------------------------|------|-----------------------------------------------|
| opcua.contract.bind.happy            | 3    | Activates after dual-sign                     |
| opcua.contract.refuse.weak_policy    | 4    | Connection refused with weak SecurityPolicy   |
| opcua.contract.refuse.write          | 4    | Default writes refused                        |
| opcua.contract.refuse.method         | 4    | Default methods refused                       |
| opcua.contract.alarm.priority        | 4    | Alarms route at high priority                 |
| opcua.contract.rfm.writeable_node    | 5    | Writeable node addendum runs full RFM         |
| opcua.contract.history.retention     | 4    | Out-of-window history read refused            |
| opcua.contract.terminate             | 3    | Sessions closed; certs rotated                |
