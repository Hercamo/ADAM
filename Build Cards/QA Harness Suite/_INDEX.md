# ADAM QA Harness Suite — Build Cards

Build Cards covering the reference verification toolchain that ships with ADAM.

These cards specify the components an operator needs to recreate the QA Harness
Suite end to end. The suite is an **operator support tool** — not part of the
ADAM doctrine. The contract is the contract; the harness is one prebuilt way
to check it.

## Cards in this folder

| Card ID | Subject | Class |
|---|---|---|
| `qa-suite-runner` | Driver, Results registry, parameterisation, JSON report. | Verification Tool — Driver |
| `qa-layer1-code-health` | Layer 1 — every Python module in the deployment under test parses. | Verification Tool — Layer |
| `qa-layer2-crypto` | Layer 2 — Cryptographic Authorization Vault sign / verify / rotate across the algorithm matrix. | Verification Tool — Layer |
| `qa-layer3-chain-integrity` | Layer 3 — Flight Recorder hash-chain deep verify and WORM-trigger negative tests. | Verification Tool — Layer |
| `qa-layer4-governance-non-negotiables` | Layer 4 — doctrine immutability, sacred boundaries, no-blockchain refusals, test-proxy binding. | Verification Tool — Layer |
| `qa-layer5-boss-methodology` | Layer 5 — BOSS composite formula, critical-dim override, non-idempotent penalty, sample-intent routing. | Verification Tool — Layer |
| `qa-layer6-flow-e2e` | Layer 6 — end-to-end policy-gate presence in the customer-facing application. | Verification Tool — Layer |
| `qa-layer7-owasp-agentic` | Layer 7 — OWASP Agentic AA01–AA10 risk-to-mitigation binding. | Verification Tool — Layer |
| `qa-layer8-ai-control` | Layer 8 — RL governance bounds, sacred-boundary keyword filter, autonomy throttling. | Verification Tool — Layer |
| `qa-layer9-customer-seed` | Layer 9 — synthetic-data generator distribution sanity at the configured scale. | Verification Tool — Layer |
| `qa-layer10-director-console` | Layer 10 — Director Console seat-to-dimension mapping and UI tab presence. | Verification Tool — Layer |
| `qa-views-smoke` | Director-facing views smoke runner — the four production view endpoints. | Verification Tool — Smoke |
| `qa-e2e-smoke` | Cross-service end-to-end runner — stand up FR / BOSS / AGT / app, drive flows, verify chain. | Verification Tool — Smoke |
| `qa-report-generator` | Optional human-report renderer — translates the suite JSON into a director-readable artefact. | Verification Tool — Report |

## Conformance baseline

ADAM Book New / BOSS Score Formulas / Flight Recorder Schema / Runtime
Governance Interface / 5+2 Director Constitution. Software substrate (ACS) by
default; hardware-HSM substrate is a first-class baseline alternative.

## Card anatomy

Each card follows the canonical 20-section anatomy used elsewhere in the Build
Cards directory:

1. Identity & Authority
2. Mission
3. In-Scope Responsibilities
4. Explicitly Out of Scope
5. Inputs
6. Outputs (Flight Recorder & Side Effects)
7. Public API / Invocation
8. State & Persistence
9. BOSS v3.2 Touch Points
10. Governor / Director Concurrence
11. RGI Contracts & OPA Rego Hooks
12. Failure Modes & Safe-Mode
13. Resource Profile
14. Dependencies
15. SLOs & Mandate Alignment
16. Security & Quantum Posture (Day-1 PQC baseline)
17. QA & Observability Hooks
18. Test & Evidence
19. Adapters Used
20. Acceptance Criteria (Definition of Done)

## Doctrinal status

The QA Harness Suite is doctrinally **operator support, not doctrine**. An
operator may extend the suite, replace any layer, or substitute the entire
suite with an alternative verification toolchain without changing ADAM
doctrine. What the suite ships with is the reference toolchain the SpecPack
points to and the published 100/100 reference target is measured against.
