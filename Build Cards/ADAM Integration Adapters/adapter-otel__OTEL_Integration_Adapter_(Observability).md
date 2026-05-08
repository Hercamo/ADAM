# OTEL Integration Adapter — Observability (v0.3, Contract-Bound, Day-1 PQC)

**Card ID:** `adapter-otel`
**Version:** v0.3 (contract-bound, dual-emit projection adapter)
**Status:** build-ready
**Supersedes:** none — new card. No `.docx.BAK` predecessor.
**Contract pattern:** `_CONTRACT_SPEC.md`
**Used By:** `meta-audit`, `meta-integrity`, `meta-stability`, `orch-evidence`, `orch-exception`, `orch-policy`, `orch-global`, `wg-fin-audit`, `wg-gov-compliance`, `wg-sec-incident`, `wg-sec-threat`, `wg-ops-resilience`, `wg-ops-recovery`, `wg-ops-bc`, `ai-audit-collect`, `ai-audit-correlate`, `ai-audit-simulate`, `ai-model-drift`, `ai-data-pipeline`, `ai-external-regulatory`, `ai-external-stakeholder`. Used by every ADAMPLUS pack indirectly through the Flight Recorder dual-emit pipeline. UI consumer: NetStreamX Directors Dashboard "FR Lifecycle" view (read-only projection).

---

## 1. Target System

OpenTelemetry-compliant observability stacks consumed via the in-cluster collector `adam-otel-collector` (namespace `adam-monitoring`, image `otel/opentelemetry-collector-contrib:0.92.0`, gRPC `:4317`, HTTP `:4318`) and any standards-compliant downstream the operator wires the collector to (Tempo, Jaeger, Honeycomb, Datadog, New Relic, Grafana Cloud, Elastic, Splunk, AWS X-Ray, Azure Monitor, GCP Cloud Trace, Lightstep, Dynatrace, etc.). Production scope: dual-emission of every Flight Recorder entry as an OTLP span and every BOSS Score evaluation as an OTLP evaluation event using ADAM's `agent_scope.*` semantic-convention namespace (the ADAM-prefixed superset that tracks the emerging OTel Agent/GenAI semantic conventions). Out of scope by default: ingesting external traces back into ADAM (one-way fan-out), modifying or deleting FR entries (chain remains source of truth), pushing decision-making over OTel (OTel is projection, never command). The chain is the source of truth; OTEL is the open-standard projection.

## 2. Inbound + Outbound Capabilities

**Outbound (the only direction this adapter normally takes):**

* `fr.span.emit` — every committed Flight Recorder entry produced as one OTLP span, parented by `intent_id` (root) and chained by `previous_hash → current_hash` link attributes.
* `boss.evaluation.emit` — every `boss_scored` FR entry additionally produced as an OTLP `evaluation` event (per emerging GenAI/Agent SemConv evaluation conventions) carrying the seven BOSS dimensions, composite score, routing tier, and policy provenance.
* `governance.span.emit` — convenience subset for governance-class events (`governor_evaluated`, `governors_concurred`, `governor_blocked`, `director_proxy_acting`, `director_approval`, `director_rejection`, `delegation_*`).
* `exception.span.emit` — `exception_emitted` and `exception_resolved` projected with Exception Economy routing tier as a span attribute.
* `pqc.span.emit` — `pqc_key_rotation_*` projected with cryptographic posture attributes.
* `metric.export` — counters and histograms aggregated from FR (entries/sec by `event_type`, BOSS composite distribution, exception-tier counters, governor concurrence latency, dual-sign verification latency).
* `log.export` — operator-readable structured log lines for every emitted span, mirroring FR `evidence` field minimally.
* `selftest.heartbeat` — adapter heartbeat and contract-head attestation projected as a heartbeat span every 30 s.

**Inbound (gated; default deny):**

* `collector.healthcheck` — pull-only: read `:13133` health endpoint of the local collector for the adapter's preflight; never accepts external OTLP back into ADAM.
* `webhook.opamp` — Open Agent Management Protocol pull from operator-controlled config server (RFM-gated; default off).

The adapter is a **one-way fan-out projector**. Inbound traces, metrics, or logs from any external observability backend are refused by default and require RFM with `ga-security` + `meta-integrity` co-sign before any external signal can re-enter ADAM (and even then, never as an FR-mutating signal).

## 3. Auth + Identity

