"""FastAPI dependencies (shared services)."""

from __future__ import annotations

import threading
from functools import lru_cache

from boss_api.config import Settings, get_settings
from boss_core.flight_recorder import FlightRecorder, JsonlSink
from boss_core.graph_client import GraphClient, InMemoryGraph, Neo4jGraph
from boss_core.tiers import ADAM_DEFAULT_TIERS, TierConfig

_tier_lock = threading.Lock()
_active_tier_config: TierConfig = ADAM_DEFAULT_TIERS


def get_tier_config() -> TierConfig:
    """Return the currently active tier configuration."""
    with _tier_lock:
        return _active_tier_config


def set_tier_config(new_config: TierConfig) -> TierConfig:
    """Replace the active tier configuration."""
    global _active_tier_config
    with _tier_lock:
        _active_tier_config = new_config
        return _active_tier_config


@lru_cache(maxsize=1)
def get_flight_recorder() -> FlightRecorder:
    """Construct and cache the Flight Recorder for the lifetime of the process."""
    settings: Settings = get_settings()
    sink = JsonlSink(settings.flight_recorder_path)
    return FlightRecorder(sink=sink, signer=settings.service_name)


@lru_cache(maxsize=1)
def get_graph_client() -> GraphClient:
    """Return a graph client (Neo4j if configured, otherwise in-memory)."""
    settings: Settings = get_settings()
    if settings.neo4j_uri:
        try:
            return Neo4jGraph(
                uri=settings.neo4j_uri,
                user=settings.neo4j_user,
                password=settings.neo4j_password,
                database=settings.neo4j_database,
            )
        except Exception:  # pragma: no cover - fallback when Neo4j absent
            return InMemoryGraph()
    return InMemoryGraph()
