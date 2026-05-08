# ADAM Build Card — Layer 6: End-to-End Flow

**Card ID:** `qa-layer6-flow-e2e`
**Class:** Verification Tool — Layer
**Subgroup / Plane:** QA Harness Suite — Layer 6
**Conformance:** ADAM Book New / BOSS / Flight Recorder Schema / RGI / 5+2 Director Constitution / Day-1 PQC
**Doctrinal status:** Operator support tool. Not part of doctrine.

## 1. Identity & Authority

| Field | Value |
|---|---|
| Card ID | `qa-layer6-flow-e2e` |
| Canonical Name | QA Harness Suite — Layer 6: End-to-End Flow |
| Class | Verification Tool — Layer |
| Owning Domain Governor | None (operator-owned tool) |
| Accountable Director | CISO + Operations & Delivery (joint, for evidence-pack runs) |
| Doctrine Cross-Refs | ADAM main book Part E.3; QA Harness Suite — Quality Built In Part IV; QA Suite Runner card; relevant doctrine artefact named in §5. |
| Special Note | Layer asserts contracts. It does not enforce them. |

## 2. Mission

Read the customer-facing application source and assert the policy gates are present in the right places.

## 3. In-Scope Responsibilities

- Read the artefacts named in §5 from the deployment under test.
- Assert every contract named in §6 against those artefacts.
- Record each assertion as a single PASS or FAIL row through `results.check(layer=6, name, ok, detail)`.

## 4. Explicitly Out of Scope

- Authoring or modifying the artefacts under test.
- Enforcing the contracts the layer asserts.
- Reporting or rendering. The runner owns the run summary; `qa-report-generator` owns the human report.

## 5. Inputs

`netstreamx_app/netstreamx_app.py` (or the operator's equivalent application module).

## 6. Outputs (Flight Recorder & Side Effects)

PASS / FAIL rows for the reference profile: under-13 signup rejected with `under_13_not_permitted` and `age < 13`; signup emits `intent_rejected` with COPPA reason; playback checks region; playback checks age vs. rating; playback checks `rights_cleared`; playback checks subscription tier; playback checks `taken_down`; recommendations does not consume individual viewing data.

The layer does not append to the live Flight Recorder. Any temporary files the layer creates are removed before the layer returns.

## 7. Public API / Invocation

The layer is a single function with the signature:

```python
def layer6_end_to_end_flow(cfg: QAConfig, results: Results) -> None: ...
```

It is registered in the runner's `LAYER_FNS` dictionary under key `6`. It is invoked by the runner; it is not invoked directly by operators.

## 8. State & Persistence

In-memory only. The single side-effect is `results.check(...)` calls into the registry the runner owns.

## 9. BOSS v3.2 Touch Points

None directly; the layer is on a non-BOSS surface.

## 10. Governor / Director Concurrence

None. The layer is read-only and reports through the Results registry.

## 11. RGI Contracts & OPA Rego Hooks

The layer does not write through RGI. Where the layer reads OPA-related artefacts, the assertion is on artefact presence and content, not on policy enforcement at runtime.

## 12. Failure Modes & Safe-Mode

Policy gate removed during refactor; recommendation generator started consuming viewing data; rights or rating gates softened.

The layer never raises uncaught exceptions through the runner; if an artefact is missing, the layer records a FAIL row naming the missing artefact and returns. (The runner's own crash handler is the backstop for any genuine implementation bug.)

## 13. Resource Profile

Source reads only. Operators that want runtime behaviour assertion extend Layer 6 with the `qa-e2e-smoke` runner.

## 14. Dependencies

- Python 3.10+.
- The runner (`qa-suite-runner`) for invocation.
- Read access to every artefact named in §5.

## 15. SLOs & Mandate Alignment

| Metric | Target |
|---|---|
| Layer latency | < 1 s. |
| Mandates supported | M3 (evidence), M4 (auditability) |

## 16. Security & Quantum Posture (Day-1 PQC baseline)

The layer is read-only and does not sign or verify on its own. Where the layer reads cryptographic substrate or chain artefacts, the substrate's Day-1 PQC posture (Ed25519 + ML-DSA-65 dual-signature; ML-KEM-768 transport; SLH-DSA long-term anchor) is what the layer is asserting against. Hardware-HSM and software-substrate (ACS) deployments are equally valid; the layer's contracts hold across both.

## 17. QA & Observability Hooks

The layer is itself a QA hook. The runner's stdout and JSON report are the only observability surfaces.

## 18. Test & Evidence

- The runner's `--self-test` mode exercises this layer against synthetic artefacts.
- The Build Cards QA harness verifies the layer is registered in `LAYER_FNS` and that its function signature matches the runner's expected shape.

## 19. Adapters Used

- None. Layer is internal-only.

## 20. Acceptance Criteria (Definition of Done)

- [ ] All §6 contracts pass against the deployed application source.
- [ ] Each policy gate names the exact failure path (e.g., `playback_blocked_rights`, `playback_blocked_age`, `Asset taken down`) and the layer asserts the string presence.
- [ ] Recommendation generator is asserted to NOT consume individual viewing data; the assertion fails if the negation phrase is removed during refactor.