* mTLS to `adam-otel-collector.adam-monitoring.svc.cluster.local:4317` using a per-instance client cert vaulted at `wg-sec-vault://otel/<tenant>/collector-client`. Server identity pinned to the collector's CA bundle (rotated on the platform PKI cycle).
* Optional bearer header for downstream-collector-fanout when the operator wires the collector to a SaaS backend; the bearer is held by the collector, **never by this adapter**. The adapter never sees vendor credentials.
* OPAMP (when enabled): per-instance mTLS to operator config server vaulted at `wg-sec-vault://otel/<tenant>/opamp-client`.
* Quantum lock: ML-KEM-1024 wrap, ML-DSA-65 dual-sign on every bus emission. Hybrid X25519+ML-KEM-768 mTLS to the collector when the collector advertises hybrid capability; classical fallback recorded as `qsuite=classical-fallback` on every emitted event.
* The adapter holds **no live credentials in memory** beyond the in-flight session ticket; vault handle is the only source.
* Read-only on FR: the adapter holds an **FR replication-stream subscriber token**, scope `subscribe-only`. It cannot append, mutate, or delete FR entries. Append capability is reserved to the FR writer set; this is enforced by capability-token type and by the FR's WORM mount.

## 4. Schema Mapping

| ADAM Concept (FR/BOSS/Intent)             | OTEL Surface                                                                                          | `agent_scope.*` Attribute Keys                                                                                                                                                                                                                                  |
|-------------------------------------------|-------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `entry_id`                                | `span.attributes["agent_scope.fr.entry_id"]`                                                          | UUIDv4/v7                                                                                                                                                                                                                                                    |
| `seq`                                     | `span.attributes["agent_scope.fr.seq"]`                                                               | int64                                                                                                                                                                                                                                                        |
| `timestamp`                               | span `start_time` (nanosecond precision)                                                              | RFC3339 → unix_nano                                                                                                                                                                                                                                          |
| `event_type`                              | `span.name` and `span.attributes["agent_scope.fr.event_type"]`                                        | exact FR enum value (e.g. `boss_scored`, `governors_concurred`, `action_executed`, `pqc_key_rotation_completed`)                                                                                                                                              |
| `agent_id`                                | `span.attributes["agent_scope.agent.id"]` and resource attribute `service.name`                        | e.g. `meta-stability`                                                                                                                                                                                                                                        |
| `agent_class`                             | `span.attributes["agent_scope.agent.class"]`                                                          | e.g. `meta`, `governor`, `orchestrator`, `human-interface`, `corporate-workgroup`, `ai-centric`, `digital-twin`                                                                                                                                              |
| `intent_id`                               | trace `trace_id` (deterministic 128-bit hash of `intent_id`)                                          | every FR entry of an intent shares one trace                                                                                                                                                                                                                 |
| `action_id`                               | `span.attributes["agent_scope.action.id"]`                                                            | UUID                                                                                                                                                                                                                                                          |
| `doctrine_version`                        | resource attribute `agent_scope.doctrine.version` (e.g. `adam-book-new@v0.3`)                          | sealed at emission                                                                                                                                                                                                                                            |
| `hash_chain.previous_hash`                | `span.links[0].trace_id || link attr "agent_scope.fr.prev_hash"`                                      | SHA-256 / SHA-3-256                                                                                                                                                                                                                                          |
| `hash_chain.current_hash`                 | `span.attributes["agent_scope.fr.current_hash"]`                                                       | SHA-256 / SHA-3-256                                                                                                                                                                                                                                          |
| `hash_chain.algorithm`                    | `span.attributes["agent_scope.fr.hash_alg"]`                                                          | `SHA-256` or `SHA3-256`                                                                                                                                                                                                                                       |
| `hash_chain.anchor_id`                    | `span.attributes["agent_scope.fr.anchor_id"]`                                                         | optional                                                                                                                                                                                                                                                      |
| `cryptographic_proof.signature_algorithm` | `span.attributes["agent_scope.fr.sig_alg"]`                                                            | `Ed25519` / `ECDSA-P256` / `ML-DSA-65`                                                                                                                                                                                                                        |
| `cryptographic_proof.signing_key_id`      | `span.attributes["agent_scope.fr.sig_key_id"]`                                                         | vault key handle (no key material)                                                                                                                                                                                                                            |
| `tamper_evident.attestations[]`           | `span.attributes["agent_scope.fr.attestations"]`                                                      | JSON-array string of secondary signature objects (the ML-DSA-65 + SLH-DSA anchor pair)                                                                                                                                                                       |
| `evidence` (object)                       | `span.attributes["agent_scope.fr.evidence_digest"]` + `agent_scope.fr.evidence_size_bytes`             | the **digest** is emitted, **not** the body, by default; bodies emitted only when contract `data_classes_allowed` permits and the evidence is `internal` or `public`                                                                                          |
| `worm`, `tamper_evident`                  | `span.attributes["agent_scope.fr.worm"]` / `agent_scope.fr.tamper_evident`                            | bool                                                                                                                                                                                                                                                          |
| BOSS dim `security_impact`                | event attribute `agent_scope.boss.dim.security_impact`                                                 | 0..100                                                                                                                                                                                                                                                        |
| BOSS dim `sovereignty_action`             | event attribute `agent_scope.boss.dim.sovereignty_action`                                              | 0..100                                                                                                                                                                                                                                                        |
| BOSS dim `financial_exposure`             | event attribute `agent_scope.boss.dim.financial_exposure`                                              | 0..100                                                                                                                                                                                                                                                        |
| BOSS dim `regulatory_impact`              | event attribute `agent_scope.boss.dim.regulatory_impact`                                               | 0..100                                                                                                                                                                                                                                                        |
| BOSS dim `reputational_risk`              | event attribute `agent_scope.boss.dim.reputational_risk`                                               | 0..100                                                                                                                                                                                                                                                        |
| BOSS dim `rights_certainty`               | event attribute `agent_scope.boss.dim.rights_certainty`                                                | 0..100                                                                                                                                                                                                                                                        |
| BOSS dim `doctrinal_alignment`            | event attribute `agent_scope.boss.dim.doctrinal_alignment`                                             | 0..100                                                                                                                                                                                                                                                        |
| BOSS `composite_score`                    | event attribute `agent_scope.boss.composite_score`                                                     | 0..100                                                                                                                                                                                                                                                        |
| BOSS `routing_tier`                       | event attribute `agent_scope.boss.routing_tier`                                                        | enum `soap` / `moderate` / `elevated` / `high` / `ohshat`                                                                                                                                                                                                    |
| BOSS `is_non_idempotent`                  | event attribute `agent_scope.boss.is_non_idempotent`                                                   | bool                                                                                                                                                                                                                                                          |
| BOSS `critical_override_applied`          | event attribute `agent_scope.boss.critical_override_applied`                                           | bool                                                                                                                                                                                                                                                          |
| BOSS `policy_provenance[]`                | event attribute `agent_scope.boss.policy_provenance` (JSON-array string)                               | array of `{policy_id, version, hash}`                                                                                                                                                                                                                          |
| Intent `urgency`                          | trace attribute `agent_scope.intent.urgency`                                                           | `routine` / `elevated` / `critical` / `emergency`                                                                                                                                                                                                            |
| Intent `source.role`                      | trace attribute `agent_scope.intent.role`                                                              | `director` / `executive` / `operator` / `system` / `customer`                                                                                                                                                                                                |
| Intent `source.director_id`               | trace attribute `agent_scope.intent.director_id`                                                      | one of `ceo`, `cfo`, `legal_director`, `market_director`, `ciso`, `cpo`, `cto`                                                                                                                                                                               |
| Intent `replay_marker.original_intent_id` | trace attribute `agent_scope.intent.replay_of`                                                        | UUID                                                                                                                                                                                                                                                          |
| Adapter contract head hash                | resource attribute `agent_scope.contract.head_hash`                                                    | SHA-3-512 (per `_CONTRACT_SPEC.md` §2.1 `fr_anchor_hash`)                                                                                                                                                                                                    |
| `qsuite=classical-fallback` flag          | resource attribute `agent_scope.pqc.qsuite`                                                           | enum `hybrid-pqc` / `classical-fallback`                                                                                                                                                                                                                     |

