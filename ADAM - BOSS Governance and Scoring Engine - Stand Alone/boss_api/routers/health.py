"""Liveness, readiness, and metrics endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from boss_api.deps import get_flight_recorder, get_graph_client
from boss_api.telemetry import render_metrics
from boss_core.flight_recorder import FlightRecorder
from boss_core.graph_client import GraphClient
from boss_core.version import ADAM_REFERENCE_VERSION, BOSS_FORMULA_VERSION, __version__

router = APIRouter(tags=["health"])


@router.get("/healthz", summary="Liveness probe")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz", summary="Readiness probe")
async def readyz(
    flight: FlightRecorder = Depends(get_flight_recorder),
    graph: GraphClient = Depends(get_graph_client),
) -> dict[str, object]:
    return {
        "status": "ready",
        "flight_recorder_head": flight._sink.head(),
        "graph_ok": graph.healthcheck(),
    }


@router.get("/version", summary="Version information")
async def version() -> dict[str, str]:
    return {
        "engine": __version__,
        "boss_formula": BOSS_FORMULA_VERSION,
        "adam_reference": ADAM_REFERENCE_VERSION,
    }


@router.get(
    "/metrics",
    summary="Prometheus metrics",
    response_class=PlainTextResponse,
    include_in_schema=False,
)
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(
        content=render_metrics().decode("utf-8"),
        media_type="text/plain; version=0.0.4",
    )
