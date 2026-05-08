# ADAM Build Card — QA Suite Runner

**Card ID:** `qa-suite-runner`
**Class:** Verification Tool — Driver
**Subgroup / Plane:** QA Harness Suite — Driver
**Conformance:** ADAM Book New / BOSS / Flight Recorder Schema / RGI / 5+2 Director Constitution / Day-1 PQC
**Doctrinal status:** Operator support tool. Not part of doctrine.

## 1. Identity & Authority

| Field | Value |
|---|---|
| Card ID | `qa-suite-runner` |
| Canonical Name | QA Harness Suite — Driver |
| Class | Verification Tool — Driver |
| Owning Domain Governor | None (operator-owned tool) |
| Accountable Director | CISO + Operations & Delivery (joint, for evidence-pack runs) |
| Doctrine Cross-Refs | ADAM main book Part E.3; QA Harness Suite — Quality Built In; BOSS Score Formulas; Flight Recorder schema; Director Constitution; OPA Rego Authoring Standards |
| Special Note | The runner has no authority of its own. It reads, asserts, and reports. It does not block, refuse, or revoke. |

## 2. Mission

Drive the layered QA Harness Suite end to end against a parameterised deployment, collect every assertion through a single Results registry, emit machine-readable JSON, and exit with the failure count.

## 3. In-Scope Responsibilities

- Parse command-line arguments into a `QAConfig`.
- Resolve deployment paths from the `--root` argument.
- Maintain the `LAYER_FNS` registry mapping layer numbers to layer functions.
- Run the requested `--layers` set in numeric order; honour `--skip-layers`.
- Catch and record any layer-level exception as a single FAIL row tagged `"layer N crashed"`.
- Honour `--strict` to summary-and-exit on the first FAIL.
- Emit a JSON report at `--json-report` if provided.
- Exit with the failure count (zero on clean run).

## 4. Explicitly Out of Scope

- Authoring layers. Each layer is a separate card.
- Enforcing any contract. The runner reports; the Director Constitution and the Cryptographic Authorization Vault enforce.
- Producing the human report. That is `qa-report-generator`.

## 5. Inputs

- `--root PATH` — deployment root.
- `--chain PATH` — Flight Recorder chain SQLite.
- `--legacy-key PATH` — legacy Ed25519 key adopted into the HSM keystore.
- `--doctrine-version V` — expected doctrine version.
- `--expect-users N` / `--expect-assets N` — synthetic-data scale.
- `--expect-subs-min N` / `--expect-subs-max N` — subscription-ratio band.
- `--film N` / `--series N` / `--game N` / `--live N` — per-asset-kind expected counts.
- `--tier1-region-min N` — tier-1 region floor.
- `--minor-min N` / `--minor-max N` — minor-count band.
- `--bw-soap-max N` / `--bw-mod-max N` / `--bw-elev-max N` / `--bw-high-max N` — BOSS tier breakpoints.
- `--penalty N` — non-idempotent additive.
- `--weight-sum N` — BOSS weight sum (default 24.0).
- `--critical-thresh N` — critical-dim override threshold (default 75).
- `--layers L1,L2,...` / `--skip-layers L1,L2,...` — layer subset selection.
- `--strict` — stop at first FAIL.
- `--json-report PATH` — machine-readable report path.
- `--self-test` — synthetic-deployment self-test mode (slow).

## 6. Outputs (Flight Recorder & Side Effects)

- Stdout: per-assertion `[✓]` / `[✗]` lines and a totals block.
- Optional JSON report file: `{ total, pass, fail, entries: [...] }`.
- No Flight Recorder events emitted by the runner itself. (Layers may write to operator-named locations during their work; the runner does not append to the live Flight Recorder.)
- Process exit code: failure count.

## 7. Public API / Invocation

```bash
# Default reference run
python3 qa_suite.py

# Layer subset
python3 qa_suite.py --layers 1,2,3
python3 qa_suite.py --skip-layers 9

# Production-scale parameters
python3 qa_suite.py --expect-users 10000 --expect-assets 10000 \
    --film 6000 --series 2500 --game 1000 --live 500 \
    --tier1-region-min 5000 --minor-min 800 --minor-max 1300

# Strict mode
python3 qa_suite.py --strict

# JSON report
python3 qa_suite.py --json-report ./reports/$(date +%Y%m%d).json

# Different deployment root
python3 qa_suite.py --root /opt/adam/deployment/AlternateProfile
```