`agent_scope.*` is the ADAM-prefixed superset of the emerging OTel Agent / GenAI semantic conventions. Where OTel canonicalises a key (e.g. `gen_ai.system`, `gen_ai.evaluation.score`), the adapter emits **both** the canonical OTel key and the `agent_scope.*` mirror, so a vendor stack that only knows OTel canonical keys still gets a useful trace, and an ADAM-aware stack gets the full doctrine context.

## 5. Idempotency

* Every FR entry has a unique `(entry_id, seq)`; the adapter keys its outbound OTLP exporter on `seq` and persists the **last successfully exported `seq`** in a local idempotency journal at `/var/lib/adam-otel/state.db` (SQLite, fsync per write).
* On restart, the adapter resumes from `last_seq + 1`; on collector outage, batches buffer to disk WAL and replay on reconnect with the same `seq`.
* OTLP collectors are themselves idempotent on `(trace_id, span_id)`; the adapter derives `trace_id` deterministically from `intent_id` and `span_id` from `entry_id`, so duplicate emission of the same FR entry produces an identical span and is silently de-duplicated downstream.
* Boss-evaluation events are keyed by `(intent_id, score_id)`.
* Heartbeat spans are keyed by `(adapter_instance_id, heartbeat_seq)`.
* Reconciliation job (§16, §20) walks `[FR.head_seq] - [last_exported_seq]` daily and re-emits any gap; gap detection emits `adapter.otel.gap.detected` on the bus.

