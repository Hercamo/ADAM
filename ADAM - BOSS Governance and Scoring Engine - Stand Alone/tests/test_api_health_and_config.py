"""Health, version, metrics, and tier-config API tests."""

from __future__ import annotations

import httpx
import pytest


@pytest.mark.asyncio
async def test_healthz(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/v1/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_readyz(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/v1/readyz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert "flight_recorder_head" in body
    assert "graph_ok" in body


@pytest.mark.asyncio
async def test_version(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/v1/version")
    assert response.status_code == 200
    body = response.json()
    assert "engine" in body
    assert "boss_formula" in body
    assert "adam_reference" in body


@pytest.mark.asyncio
async def test_metrics_endpoint(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/v1/metrics")
    # Even before any traffic, the Prometheus endpoint should respond.
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_read_tier_config(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/v1/config/tiers")
    assert response.status_code == 200
    body = response.json()
    assert "assignments" in body
    assert body["assignments"]["security"] == "Top"


@pytest.mark.asyncio
async def test_write_tier_config_swaps_top(api_client: httpx.AsyncClient) -> None:
    new_assignments = {
        "security": "Very High",
        "sovereignty": "Very High",
        "financial": "Very High",
        "regulatory": "Top",  # promote regulatory to Top
        "reputational": "High",
        "rights": "High",
        "doctrinal": "Medium",
    }
    response = await api_client.put(
        "/v1/config/tiers",
        json={
            "assignments": new_assignments,
            "author": "director.alpha",
            "reason": "Pilot regulatory-first configuration",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["assignments"]["regulatory"] == "Top"


@pytest.mark.asyncio
async def test_write_tier_config_zero_top_rejected(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.put(
        "/v1/config/tiers",
        json={
            "assignments": {
                "security": "Very High",
                "sovereignty": "Very High",
                "financial": "Very High",
                "regulatory": "High",
                "reputational": "High",
                "rights": "High",
                "doctrinal": "Medium",
            },
            "author": "director.alpha",
        },
    )
    assert response.status_code in {400, 422, 500}


@pytest.mark.asyncio
async def test_graph_frameworks(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/v1/graph/frameworks")
    assert response.status_code == 200
    frameworks = response.json()
    assert len(frameworks) > 0
    keys = {f["key"] for f in frameworks}
    # Sanity — the doctrine-mandated frameworks must be present.
    assert "NIST_CSF_2" in keys or "nist_csf_2" in {k.lower() for k in keys}
    assert any("GDPR" in k.upper() for k in keys)


@pytest.mark.asyncio
async def test_graph_dimensions(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/v1/graph/dimensions")
    assert response.status_code == 200
    dims = response.json()
    assert len(dims) == 7
    names = {d["dimension"] for d in dims}
    assert names == {
        "security",
        "sovereignty",
        "financial",
        "regulatory",
        "reputational",
        "rights",
        "doctrinal",
    }
