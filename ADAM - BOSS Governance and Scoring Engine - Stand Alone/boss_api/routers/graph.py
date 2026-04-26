"""Graph introspection endpoints (read-only)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from boss_api.deps import get_graph_client
from boss_api.security import require_token
from boss_core.frameworks import DIMENSION_FRAMEWORKS, FRAMEWORKS
from boss_core.graph_client import GraphClient
from boss_core.tiers import DIMENSION_ORDER

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get(
    "/frameworks",
    summary="List all frameworks registered in the BOSS Data Graph",
)
async def list_frameworks(
    _token: str = Depends(require_token),
) -> list[dict[str, object]]:
    return [
        {
            "key": f.key,
            "name": f.name,
            "publisher": f.publisher,
            "url": f.url,
            "version": f.version,
        }
        for f in FRAMEWORKS
    ]


@router.get(
    "/dimensions",
    summary="List all BOSS dimensions and their framework attribution",
)
async def list_dimensions(
    _token: str = Depends(require_token),
) -> list[dict[str, object]]:
    return [
        {
            "dimension": dim.value,
            "frameworks": list(DIMENSION_FRAMEWORKS[dim]),
        }
        for dim in DIMENSION_ORDER
    ]


@router.get(
    "/ping",
    summary="Ping the data graph backend",
)
async def ping_graph(
    graph: GraphClient = Depends(get_graph_client),
    _token: str = Depends(require_token),
) -> dict[str, bool]:
    return {"ok": graph.healthcheck()}