## 6. Rate Limits

* No external rate ceiling (in-cluster collector); contract `rate_ceiling_per_min` set to 80% of the collector's tested burst (default `60_000` spans/min per adapter instance, tuned per deployment).
* Sustained-load self-throttle: when collector RTT p95 > 200 ms for 30 s, the adapter sheds metric exports first (lowest priority), then heartbeat spans, **never** FR-projection spans. FR projection is the contracted obligation; metrics and heartbeats are convenience.
* When self-throttle engages, an `adapter.otel.rate.pressure` event is emitted on the bus, and the FR-projection backlog is buffered to disk WAL (default cap `2 GiB`, configurable, alarms at 80%).

## 7. Error Handling

* Collector unreachable (TCP refused / TLS handshake failure / 5xx): exponential backoff with jitter (1 s → 60 s cap), buffer to WAL, emit `adapter.otel.collector.unreachable`. Adapter never blocks FR writers; FR remains the source of truth.
* Collector returns OTLP `PartialSuccess.rejected_spans > 0`: capture the rejection reason, emit `adapter.otel.span.rejected` with the FR `entry_id` and the collector's reason, and (a) re-shape if the rejection is a known schema mismatch the adapter can correct without losing fidelity, (b) park-and-alert if not. Never silently drop.
* Hash-chain inconsistency at the adapter (the FR replication stream delivers an entry whose `previous_hash` does not match the prior `current_hash`): emit `adapter.otel.fr.chain_break_observed` immediately, halt projection, page `meta-integrity` and `wg-sec-incident`. Critical incident; do **not** advance `last_seq`.
* Dual-signature verification fails on a replicated FR entry: emit `adapter.otel.fr.signature_invalid`, halt, page `meta-integrity` and `ga-security`. The adapter refuses to project events it cannot verify.
* OPAMP config push from operator that would change `data_classes_allowed` or `forbidden_actions` is refused at the adapter; OPAMP can adjust sampling and exporter endpoints only, never policy.
* Vault unreachable on cold start: refuse to start (no credentials, no projection); emit `adapter.contract.bind_failed` per `_CONTRACT_SPEC.md` §4.

## 8. Residency

* Collector and any downstream backend MUST be in the same residency cell as the FR they project; the contract pins `external_system.residency` to one or more ISO-3166 region codes (or vendor-specific corridor identifiers per `_CONTRACT_SPEC.md` §10 note).
* Cross-region projection is forbidden by default; an RFM is required to enable additional egress allowlist entries that span regions.
* For data classes `pii`, `phi`, `pci`, the default behaviour is **digest-only** (`evidence` body redacted to a SHA-3-256 digest); body emission requires explicit per-event allow in the contract and a runtime predicate that the consuming backend is in-residency. Refuse otherwise.

## 9. FR Events

```
adapter.otel.span.emitted
adapter.otel.span.rejected
adapter.otel.evaluation.emitted
adapter.otel.metric.exported
adapter.otel.log.exported
adapter.otel.heartbeat.emitted
adapter.otel.collector.unreachable
adapter.otel.collector.recovered
adapter.otel.gap.detected / .gap.repaired
adapter.otel.fr.chain_break_observed
adapter.otel.fr.signature_invalid
adapter.otel.rate.pressure / .rate.recovered
adapter.otel.opamp.config.received / .opamp.config.refused
adapter.otel.recon.divergence
adapter.otel.schema.drift.detected
```

## 10. Configuration Schema

```yaml
adapter_otel:
  instance_id: "<uuid7-per-instance>"
  collector:
    endpoint: "https://adam-otel-collector.adam-monitoring.svc.cluster.local:4317"
    protocol: "grpc"           # grpc | http
    tls:
      enabled: true
      ca_bundle: "wg-sec-vault://platform/ca-bundle"
      mtls_client: "wg-sec-vault://otel/<tenant>/collector-client"
      hybrid_pqc: true         # X25519+ML-KEM-768 if collector advertises
    healthcheck_url: "http://adam-otel-collector.adam-monitoring.svc.cluster.local:13133/health"
  fr_subscriber:
    stream: "flight-recorder://committed"
    cursor_path: "/var/lib/adam-otel/cursor"
    capability_token: "wg-sec-vault://fr/subscribers/adapter-otel"
    verify_dual_signature: true   # never disable
  emission:
    batch:
      max_spans: 512
      max_bytes: 1048576       # 1 MiB
      flush_interval_ms: 1000
    sampling:
      mode: "all"              # all | tier-weighted (BOSS-tier-aware)
      tier_weights:
        soap: 1.0
        moderate: 1.0
        elevated: 1.0
        high: 1.0
        ohshat: 1.0            # never drop ohshat; default 1.0 across tiers
    body_redaction:
      default: "digest-only"   # digest-only | full
      allow_full_for_classes: ["public"]
  wal:
    path: "/var/lib/adam-otel/wal"
    max_bytes: 2147483648      # 2 GiB
    fsync_on_write: true
  opamp:
    enabled: false             # default off; RFM to enable
    server_url: ""
    mtls_client: "wg-sec-vault://otel/<tenant>/opamp-client"
  semantic_conventions:
    namespace: "agent_scope"
    mirror_otel_canonical: true   # emit both `agent_scope.*` and OTel canonical keys
  contract_id: "adapter-otel-contract"
```

