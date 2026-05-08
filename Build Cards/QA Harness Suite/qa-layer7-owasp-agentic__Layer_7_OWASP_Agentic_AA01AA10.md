# ADAM Build Card — Layer 7: OWASP Agentic AA01–AA10

**Card ID:** `qa-layer7-owasp-agentic`
**Class:** Verification Tool — Layer
**Subgroup / Plane:** QA Harness Suite — Layer 7
**Conformance:** ADAM Book New / BOSS / Flight Recorder Schema / RGI / 5+2 Director Constitution / Day-1 PQC
**Doctrinal status:** Operator support tool. Not part of doctrine.

## 1. Identity & Authority

| Field | Value |
|---|---|
| Card ID | `qa-layer7-owasp-agentic` |
| Canonical Name | QA Harness Suite — Layer 7: OWASP Agentic AA01–AA10 |
| Class | Verification Tool — Layer |
| Owning Domain Governor | None (operator-owned tool) |
| Accountable Director | CISO + Operations & Delivery (joint, for evidence-pack runs) |
| Doctrine Cross-Refs | ADAM main book Part E.3; QA Harness Suite — Quality Built In Part IV; QA Suite Runner card; relevant doctrine artefact named in §5. |
| Special Note | Layer asserts contracts. It does not enforce them. |

## 2. Mission

Bind every canonical OWASP Agentic AI risk to a named mitigation surface in the running deployment.

## 3. In-Scope Responsibilities

- Read the artefacts named in §5 from the deployment under test.
- Assert every contract named in §6 against those artefacts.
- Record each assertion as a single PASS or FAIL row through `results.check(layer=7, name, ok, detail)`.

## 4. Explicitly Out of Scope

- Authoring or modifying the artefacts under test.
- Enforcing the contracts the layer asserts.
- Reporting or rendering. The runner owns the run summary; `qa-report-generator` owns the human report.

## 5. Inputs

DNA JSON; doctrine seed; auth-vault source; AGT-Full server source; software-HSM source.

## 6. Outputs (Flight Recorder & Side Effects)

PASS / FAIL rows for: `OWASP Agentic AA01-AA10` named in compliance frameworks; AA01 → Trust Gateway present; AA02 → Intent Interpretation present; AA03 → 5 governors must concur; AA04 → vault has revoke + ttl; AA05 → HSM-signed tokens; AA06 → 4-ring containment present; AA07 → 'Never sell viewing data' sacred boundary present; AA08 → HSM keys chmod 600; AA09 → WORM triggers in Flight Recorder; AA10 → RGI-05 plugin attestation endpoint present.

The layer does not append to the live Flight Recorder. Any temporary files the layer creates are removed before the layer returns.

## 7. Public API / Invocation

The layer is a single function with the signature:

```python
def layer7_owasp_agentic_aa01aa10(cfg: QAConfig, results: Results) -> None: ...
```

It is registered in the runner's `LAYER_FNS` dictionary under key `7`. It is invoked by the runner; it is not invoked directly by operators.

## 8. State & Persistence

In-memory only. The single side-effect is `results.check(...)` calls into the registry the runner owns.

## 9. BOSS v3.2 Touch Points

None directly; the layer is on a non-BOSS surface.

## 10. Governor / Director Concurrence

None. The layer is read-only and reports through the Results registry.

## 11. RGI Contracts & OPA Rego Hooks

The layer does not write through RGI. Where the layer reads OPA-related artefacts, the assertion is on artefact presence and content, not on policy enforcement at runtime.

## 12. Failure Modes & Safe-Mode

OWASP register evolution without layer extension; mitigation surface removed during refactor.

The layer never raises uncaught exceptions through the runner; if an artefact is missing, the layer records a FAIL row naming the missing artefact and returns. (The runner's own crash handler is the backstop for any genuine implementation bug.)

## 13. Resource Profile

Source reads only.

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

- [ ] Every canonical risk has a named mitigation row.
- [ ] AA01 through AA10 are each asserted; the layer fails when any one of the ten is unmapped.
- [ ] DNA `compliance_frameworks` includes the canonical OWASP register identifier.
- [ ] Mitigation strings are asserted at source level so a refactor that removes a mitigation breaks the layer immediately.
