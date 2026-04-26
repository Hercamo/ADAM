# BOSS Engine — Test Suite Guide

This suite mirrors BOSS Formulas v3.2 and the ADAM Exception Economy.
Every test is self-contained: no network, no real Neo4j, no real JWT
issuer. Each fixture wires up an in-process FastAPI app via
`httpx.ASGITransport` so API-level tests run in the same Python process
as the engine.

## Layout

| File | What it covers |
| --- | --- |
| `conftest.py` | Shared fixtures: `tmp_flight_path`, `flight_recorder`, `in_memory_graph`, canonical `soap_intent` / `amber_coast_intent` / `ohshat_intent`, `fresh_settings`, `app`, `api_client`. |
| `test_tiers.py` | Tier weight mapping (5/4/3/2/1/0.5), exactly-one-Top rule, ADAM v3.2 defaults. |
| `test_router.py` | SOAP→OHSHAT boundary mapping and SLA values. |
| `test_composite.py` | Weighted-sum formula, Critical Dimension Override (>75), Non-Idempotent Penalty (+15), cap at 100. |
| `test_flight_recorder.py` | Hash chain integrity, tamper detection (payload edit, reorder, prior_hash edit), determinism. |
| `test_schemas.py` | IntentObject JSON round-trip, TierConfigRequest, ExceptionPacket, DecisionReceipt. |
| `test_api_score.py` | **Canonical Amber Coast ELEVATED assertion** + SOAP + OHSHAT + `/explain` + input validation. |
| `test_api_exceptions.py` | 409 for SOAP intents; 201 with 60-min SLA for ELEVATED; 15-min SLA for OHSHAT. |
| `test_api_receipts.py` | End-to-end score → exception → receipt round-trip; Flight Recorder `DECISION_RECORDED` event. |
| `test_api_flight_recorder.py` | Tail endpoint enabled/disabled, event filter, oversized-limit rejection, chain verification after API activity. |
| `test_api_health_and_config.py` | Liveness/readiness/version/metrics; tier config read + write with Top-swap and zero-Top rejection; `/graph/frameworks` and `/graph/dimensions`. |
| `test_adapters.py` | LangGraph (`normalize_tool_call`, `score_tool_call`, `boss_guard_node`, block on OHSHAT), OpenAI Agents (Responses + Assistants shapes), AI Foundry evaluator promotion, CrewAI task + tool, generic `evaluate_payload` error paths. |
| `test_graph_loader.py` | Cypher `_split_statements` edge cases; idempotent `apply_schema` + `seed_graph` against `InMemoryGraph`. |
| `property/test_properties.py` | Hypothesis invariants: composite ∈ [0,100]; uniform-score identity; non-idempotent ≥ idempotent; escalation monotone in composite; tier weight total matches the sum. |
| `test_schemathesis.py` | OpenAPI fuzz against `/v1/openapi.json` (opt-in via the `schemathesis` marker). |
| `fixtures/*.json` | Canonical intents & tier configs reusable across tests and developer scripts. |

## Markers

Defined in `pyproject.toml`:

- `integration` — tests that may touch a real Neo4j (skipped in CI unit lane).
- `schemathesis` — OpenAPI fuzz; gated separately so unit tests stay <1 s.
- `slow` — tests that take more than one second.

## Running

```bash
# Whole unit suite (no Neo4j, no schemathesis)
pytest -m "not integration and not schemathesis"

# Property tests only
pytest tests/property

# Schemathesis fuzz (optional, needs `pip install boss-engine[test]`)
pytest -m schemathesis

# Coverage report
pytest --cov=boss_core --cov=boss_api --cov=boss_graph --cov=boss_adapters
```

## Load-Bearing Invariants

The reviewer should be able to verify each of these by reading a single
test. If any of them breaks the engine is no longer BOSS-compliant:

1. **Exactly one Top dimension** — `test_tiers.py::TestSingleTopRule`.
2. **Weighted-mean identity** (uniform score ⇒ composite = score) —
   `test_composite.py::TestWeightedSum::test_uniform_score_equals_itself`.
3. **Critical Dimension Override at >75** —
   `test_composite.py::TestCriticalOverride::test_override_triggers_when_dimension_above_threshold`.
4. **Non-Idempotent +15** —
   `test_composite.py::TestNonIdempotentPenalty::test_penalty_added`.
5. **Cap at 100** —
   `test_composite.py::TestCap::test_cap_triggers_when_sum_exceeds_100`.
6. **Hash-chained Flight Recorder** —
   `test_flight_recorder.py::TestTamperDetection` (three tamper modes).
7. **NetStreamX Amber Coast ⇒ ELEVATED** —
   `test_api_score.py::test_amber_coast_routes_to_elevated`.
8. **OHSHAT emergency-stop adapter action** —
   `test_adapters.py::TestLangGraph::test_boss_guard_node_blocks_ohshat`.