## 11. Schemas Spoken

* OTLP/gRPC and OTLP/HTTP (OpenTelemetry Protocol v1).
* OpenTelemetry Resource SemConv (service.\*, telemetry.sdk.\*, deployment.environment).
* OpenTelemetry Trace SemConv (general).
* `agent_scope.*` ADAM-prefixed namespace (this card is the canonical reference for the namespace).
* OTel emerging Agent / GenAI SemConv (`gen_ai.*`) — mirrored when applicable.
* OPAMP v1.0 (Open Agent Management Protocol; gated, read-only config pull).
* Flight Recorder schema v2.1 (`https://adam.io/schemas/flight-recorder/v2.1`) — read-only consumer.
* BOSS Score schema (`boss-score-schema.json`) — read-only consumer.
* Intent Object schema v1.1 (`https://adam.io/schemas/intent-object/v1.1`) — read-only consumer.

## 12. Day-1 PQC Posture

* Bus emissions: hybrid Ed25519 + ML-DSA-65 (NIST FIPS 204) on every event.
* Collector mTLS: hybrid X25519+ML-KEM-768 (NIST FIPS 203) when the collector advertises the suite; classical X25519 fallback otherwise with `qsuite=classical-fallback` recorded as a resource attribute on every emitted span and on the bus event for that emission.
* Vault wrap of any persisted credential / cursor cipher: ML-KEM-1024.
* Long-term anchor: the adapter projects (does not produce) the FR's SLH-DSA (NIST FIPS 205) anchor on every span as `agent_scope.fr.attestations`. The adapter never strips an attestation from the projection; doing so would break replay-evidence guarantees.
* Dual-signature verification of every replicated FR entry is mandatory; failure halts the adapter and pages security. There is no "soft-verify" mode.

## 13. Resource Profile

* CPU: 1 vCPU steady, 4 vCPU burst (per instance; horizontally scalable, partitioned by `entry_id` hash modulo instance count).
* Memory: 1 GiB steady, 4 GiB burst (WAL is on disk, not memory).
* Disk: 10 GiB ephemeral for cursor + idempotency journal + WAL (default cap; `wal.max_bytes` raises ceiling).
* Network: ≤500 Mbps egress to in-cluster collector; near-zero external egress (collector handles fan-out).

## 14. Dependencies

`wg-sec-vault`, FR (read-only subscriber), `hi-intent`, `orch-policy`, `orch-evidence`, `meta-stability`, `meta-integrity`, `meta-audit`, `wg-sec-incident`, `adam-adapter-contract-sdk`. Platform deployments: `adam-otel-collector` (Helm chart `adam-platform.monitoring`, manifest `kubernetes/helm/adam-platform/templates/monitoring.yaml`).

## 15. SLOs

* Span emission p95 ≤ **50 ms** from FR commit to OTLP `Export` ack (in-cluster collector).
* Span emission p99 ≤ **200 ms**.
* BOSS evaluation event p95 ≤ **80 ms** from `boss_scored` FR commit.
* Adapter availability ≥ **99.99%** (the FR is the source of truth, but operators expect projection to keep up).
* WAL drain after collector recovery: backlog ≤ 1 GiB drains in ≤ 5 min; ≤ 2 GiB in ≤ 10 min.
* Refusal latency p99 ≤ **20 ms** (cheap on the hot path; the projection contract must not back-pressure FR writers).
* Reconciliation job (daily): ≤ 30 min for a 100M-entry FR.
* Zero FR entries lost across a tested 24 h collector outage (WAL must be sized accordingly; alarmed at 80%).

## 16. Build Plan

