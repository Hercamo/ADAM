# SWIFT / ISO 20022 Adapter (v0.3, Contract-Bound, Day-1 PQC)

**Card ID:** `adapter-swift-iso20022`
**Version:** v0.3 (contract-bound)
**Status:** build-ready
**Supersedes:** `adapter-swift-iso20022__SWIFT_-_ISO_20022_Adapter.docx.BAK` (v0.2 — retained as old version)
**Contract pattern:** `_CONTRACT_SPEC.md`
**Used By:** `adamplus-fin-treasury`, `adamplus-fin-fx`, `wg-fin-txn`, `wg-fin-recon`, `wg-fin-audit`, `wg-gov-filing`

---

## 1. Target System

SWIFT FIN (legacy MT) and ISO 20022 (CBPR+, HVPS+, T2/T2S, FedNow ISO 20022, RTGS migrations). Channels: SWIFT Alliance Access / Alliance Cloud, SWIFTNet FileAct + InterAct, MQ Series bridge for some banks, SCORE/SIBOS workflows. Production scope: PAIN.001 (CustomerCreditTransferInitiation), PACS.008/PACS.009 (FIToFI), CAMT.052/053/054 (account reports/statements/notifications), PAIN.002 (status report). Legacy MT103 / MT202 / MT940 supported via translation layer.

## 2. Inbound + Outbound Capabilities

**Outbound:**
* Generate + sign ISO 20022 messages (PAIN.001, PACS.008, PACS.009).
* Submit via SWIFTNet InterAct or FileAct depending on bank corridor.
* Translate ADAM payment intents into MT103 where corridor still requires it (sunset-tracked).
* Emit XBRL/structured remittance attached to PAIN.001 where supported.

**Inbound:**
* Receive CAMT.052/053/054 statements via FileAct.
* Receive PAIN.002 status updates (RJCT/ACCP/ACSC).
* Receive MT9xx legacy statements; translate to CAMT canonical.

## 3. Auth + Identity

* SWIFT BIC + ITC (institution token) bound to ADAM-issued service identity.
* SWIFT PKI for non-repudiation: HSM-backed signing certs for InterAct/FileAct payload signing.
* `wg-sec-vault://swift/<bic>/pki` holds soft-HSM-wrapped private keys (until hardware HSM lands).
* mTLS to SWIFT VPN endpoint; egress allowlist limited to SWIFTNet IPs.
* Quantum lock: ML-KEM-1024 wrap, ML-DSA-65 dual-sign on bus.

## 4. Schema Mapping

| ISO 20022 Message      | ADAM Canonical                       | Notes                              |
|------------------------|--------------------------------------|------------------------------------|
| PAIN.001               | `treasury.payment_instruction`       | Customer-initiated credit transfer |
| PAIN.002               | `treasury.payment_status`            | Status report                      |
| PACS.008               | `treasury.fitofi_credit_transfer`    | Bank-to-bank                       |
| PACS.009               | `treasury.fi_credit_transfer`        |                                    |
| CAMT.052               | `treasury.account_report`            | Intraday                           |
| CAMT.053               | `treasury.account_statement`         | EOD                                |
| CAMT.054               | `treasury.account_notification`      | Debit/credit advice                |
| MT103                  | `treasury.payment_instruction.legacy`| Sunset-tracked                     |
| MT940/942              | `treasury.account_statement.legacy`  |                                    |

## 5. Idempotency

* Outbound PAIN.001 carries `MsgId` (UUID v7-derived) and per-transaction `EndToEndId`; both recorded in FR.
* Inbound dedup: `(MsgId, CreDtTm)` 7-day window (ISO 20022 standard duplicate window).
* Restart: replay-safe via FR-anchored MsgId journal.

## 6. Rate Limits

* SWIFT corridor TPS limits per bank — contract enforces 80% ceiling.
* CBPR+ batch caps respected.
* On corridor congestion: queue with FIFO + FR-anchored ordering.

## 7. Error Handling

* PAIN.002 RJCT codes mapped to canonical taxonomy; `AC03` (creditor account invalid), `AM05` (duplication), etc.
* MT NACK / MT103 RT — translated to canonical exception class.
* All errors dual-signed onto bus.

## 8. Residency

Critical. Each message scope is pinned to a permitted clearing system region (HVPS+ EU, T2 Eurozone, FedNow US, etc.) by contract. Cross-region or off-corridor routing is forbidden without RFM with `ga-legal` + `ga-financial` co-sign.

## 9. FR Events

```
adapter.swift.outbound.pain001.submitted / .accepted / .rejected
adapter.swift.outbound.pacs008.submitted / .accepted / .rejected
adapter.swift.inbound.camt052.received
adapter.swift.inbound.camt053.received
adapter.swift.inbound.camt054.received
adapter.swift.inbound.pain002.received
adapter.swift.legacy.mt103.translated
adapter.swift.legacy.mt940.translated
adapter.swift.duplicate.detected
adapter.swift.corridor.congestion
adapter.swift.signing.failed
```

## 10. Configuration Schema

