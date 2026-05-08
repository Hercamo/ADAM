# ADAM Build Card — QA Director Views Smoke Runner

**Card ID:** `qa-views-smoke`
**Class:** Verification Tool — Smoke
**Subgroup / Plane:** QA Harness Suite — Director Surface
**Conformance:** ADAM Book New / BOSS / Flight Recorder Schema / RGI / 5+2 Director Constitution / Day-1 PQC
**Doctrinal status:** Operator support tool. Not part of doctrine.

## 1. Identity & Authority

| Field | Value |
|---|---|
| Card ID | `qa-views-smoke` |
| Canonical Name | QA Harness Suite — Director Views Smoke Runner |
| Class | Verification Tool — Smoke |
| Owning Domain Governor | None (operator-owned tool) |
| Accountable Director | CISO + Operations & Delivery |
| Doctrine Cross-Refs | Directors Dashboard reference; Intent Object Definition; BOSS Score Formulas |

## 2. Mission

Verify the four director-facing view endpoints against live deployment data, in-process, with no Docker dependency. Returns exit 0 only on a full pass.

## 3. In-Scope Responsibilities

- Stand the dashboard view module up under a Flask test client in-process.
- Hit `/api/dashboard/views/health`; assert service mounted and live paths resolve.
- Hit `/api/dashboard/dna/sections`; assert the 13 DNA sections, with Q+A sourced from the deployed DNA JSON, with canonical title fragments present.
- Hit `/api/dashboard/dna/section/<n>`; assert the single-section payload and that out-of-range returns 404.
- Hit `/api/dashboard/boss/dimension/<dim>`; assert all seven canonical dimensions return weight, framework, tier interpretation, and matched rules; unknown dimension returns 404.
- Hit `/api/dashboard/lifecycle/<intent_id>`; assert it reads `chain.sqlite` read-only and returns explicit empty-list on absent intent (no synthesised events).
- Confirm the live chain mtime is unchanged after the suite runs.

## 4. Explicitly Out of Scope

- Driving the dashboard UI. The smoke runner exercises the API surface only.
- Modifying any deployment artefact.

## 5. Inputs

- Deployment root with `netstreamx_app/dashboard_views.py` (or operator equivalent).
- Live `chain.sqlite` for the lifecycle endpoint.
- Deployed DNA JSON for the section content checks.

## 6. Outputs (Flight Recorder & Side Effects)

- Stdout: `PASS` / `FAIL` per check.
- Process exit code: 0 on full pass, 1 on any failure.
- No Flight Recorder events emitted by the runner.

## 7. Public API / Invocation

```bash
python3 deployment/<profile>/qa/views_smoke.py
```

## 8. State & Persistence

In-process Flask test client. No durable state.

## 9. BOSS v3.2 Touch Points

The dimension endpoint exposes the canonical seven dimensions; the runner asserts each is reachable and returns the contract content.

## 10. Governor / Director Concurrence

None.

## 11. RGI Contracts & OPA Rego Hooks

Read-only.

## 12. Failure Modes & Safe-Mode

Endpoint regression; DNA section drift; chain-mtime mutation by an unrelated process. Each surfaces as a FAIL row.

## 13. Resource Profile

Single Python process; < 500 MB RAM at reference scale; < 5 s wall-clock.

## 14. Dependencies

- Python 3.10+; Flask; the dashboard_views module on the import path.

## 15. SLOs & Mandate Alignment

| Metric | Target |
|---|---|
| Latency | < 5 s |
| Mandates supported | M3, M4 |

## 16. Security & Quantum Posture (Day-1 PQC baseline)

Read-only against signed artefacts. Substrate-agnostic.

## 17. QA & Observability Hooks

The smoke runner is itself a hook. Its output is reported via stdout and exit code; an operator can pipe stdout into a JSON-shaped artefact through their own automation.

## 18. Test & Evidence

The runner is exercised against the reference NetStreamX deployment as part of the published 100/100 reference target.

## 19. Adapters Used

- None.

## 20. Acceptance Criteria (Definition of Done)

- [ ] All six checks pass against the reference NetStreamX deployment.
- [ ] The chain SQLite mtime is unchanged after the runner completes.
- [ ] The runner exits 1 on any failure and 0 only on a full pass.
- [ ] Out-of-range section requests return 404; unknown dimension requests return 404.