1. Pre-Action Gate via `adam-adapter-contract-sdk`. Refusal hot path uses cached contract head; no syscall on refusal.
2. FR replication-stream subscriber (read-only capability token); local cursor at `/var/lib/adam-otel/cursor` with fsync per advance.
3. Dual-signature verification per replicated entry (Ed25519 + ML-DSA-65); SLH-DSA anchor verification on chain-roll snapshots.
4. Hash-chain validator: every entry's `previous_hash` MUST match the local mirror's prior `current_hash`. Mismatch ⇒ halt + page.
5. Span builder: deterministic `trace_id` from `intent_id` (SHA-256(intent_id)[0:16]) and `span_id` from `entry_id` (SHA-256(entry_id)[0:8]); maps every FR field to `agent_scope.*` per §4 and mirrors OTel canonical keys.
6. BOSS evaluation event builder: emits a span event with all seven dimensions, composite, routing tier, `is_non_idempotent`, `critical_override_applied`, and `policy_provenance` (JSON-array attribute).
7. OTLP exporter (gRPC primary, HTTP fallback) with batch + WAL; mTLS client cert from vault; hybrid PQC suite negotiation on TLS handshake.
8. WAL writer + drain loop with fsync; bounded by `wal.max_bytes`; alarms at 80%.
9. Self-throttle: collector RTT p95 watcher; sheds metrics → heartbeats → never FR projection.
10. Reconciliation job (daily): walk `[head_seq] - [last_exported_seq]`; re-emit any gap; emit `adapter.otel.recon.divergence` if collector storage lacks an entry the adapter says it exported.
11. OPAMP client (default disabled; RFM-gated) for sampling + endpoint config only — never policy.
12. Heartbeat span every 30 s carrying current `agent_scope.contract.head_hash`.
13. Per-tenant resource attribute injection (`adam.tenant`, `adam.cell`, `agent_scope.doctrine.version`).
14. Helm overlay `kubernetes/helm/adam-platform/templates/otel-adapter.yaml` (Deployment + ServiceAccount + NetworkPolicy egress fence), wired to existing `adam-otel-collector`. Manifest twin for non-Helm deployments under `deploy/manifests/55-otel-adapter.yaml`.
15. Wire the FR Lifecycle view in the NetStreamX Directors Dashboard to read the same OTLP endpoint via Tempo/Jaeger query API for "drill-into trace from FR entry"; this is a UI consumer of the adapter's output, not part of the adapter itself.
16. QA pass1..5 + 360.

## 17. Definition of Done

* `qa_all` 100/100; `qa_360` 100/100; `qa_pass3..5` 100/100 each.
* `views_smoke` 70/70, including a new view-smoke that drills from the FR Lifecycle entry into a Tempo/Jaeger trace and confirms parity (entry_id, seq, hash chain, BOSS dims when applicable).
* Contract lifecycle green: bind → activate → amend (sampling change via RFM) → terminate.
* Chain-break negative test: synthetic chain break in a replication stream halts the adapter and emits `fr.chain_break_observed`.
* Dual-signature negative test: tampered ML-DSA-65 signature halts the adapter and emits `fr.signature_invalid`.
* Collector-outage test: 24 h synthetic collector outage drains cleanly from WAL with zero FR entries lost.
* Reconciliation test: gap injected in exported set is detected within one daily run and repaired idempotently.
* Body-redaction test: `pii`/`phi`/`pci` evidence appears as digest-only in projected spans by default; full body forbidden by contract refusal.
* OPAMP refusal test: a config push that attempts to widen `data_classes_allowed` is refused with `opamp.config.refused`.
* Index entry added to `_INDEX.md`; QA log appended to `_QA_LOG.md` (Pass A→D record + clean-pass attestation).
* Upgrade entry written to `D:\ADAM\upgrade_log\UPGRADE_LOG.md`.

---

## 18. Contract Binding

* `contract_id`: `adapter-otel-contract`
* `boss_score_floor`: **80** (telemetry projection is high-leverage but read-only against FR; canonical 0..100 BOSS scale).
* `data_classes_allowed`: `internal`, `public`. PII / PHI / PCI evidence is **digest-only** by default — body emission of those classes requires per-event predicate allow + RFM amendment; raw PII / PHI / PCI bodies in spans are forbidden by contract.
* `egress_allowlist`:
  * `adam-otel-collector.adam-monitoring.svc.cluster.local:4317`
  * `adam-otel-collector.adam-monitoring.svc.cluster.local:4318`
  * `adam-otel-collector.adam-monitoring.svc.cluster.local:13133` (health, read-only)
  * OPAMP server entry only when OPAMP is RFM-enabled per deployment addendum (no DNS resolution outside the allowlist; seccomp/CNI mirror).
