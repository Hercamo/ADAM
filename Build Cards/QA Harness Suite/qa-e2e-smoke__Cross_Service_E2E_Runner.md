# ADAM Build Card — QA Cross-Service E2E Runner

**Card ID:** `qa-e2e-smoke`
**Class:** Verification Tool — Smoke
**Subgroup / Plane:** QA Harness Suite — Black-Box Cross-Service
**Conformance:** ADAM Book New / BOSS / Flight Recorder Schema / RGI / 5+2 Director Constitution / Day-1 PQC
**Doctrinal status:** Operator support tool. Not part of doctrine.

## 1. Identity & Authority

| Field | Value |
|---|---|
| Card ID | `qa-e2e-smoke` |
| Canonical Name | QA Harness Suite — Cross-Service End-to-End Runner |
| Class | Verification Tool — Smoke |
| Owning Domain Governor | None (operator-owned tool) |
| Accountable Director | CISO + Operations & Delivery |
| Doctrine Cross-Refs | QA Harness Suite — Quality Built In Part IV §4.6; Flight Recorder schema; BOSS Score Formulas; RGI contracts |

## 2. Mission

Stand up every backend service in-process — Flight Recorder, BOSS, AGT-Full, the customer-facing application — drive a full customer flow across services, and verify the cross-service events landed in the chain in the expected shape and order.

## 3. In-Scope Responsibilities

- Start FR / BOSS / AGT-Full / app in-process on localhost ports (e.g., 18200, 18210, 18400, 18500).
- Drive ~25 cross-service calls covering the canonical customer flow (signup, playback authorisation, recommendation, dispute, dunning).
- After the flow completes, open the chain SQLite read-only and verify the expected events appear with the expected `intent_id` lineage.
- Tear down each in-process server cleanly on success or failure.

## 4. Explicitly Out of Scope

- Long-running soak testing. The smoke is a short, deterministic shape check.
- UI-level interaction. The smoke is API-driven.

## 5. Inputs

- Deployment root.
- Path to (or in-process construction of) chain SQLite.
- Path to legacy Ed25519 key.
- Localhost port allocations for the four services.

## 6. Outputs (Flight Recorder & Side Effects)

- Stdout: per-step `PASS` / `FAIL` lines.
- Exit code: failure count.
- Chain events written into the temporary chain during the run; the temporary chain is removed on exit unless `--keep` is set.

## 7. Public API / Invocation

```bash
python3 deployment/<profile>/qa/e2e_smoke.py [--root PATH] [--chain PATH] [--legacy-key PATH]
```

## 8. State & Persistence

Temporary chain SQLite during the run; removed on exit.

## 9. BOSS v3.2 Touch Points

Every action that crosses BOSS during the flow is scored. The smoke asserts the routing tier matches the expectation per action.

## 10. Governor / Director Concurrence

None.

## 11. RGI Contracts & OPA Rego Hooks

Read-only against the running services. The services themselves write through RGI as normal.

## 12. Failure Modes & Safe-Mode

Service start-up failure; port conflict; cross-service event drift; chain-shape mismatch. Each surfaces as a FAIL row.

## 13. Resource Profile

Single Python host; ~2 GB RAM at reference scale; < 60 s wall-clock at reference scale.

## 14. Dependencies

- Python 3.10+; the four backend service modules importable on the local Python path; `urllib`.

## 15. SLOs & Mandate Alignment

| Metric | Target |
|---|---|
| Latency | < 60 s reference scale |
| Mandates supported | M3, M4, M5 |

## 16. Security & Quantum Posture (Day-1 PQC baseline)

Every event written during the smoke is dual-signed Ed25519 + ML-DSA-65 by the in-process Vault. The smoke verifies both signatures on the expected events as part of its chain-shape check.

## 17. QA & Observability Hooks

The smoke is the runtime complement to Layer 6's source-level assertion. Operators that want runtime policy-gate behaviour assertion run this smoke alongside the layered suite.

## 18. Test & Evidence

The smoke is exercised against the reference NetStreamX deployment as part of the published 100/100 reference target.

## 19. Adapters Used

- None directly. The smoke drives the application through its public API, not through any adapter.

## 20. Acceptance Criteria (Definition of Done)

- [ ] All four services start cleanly on the allocated ports.
- [ ] All ~25 cross-service calls return their expected shape.
- [ ] Every expected event lands in the chain with `intent_id` lineage intact.
- [ ] Both signatures verify on every signed event.
- [ ] Services tear down cleanly on success and on failure.
- [ ] Exit code equals the failure count.