```yaml
adapter_swift_iso20022:
  bic: "<MyBIC>"
  channel: "alliance-cloud"   # alliance-access | alliance-cloud | mq-bridge
  endpoints:
    interact: "https://swiftnet.swift.com/interact/<svc>"
    fileact:  "https://swiftnet.swift.com/fileact/<svc>"
  vault_handle: "wg-sec-vault://swift/<bic>/pki"
  corridors:
    - name: "CBPR+EUR"
      messages: ["PAIN.001", "PACS.008", "CAMT.053"]
      residency: "EU"
    - name: "FEDNOW"
      messages: ["PAIN.001", "CAMT.054"]
      residency: "US"
  legacy_mt:
    enabled: true
    sunset_after: "2027-11-30"
  contract_id: "adapter-swift-iso20022-contract"
```

## 11. Schemas Spoken

* ISO 20022 (PAIN.001, PAIN.002, PACS.008/009, CAMT.052/053/054).
* SWIFT MT (MT103, MT202, MT940, MT942) — legacy translation only.
* SWIFTNet InterAct / FileAct envelopes.
* SWIFT PKI (X.509, RFC 3739).
* CBPR+ usage guidelines.

## 12. Day-1 PQC Posture

* Bus emissions: hybrid Ed25519 + ML-DSA-65.
* SWIFT PKI: classical RSA-2048 / ECDSA P-256 (vendor-controlled). `qsuite=classical-fallback` recorded.
* Vault wrap: ML-KEM-1024.
* Internal signing audit log dual-signed.
* RFM filed automatically the moment SWIFT publishes a PQC suite — adapter is ready to switch.

## 13. Resource Profile

CPU 2 vCPU / 6 burst, RAM 2 GB, Disk 50 GB (statement archive cache), Net ≤500 Mbps.

## 14. Dependencies

`wg-sec-vault`, FR, `hi-intent`, `orch-policy`, `meta-stability`, `meta-integrity`, `wg-fin-txn`, `wg-fin-recon`, `wg-fin-audit`, `adam-adapter-contract-sdk`.

## 15. SLOs

PAIN.001 submission p95 ≤ 2.0 s; CAMT.053 ingestion within 5 min of corridor publish; availability ≥ 99.95%; refusal p99 ≤ 50 ms.

## 16. Build Plan

1. Pre-Action Gate via SDK.
2. ISO 20022 schema validation (XSD + CBPR+ usage guidelines).
3. PKI signer + soft-HSM with hardware-HSM stub for cutover.
4. Channel adapters (Alliance Cloud, FileAct).
5. Legacy MT translator with sunset tracker.
6. Statement reconciliation engine vs internal `treasury.payment_*` events.
7. QA pass1..5 + 360.

## 17. Definition of Done

`qa_all` / `qa_360` / `qa_pass3..5` 100/100; contract lifecycle green; CBPR+ usage-guideline conformance verified by ISO 20022 validator; signing failure path triggers self-suspend; `views_smoke` 70/70.

---

## 18. Contract Binding

* `contract_id`: `adapter-swift-iso20022-contract`
* `boss_score_floor`: **90** (highest financial materiality + non-repudiation; canonical 0..100 BOSS scale).
* `data_classes_allowed`: `pii`, `internal`, `restricted`, `pci-token`. PHI forbidden.
* `egress_allowlist`: SWIFTNet IPs on InterAct/FileAct ports (typical `<ip>:443` and `<ip>:48003`) from per-deployment addendum only — DNS-bypass via static IPs.
* `allowed_actions` (default): `pain001.submit`, `pacs008.submit`, `pacs009.submit`, `camt052.receive`, `camt053.receive`, `camt054.receive`, `pain002.receive`, `mt103.translate`, `mt940.translate`.
* `forbidden_actions`: `corridor.add`, `bic.modify`, `pki.cert.replace`, `legacy_mt.enable.beyond_sunset`, `cross_corridor.route`.

## 19. RFM Triggers

* Add a corridor (region or clearing system).
* Lift sunset on legacy MT.
* PKI cert replacement (off-cycle).
* Lift TPS ceiling.
* Crypto suite migration (when SWIFT publishes PQC).
* Add a new message class (e.g., HEAD.001 head-only flows).

## 20. Smart-Adapter Behaviors

* Validates every outbound message against XSD + CBPR+ usage guidelines BEFORE signing; refuses to sign a non-conformant message and emits `signing.refused`.
* Detects corridor sunset boundaries (e.g., MT-to-MX cutover dates) and auto-files RFM 90 days ahead.
* Maintains a duplicate-window cache per BIC/MsgId; refuses to re-submit an MsgId already accepted.
* On HSM key revocation, halts and rotates via Intent Object — never re-signs with a stale key.
* Reconciles CAMT.053 lines against internal `treasury.payment_*` events daily; emits `recon.divergence` on mismatch.

## 21. 360 QA Coverage

| Test ID                              | Pass | Outcome                                          |
|--------------------------------------|------|--------------------------------------------------|
| swift.contract.bind.happy            | 3    | Activates after dual-sign                        |
| swift.contract.refuse.bad_xsd        | 4    | Non-conformant message refused at sign           |
| swift.contract.refuse.cross_corridor | 4    | Cross-corridor routing refused                   |
| swift.contract.duplicate             | 4    | Duplicate MsgId refused; `duplicate.detected`    |
| swift.contract.recon.camt053         | 5    | Daily recon flags injected divergence            |
| swift.contract.rfm.corridor          | 5    | Adding FedNow corridor runs RFM with co-signs    |
| swift.contract.legacy.sunset         | 5    | Auto-RFM filed 90d ahead of MT sunset            |
| swift.contract.terminate             | 3    | PKI keys rotated; corridors closed               |