* `allowed_actions` (default):
  * `fr.span.emit`
  * `boss.evaluation.emit`
  * `governance.span.emit`
  * `exception.span.emit`
  * `pqc.span.emit`
  * `metric.export`
  * `log.export`
  * `selftest.heartbeat`
  * `collector.healthcheck`
  * `recon.run`
* `forbidden_actions`:
  * `fr.append` (cannot mutate the chain — capability-token prohibits it; reasserted in contract for defence-in-depth)
  * `fr.delete` / `fr.modify`
  * `inbound.trace.ingest` (default deny; RFM + `meta-integrity` + `ga-security` co-sign required)
  * `policy.modify`
  * `boss.score.synthesise` (the adapter projects scores; it never produces them)
  * `governor.cosign` (adapter never participates in governance — only translates)
  * `webhook.opamp.policy_change` (OPAMP is restricted to sampling + endpoint config; any policy delta refused)
  * `evidence.body.emit_for_pii_phi_pci` (without per-event predicate allow)
  * `egress.dns_resolve_outside_allowlist`
  * `cross_region.span.emit` (without RFM)

## 19. RFM Triggers

* Adding any inbound capability (e.g. ingesting external traces back into ADAM under any conditions).
* Enabling OPAMP in production.
* Promoting `evidence.body.emit_for_pii_phi_pci` from forbidden to per-event allow.
* Adding a downstream collector fan-out target outside the current residency cell.
* Lifting the per-instance rate ceiling.
* Changing the semantic-convention namespace prefix (e.g. when OTel canonicalises an Agent/GenAI namespace and ADAM aligns).
* Changing the `trace_id` derivation function (would invalidate cross-system trace continuity for prior intents).
* Crypto evolution (collector hybrid PQC support flips, vault wrap algorithm change, SLH-DSA parameter change).
* Disabling dual-signature verification (forbidden under any circumstance — RFM would be refused at doctrine check).

## 20. Smart-Adapter Behaviors

* **Read-only by capability.** The adapter holds an FR `subscribe-only` capability token. Append, mutate, and delete operations are syscall-impossible because the FR's WORM mount and the writer-set ACL exclude this adapter's identity. The forbidden-actions clause is defence-in-depth, not the primary control.
* **Chain-mirror invariant.** The adapter maintains a local hash mirror of FR. Every replicated entry's `previous_hash` MUST equal the local mirror's prior `current_hash`. A break is treated as a doctrinal incident, not a bug — halts projection, pages `meta-integrity` and `wg-sec-incident`, emits `fr.chain_break_observed`. Recovery requires a doctrinal review per the Flight Recorder corruption history runbook (see `D:\ADAM\upgrade_log\UPGRADE_LOG.md` and the named-volume structural fix).
* **Deterministic trace and span IDs.** `trace_id = SHA-256(intent_id)[0:16]`; `span_id = SHA-256(entry_id)[0:8]`. Re-emission produces identical IDs, so any OTLP-compliant backend de-duplicates naturally; the adapter does not need a "do-once" guard for correctness, only for efficiency.
* **Lossless projection of attestations.** The adapter never strips, summarises, or re-signs FR attestations. The dual signature (Ed25519 + ML-DSA-65) and the SLH-DSA long-term anchor are projected verbatim into `agent_scope.fr.attestations` so that an external auditor can verify the full doctrine-cryptographic posture from the OTLP trace alone.
* **Body redaction is contract-driven, not opportunistic.** PII / PHI / PCI bodies are digest-only by contract; the digest algorithm matches FR's `hash_chain.algorithm` (SHA-256 default, SHA-3-256 when the FR entry uses it), so an auditor with the original evidence body in FR can re-derive the digest and confirm the projection matches.
* **OPAMP is surface-bounded.** Operator configuration via OPAMP is permitted to alter sampling weights and exporter endpoints only. Any payload that would change `data_classes_allowed`, `egress_allowlist`, `forbidden_actions`, or attempt to disable verification is refused on receipt and emits `opamp.config.refused`.
* **No back-channel.** The adapter has no path by which an OTLP backend can issue a command back into ADAM. Even on `webhook.opamp` (when enabled), OPAMP messages are policy-gated and have no `fr.*` capability.
* **Daily reconciliation against backend.** A reconciliation job (daily, off-peak) walks `[FR.head_seq] - [last_exported_seq]` and queries the configured backend (Tempo/Jaeger) to confirm presence of every span the adapter says it exported. Divergence emits `recon.divergence` with the missing `entry_id` set; never silently re-emits without an Intent Object for the repair if divergence exceeds 0.1% of a daily window.
* **Schema-drift detection.** When OTel publishes a new SemConv version, or when the FR schema reifies v2.2 (per `_CONTRACT_SPEC.md` header forward-looking notes), the adapter detects the version delta on cold start and emits `schema.drift.detected`; if the delta is in the FR direction (chain or attestations), the adapter halts and files an RFM. If the delta is in the OTel direction (additive attribute keys), the adapter mirrors and continues.
* **Dual-emit ordering.** A span is emitted only after the FR entry is committed and verified. The adapter never speculatively emits ahead of FR commit; the chain remains the source of truth and OTel never sees an event that did not happen in the chain.
* **Refusal is first-class.** Every contract refusal emits `adapter.otel.span.rejected` (or the appropriate `adapter.contract.refused` event from the shared spec) with the reason taxonomy from `_CONTRACT_SPEC.md` §10. Operators can dashboard refusal rate as a first-class signal.
* **Heartbeat carries contract head.** Every 30 s a heartbeat span carries `agent_scope.contract.head_hash`. Operators can detect silent contract divergence between adapter instances by trace search.
* **No latent state outside FR + vault + WAL + cursor.** A destroyed and respawned instance reconciles from cursor + FR head; the WAL drains; identity is re-issued from vault. Safe to redeploy at any time.

