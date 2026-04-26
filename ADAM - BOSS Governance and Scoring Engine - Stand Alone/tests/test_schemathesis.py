"""Schemathesis OpenAPI fuzz tests.

These are marked ``@pytest.mark.schemathesis`` so they can be gated
separately in CI — they run against the in-process FastAPI app,
load the OpenAPI schema, and assert that every response still matches
the advertised schema under randomly generated input.

If the ``schemathesis`` package isn't installed, the module is skipped
gracefully so the normal unit-test suite is unaffected.
"""

from __future__ import annotations

import pytest

pytest.importorskip("schemathesis", reason="schemathesis is an optional test dep")

import schemathesis

from boss_api.app import create_app
from boss_api.config import Settings

pytestmark = pytest.mark.schemathesis


def _settings(tmp_path_factory: pytest.TempPathFactory) -> Settings:
    path = tmp_path_factory.mktemp("schemathesis") / "flight.jsonl"
    return Settings(flight_recorder_path=str(path))


@pytest.fixture(scope="session")
def fastapi_schema(tmp_path_factory: pytest.TempPathFactory) -> schemathesis.BaseSchema:
    app = create_app(settings=_settings(tmp_path_factory))
    return schemathesis.from_asgi("/v1/openapi.json", app)


schema = schemathesis.from_asgi(
    "/v1/openapi.json",
    create_app(),
)


@schema.parametrize()
def test_api_fuzz(case: schemathesis.Case) -> None:
    """Any response must conform to the declared OpenAPI schema."""
    response = case.call_asgi()
    case.validate_response(response)