## 8. State & Persistence

- In-memory only during the run: a single `Results` registry collects every assertion.
- Optional JSON report file written at exit if `--json-report` is provided.
- No durable in-process state across runs.

## 9. BOSS v3.2 Touch Points

The runner does not score actions and does not consume the BOSS dimensions itself. Layer 5 reads the BOSS configuration and exercises the methodology; Layer 8 reads the AI-control bounds calibrated against BOSS thresholds.

## 10. Governor / Director Concurrence

- No governor or director concurrence required to run the suite.
- The output of a run is consumed by directors as evidence-pack content; consumption is governed by the relevant phase-gate or amendment process.

## 11. RGI Contracts & OPA Rego Hooks

- The runner is read-only and does not write through RGI.
- Layer-specific RGI hooks are documented on each layer's card.

## 12. Failure Modes & Safe-Mode

- A layer raising an unhandled exception is caught by the runner and recorded as a single FAIL with the exception string in the detail field. The next layer still runs (unless `--strict`).
- A missing deployment artefact (e.g., the chain SQLite) is reported as FAIL by the layer that requires it; the runner does not pre-validate.
- Strict mode aborts the run on the first FAIL and emits the JSON report at the abort point.

## 13. Resource Profile

| Profile | vCPUs | RAM (GB) | Disk |
|---|---|---|---|
| Default suite (10 layers, NetStreamX 100/100) | 1 | 1 | < 1 GB temp |
| Production scale (Layer 9 spawn) | 2 | 4 | up to chain size for Layer 3 deep-verify |

## 14. Dependencies

- Python 3.10+.
- Read access to the deployment root, the Flight Recorder chain, the legacy key, the doctrine seed, the directors registry, the exception-economy YAML, and the Cryptographic Authorization Vault source.
- The deployment's BOSS engine module on the import path for Layer 5.
- The Flight Recorder module on the import path for Layer 3.

## 15. SLOs & Mandate Alignment

| Metric | Target |
|---|---|
| Default suite latency (layers 1–10, NetStreamX 100/100) | < 60 s |
| Default suite latency excluding Layer 3 deep verify and Layer 9 seed | < 5 s |
| JSON report size | < 100 KB at reference scale |
| Mandates supported | M3 (evidence), M4 (auditability), M6 (operator transparency) |

## 16. Security & Quantum Posture (Day-1 PQC baseline)

The runner does not sign or verify any payload itself. Layer 2 exercises the Cryptographic Authorization Vault's Ed25519 + ML-DSA-65 dual-signature behaviour. Where an operator runs the suite against a hardware-HSM-rooted substrate, the same Vault API is used and the same Layer 2 assertions hold; the substrate choice is invisible to the runner.

## 17. QA & Observability Hooks

- The runner is itself the QA hook.
- Per-layer observability is documented on each layer's card.

## 18. Test & Evidence

- `--self-test` builds a synthetic deployment artefact set and runs the suite against it.
- The Build Cards QA harness (`qa_all.py`, `qa_360.py`) verifies the runner's interface contract — every layer registered in `LAYER_FNS` has a callable conforming to the `(cfg, results)` signature.

## 19. Adapters Used

- None. The runner is internal-only.

## 20. Acceptance Criteria (Definition of Done)

- [ ] `python3 qa_suite.py --self-test` exits 0 against the synthetic deployment.
- [ ] `python3 qa_suite.py --layers 1` exits 0 against the reference NetStreamX deployment.
- [ ] Every constant the suite uses is overridable from the command line.
- [ ] The `LAYER_FNS` registry contains exactly the layers documented in this card folder.
- [ ] The JSON report schema is `{ total, pass, fail, entries: [{layer, status, name, detail}] }`.
- [ ] Strict mode aborts on the first FAIL and writes the JSON report at the abort point.
- [ ] A layer raising an unhandled exception is recorded as a single FAIL row with the exception string and the next layer still runs (unless `--strict`).
- [ ] Exit code equals the failure count.
