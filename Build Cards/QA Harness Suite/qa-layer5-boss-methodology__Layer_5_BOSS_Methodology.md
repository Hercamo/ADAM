# ADAM Build Card — Layer 5: BOSS Methodology

**Card ID:** `qa-layer5-boss-methodology`
**Class:** Verification Tool — Layer
**Subgroup / Plane:** QA Harness Suite — Layer 5
**Conformance:** ADAM Book New / BOSS / Flight Recorder Schema / RGI / 5+2 Director Constitution / Day-1 PQC
**Doctrinal status:** Operator support tool. Not part of doctrine.

## 1. Identity & Authority

| Field | Value |
|---|---|
| Card ID | `qa-layer5-boss-methodology` |
| Canonical Name | QA Harness Suite — Layer 5: BOSS Methodology |
| Class | Verification Tool — Layer |
| Owning Domain Governor | None (operator-owned tool) |
| Accountable Director | CISO + Operations & Delivery (joint, for evidence-pack runs) |
| Doctrine Cross-Refs | ADAM main book Part E.3; QA Harness Suite — Quality Built In Part IV; QA Suite Runner card; relevant doctrine artefact named in §5. |
| Special Note | Layer asserts contracts. It does not enforce them. |

## 2. Mission

Import the BOSS scoring engine and assert the published composite formula, the critical-dimension override, the non-idempotent additive, and the canonical sample-intent routing.

## 3. In-Scope Responsibilities

- Read the artefacts named in §5 from the deployment under test.
- Assert every contract named in §6 against those artefacts.
- Record each assertion as a single PASS or FAIL row through `results.check(layer=5, name, ok, detail)`.

## 4. Explicitly Out of Scope

- Authoring or modifying the artefacts under test.
- Enforcing the contracts the layer asserts.
- Reporting or rendering. The runner owns the run summary; `qa-report-generator` owns the human report.

## 5. Inputs

BOSS engine module on the import path; `intent/sample-intents.json` bundle; configured weight sum, penalty, critical-dimension threshold, and tier breakpoints.

## 6. Outputs (Flight Recorder & Side Effects)

PASS / FAIL rows for: weight_sum equals configured value; non_idempotent_penalty equals configured value; composite cap = 100; all-zero vector → composite 0, tier SOAP; all-50 vector → composite 50, tier ELEVATED; all-75 vector → tier HIGH; critical override fires when max-dim > threshold (default 75) with override base = max-dim − 10 floor offset; override + non_idempotent → composite ((max-dim − 10) + penalty); penalty pushes critical case to OHSHAT; cap at 100 honoured; composite 10 → SOAP (boundary check); every sample-intent in the bundle routes to its expected tier.

The layer does not append to the live Flight Recorder. Any temporary files the layer creates are removed before the layer returns.

## 7. Public API / Invocation

The layer is a single function with the signature:

```python
def layer5_boss_methodology(cfg: QAConfig, results: Results) -> None: ...
```

It is registered in the runner's `LAYER_FNS` dictionary under key `5`. It is invoked by the runner; it is not invoked directly by operators.

## 8. State & Persistence

In-memory only. The single side-effect is `results.check(...)` calls into the registry the runner owns.

## 9. BOSS v3.2 Touch Points

Layer 5 reads the BOSS configuration and exercises the methodology directly.

## 10. Governor / Director Concurrence

None. The layer is read-only and reports through the Results registry.

## 11. RGI Contracts & OPA Rego Hooks

The layer does not write through RGI. Where the layer reads OPA-related artefacts, the assertion is on artefact presence and content, not on policy enforcement at runtime.

## 12. Failure Modes & Safe-Mode

Configuration drift in weights; methodology refactor without an authored amendment; sample bundle drift.

The layer never raises uncaught exceptions through the runner; if an artefact is missing, the layer records a FAIL row naming the missing artefact and returns. (The runner's own crash handler is the backstop for any genuine implementation bug.)

## 13. Resource Profile

Pure computation against the BOSS module.

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

- [ ] All §6 contracts pass against the deployment's live BOSS configuration.
- [ ] Sample-intent bundle is walked end to end and every sample's expected tier matches the computed tier.
- [ ] Critical-dimension override fires at the configured raw threshold (default 75) with the configured floor offset (default 10).
- [ ] Non-idempotent additive equals the configured value (default 15) and is applied flat, not multiplicatively.
- [ ] Composite cap of 100 is honoured even under the worst-case override + non-idempotent path.