## 21. 360 QA Coverage

| Test ID                              | Pass | Outcome                                                                                                  |
|--------------------------------------|------|----------------------------------------------------------------------------------------------------------|
| otel.contract.bind.happy             | 3    | Activates after dual-sign verified; first heartbeat span carries contract head hash                      |
| otel.contract.refuse.fr_append       | 4    | Synthetic call to `fr.append` refused by capability token AND by Pre-Action Gate (defence in depth)      |
| otel.contract.refuse.body_pii        | 4    | Span carrying raw PII evidence body refused; digest-only projection emitted instead                       |
| otel.contract.refuse.inbound_ingest  | 4    | Inbound trace ingest refused (`inbound.trace.ingest` not in `allowed_actions`)                            |
| otel.contract.refuse.opamp_policy    | 4    | OPAMP push that widens `data_classes_allowed` refused with `opamp.config.refused`                         |
| otel.contract.refuse.cross_region    | 4    | Cross-region collector target refused without RFM                                                         |
| otel.contract.refuse.dns_off_allow   | 4    | Egress to DNS-resolved target outside allowlist refused at CNI/seccomp                                    |
| otel.contract.fr.chain_break         | 4    | Synthetic chain break in replication stream halts adapter and emits `fr.chain_break_observed`            |
| otel.contract.fr.sig_invalid         | 4    | Tampered ML-DSA-65 signature halts adapter and emits `fr.signature_invalid`                              |
| otel.contract.dual_emit.fr_entry     | 3    | Every committed FR entry produces exactly one OTLP span; trace_id deterministic from `intent_id`         |
| otel.contract.dual_emit.boss_score   | 3    | Every `boss_scored` FR entry additionally produces an evaluation event with all 7 dims + tier            |
| otel.contract.dual_emit.exception    | 3    | `exception_emitted` projected with Exception Economy tier attribute                                      |
| otel.contract.dual_emit.pqc_rotation | 3    | `pqc_key_rotation_completed` projected with crypto posture attributes                                    |
| otel.contract.collector.outage_24h   | 4    | 24 h synthetic collector outage; WAL drains on recovery with zero entries lost                           |
| otel.contract.recon.divergence       | 5    | Missing span at backend detected by daily recon; `recon.divergence` emitted with the gap set              |
| otel.contract.rfm.opamp_enable       | 5    | Enabling OPAMP runs full RFM; default is refused without governor co-sign                                |
| otel.contract.rfm.body_pii_predicate | 5    | Per-event PII body emission RFM requires `ga-security` + `ga-legal` + `meta-integrity` co-sign            |
| otel.contract.rfm.cross_region       | 5    | Cross-region addendum runs full RFM with `wg-data-residency` co-sign                                     |
| otel.contract.attest.fail            | 4    | Effective scope mismatch vs contract triggers self-suspend                                                |
| otel.contract.semconv_mirror         | 1    | Every emitted span carries both `agent_scope.*` and the canonical OTel mirror keys                        |
| otel.contract.attestations_passthrough| 2   | SLH-DSA + ML-DSA-65 attestations projected verbatim into `agent_scope.fr.attestations`                    |
| otel.contract.heartbeat.head_hash    | 4    | Heartbeat span every 30 s carries `agent_scope.contract.head_hash`                                        |
| otel.contract.terminate              | 3    | Cursor sealed; WAL drained; mTLS client cert revoked at vault; capability token revoked at FR             |
| otel.contract.views_smoke.drill      | 5    | FR Lifecycle view drill-down opens the matching trace in Tempo/Jaeger; entry_id, seq, hash chain match    |
