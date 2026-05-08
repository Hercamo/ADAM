# ADAM Build Card — QA Human Report Renderer

**Card ID:** `qa-report-generator`
**Class:** Verification Tool — Report
**Subgroup / Plane:** QA Harness Suite — Reporting
**Conformance:** ADAM Book New / 5+2 Director Constitution
**Doctrinal status:** Operator support tool. Not part of doctrine.

## 1. Identity & Authority

| Field | Value |
|---|---|
| Card ID | `qa-report-generator` |
| Canonical Name | QA Harness Suite — Human Report Renderer |
| Class | Verification Tool — Report |
| Owning Domain Governor | None (operator-owned tool) |
| Accountable Director | CISO + Operations & Delivery (joint, for evidence-pack runs) |
| Doctrine Cross-Refs | QA Harness Suite — Quality Built In Part V; Directors Dashboard reference |
| Special Note | The renderer is optional. It does not change the truth of the run; it changes the form in which a director reads the run. |

## 2. Mission

Translate the QA Harness Suite's machine-readable JSON report into a director-readable artefact — a single PDF or Markdown document grouped by layer, with failures surfaced up front, and a one-paragraph narrative for each failure naming the contract that did not hold and the section of the doctrine the contract belongs to.

## 3. In-Scope Responsibilities

- Read the suite JSON report.
- Group assertions by layer.
- Surface every failure at the top of the document, with the per-failure narrative.
- Emit a totals block.
- Emit a layer-by-layer pass listing.
- Render to Markdown by default; render to PDF when the operator's environment provides the renderer.

## 4. Explicitly Out of Scope

- Authoring or modifying assertions.
- Changing the truth of the run. The renderer never re-evaluates an assertion; it only translates the JSON.
- Signing the report. Evidence-pack signing is the Director Constitution's act, not the renderer's.

## 5. Inputs

- Path to the suite JSON report (`--input`).
- Optional path to a doctrine cross-reference index (`--doctrine-index`) so per-failure narrative can cite the relevant doctrine section.
- Optional output path (`--output`); if absent, write to stdout.
- Optional `--format` flag: `markdown` (default) or `pdf`.

## 6. Outputs (Flight Recorder & Side Effects)

- Markdown or PDF artefact at the operator-named output path or stdout.
- No Flight Recorder events emitted.

## 7. Public API / Invocation

```bash
python3 qa_report_generator.py --input ./reports/2026-05-08.json \
                               --doctrine-index ./docs/doctrine-index.json \
                               --format markdown \
                               --output ./reports/2026-05-08.md
```

## 8. State & Persistence

Stateless transformation. No durable in-process state.

## 9. BOSS v3.2 Touch Points

None directly. Where the suite JSON contains BOSS-related assertions, the renderer surfaces them under the Layer 5 group.

## 10. Governor / Director Concurrence

None.

## 11. RGI Contracts & OPA Rego Hooks

Read-only on the JSON input.

## 12. Failure Modes & Safe-Mode

Malformed input JSON; missing doctrine index; unwritable output path. Each surfaces as a non-zero exit and a stderr message.

## 13. Resource Profile

Single Python process; trivial CPU / RAM at reference scale.

## 14. Dependencies

- Python 3.10+.
- A Markdown-to-PDF renderer (e.g., Pandoc, WeasyPrint) when `--format=pdf` is selected.

## 15. SLOs & Mandate Alignment

| Metric | Target |
|---|---|
| Latency | < 5 s for a reference-scale JSON |
| Mandates supported | M3 (evidence shape), M6 (operator transparency) |

## 16. Security & Quantum Posture (Day-1 PQC baseline)

The renderer does not sign or verify. Where the operator wants the rendered artefact to be evidence-pack ready, the operator's existing signing pipeline (e.g., a Vault-bound signing tool) signs the rendered artefact after the renderer emits it.

## 17. QA & Observability Hooks

Stdout / exit code only.

## 18. Test & Evidence

- Round-trip test: render a known-good JSON, render the renderer's own output JSON if applicable, diff against the canonical Markdown.
- Doctrine-index test: render a JSON whose failures span every layer, assert every per-failure narrative resolves to a real doctrine section.

## 19. Adapters Used

- None directly. Operators that want the rendered artefact pushed into a document-management system invoke the appropriate adapter through their own automation.

## 20. Acceptance Criteria (Definition of Done)

- [ ] Reads the published suite JSON schema (`{ total, pass, fail, entries: [{layer, status, name, detail}] }`).
- [ ] Produces a Markdown document with: totals block, failures-first block (each with one-paragraph narrative and a doctrine cross-reference), per-layer pass listings.
- [ ] Optional `--format=pdf` produces an equivalent PDF artefact.
- [ ] Renderer is replaceable: an operator with a different report style writes their own renderer against the same JSON without touching the suite.
- [ ] Renderer never re-evaluates an assertion. Truth is the JSON; the renderer only translates form.
