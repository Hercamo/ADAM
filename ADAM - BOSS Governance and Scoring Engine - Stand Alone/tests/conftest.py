"""Shared test fixtures.

The fixtures assemble the BOSS Engine without any external dependency —
no Neo4j, no real JWT issuer, no network access required. Every test
module can request the ``api_client`` fixture to get an in-process
``httpx.AsyncClient`` wired to a fresh FastAPI app with a temporary
Flight Recorder on disk.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest

from boss_api.app import create_app
from boss_api.config import Settings
from boss_api.deps import (
    get_flight_recorder,
    get_graph_client,
    get_tier_config,
    set_tier_config,
)
from boss_core.flight_recorder import FlightRecorder, JsonlSink
from boss_core.graph_client import InMemoryGraph
from boss_core.schemas import IntentObject, IntentSource
from boss_core.tiers import ADAM_DEFAULT_TIERS

# ---------------------------------------------------------------------------
# Low-level fixtures (no HTTP)
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_flight_path(tmp_path: Path) -> Path:
    """Return a fresh JSONL Flight Recorder path per test."""
    path = tmp_path / "flight-recorder.jsonl"
    return path


@pytest.fixture
def flight_recorder(tmp_flight_path: Path) -> FlightRecorder:
    """Construct a FlightRecorder over a temp JsonlSink."""
    return FlightRecorder(sink=JsonlSink(tmp_flight_path), signer="pytest")


@pytest.fixture
def in_memory_graph() -> InMemoryGraph:
    """Return an in-memory graph seeded from the repository's cypher files."""
    return InMemoryGraph()


# ---------------------------------------------------------------------------
# Canonical ADAM intent fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def soap_intent() -> IntentObject:
    """A well-scoped 'safe' intent that should route to SOAP."""
    return IntentObject(
        source=IntentSource(user_id="agent.safe.caller"),
        headline="Low-risk internal report refresh",
        description="Nightly refresh of the anonymized internal KPI board.",
        dimension_inputs={
            "security": {
                "prompt_injection_risk": 0.01,
                "cve_exposure_max_cvss": 0.0,
                "mitre_tactics_detected": 0,
            },
            "sovereignty": {
                "data_residency_compliant": True,
                "cross_border_transfers": 0,
                "lawful_basis_documented": True,
            },
            "financial": {
                "projected_revenue_m": 0.5,
                "projected_cost_m": 0.2,
                "single_loss_expectancy_m": 0.1,
                "annualized_rate_of_occurrence": 0.01,
                "risk_appetite_m": 5.0,
            },
            "regulatory": {
                "primary_regulations": [],
                "controls_passed": 50,
                "controls_total": 50,
                "open_findings_severity_max": "NONE",
            },
            "reputational": {
                "reptrak_delta": 0.0,
                "sasb_material_topics_touched": [],
                "esg_severity_score": 0.0,
            },
            "rights": {
                "authorization_certainty": 0.99,
                "ownership_certainty": 0.99,
                "consent_lineage_verified": True,
            },
            "doctrinal": {
                "doctrine_alignment": 0.95,
                "mission_fit": 0.95,
                "conflicts_with_declared_constraints": False,
            },
        },
    )


@pytest.fixture
def amber_coast_intent() -> IntentObject:
    """NetStreamX Amber Coast launch — the book's canonical ELEVATED case."""
    return IntentObject(
        intent_id=uuid4(),
        source=IntentSource(user_id="agent.launch.amber_coast"),
        headline="Launch Amber Coast EU campaign",
        description=(
            "Launch the Amber Coast reality series across eight EU countries "
            "with a co-marketing push via NetStreamX partner platforms."
        ),
        is_non_idempotent=False,
        dimension_inputs={
            "security": {
                "prompt_injection_risk": 0.08,
                "cve_exposure_max_cvss": 4.2,
                "mitre_tactics_detected": 0,
            },
            "sovereignty": {
                "data_residency_compliant": True,
                "cross_border_transfers": 3,
                "lawful_basis_documented": True,
            },
            "financial": {
                "projected_revenue_m": 42.0,
                "projected_cost_m": 17.5,
                "single_loss_expectancy_m": 9.0,
                "annualized_rate_of_occurrence": 0.08,
                "risk_appetite_m": 5.0,
            },
            "regulatory": {
                "primary_regulations": ["GDPR", "EU_AI_ACT"],
                "controls_passed": 43,
                "controls_total": 48,
                "open_findings_severity_max": "MEDIUM",
            },
            "reputational": {
                "reptrak_delta": -4.0,
                "sasb_material_topics_touched": ["data_privacy", "media_ethics"],
                "esg_severity_score": 0.35,
            },
            "rights": {
                "authorization_certainty": 0.92,
                "ownership_certainty": 0.88,
                "consent_lineage_verified": True,
            },
            "doctrinal": {
                "doctrine_alignment": 0.78,
                "mission_fit": 0.82,
                "conflicts_with_declared_constraints": False,
            },
        },
    )


@pytest.fixture
def ohshat_intent(amber_coast_intent: IntentObject) -> IntentObject:
    """A variant that trips the Critical Dimension Override into OHSHAT."""
    clone = amber_coast_intent.model_copy(deep=True)
    clone.dimension_inputs.security = {
        "prompt_injection_risk": 0.85,
        "cve_exposure_max_cvss": 9.6,
        "mitre_tactics_detected": 5,
    }
    clone.dimension_inputs.regulatory = {
        "primary_regulations": ["GDPR", "EU_AI_ACT", "DORA"],
        "controls_passed": 10,
        "controls_total": 50,
        "open_findings_severity_max": "CRITICAL",
    }
    clone.is_non_idempotent = True
    return clone


# ---------------------------------------------------------------------------
# HTTP client fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fresh_settings(monkeypatch: pytest.MonkeyPatch, tmp_flight_path: Path) -> Settings:
    """Environment-driven Settings with every side-effectful path scoped to tmp."""
    monkeypatch.setenv("BOSS_ENV", "test")
    monkeypatch.setenv("BOSS_AUTH_ENABLED", "false")
    monkeypatch.setenv("BOSS_ADMIN_TOKENS", "test-token")
    monkeypatch.setenv("BOSS_FLIGHT_RECORDER_PATH", str(tmp_flight_path))
    monkeypatch.setenv("BOSS_FLIGHT_RECORDER_TAIL", "1")
    monkeypatch.setenv("BOSS_NEO4J_URI", "")
    return Settings(flight_recorder_path=str(tmp_flight_path))


@pytest.fixture
def app(
    fresh_settings: Settings,
    flight_recorder: FlightRecorder,
    in_memory_graph: InMemoryGraph,
):
    """Return a FastAPI app with tiny, in-memory dependencies wired in."""
    application = create_app(settings=fresh_settings)
    application.dependency_overrides[get_flight_recorder] = lambda: flight_recorder
    application.dependency_overrides[get_graph_client] = lambda: in_memory_graph
    # Reset tier config between tests.
    set_tier_config(ADAM_DEFAULT_TIERS)
    application.dependency_overrides[get_tier_config] = lambda: ADAM_DEFAULT_TIERS
    yield application
    application.dependency_overrides.clear()


@pytest.fixture
async def api_client(app) -> Iterator:
    """Async httpx client bound to the in-process FastAPI app."""
    import httpx

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_fixture_json(name: str) -> dict[str, object]:
    """Load a JSON fixture from tests/fixtures/."""
    path = Path(__file__).parent / "fixtures" / name
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


__all__ = [
    "load_fixture_json",
]
