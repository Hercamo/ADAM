"""Runtime configuration for the BOSS API.

All configuration is environment-driven so the same container runs on a
developer laptop, a shared CI cluster, or a production Kubernetes
deployment without code changes.

Every field is read from the environment *inside* :func:`get_settings`
so that tests and operators can change ``os.environ`` at runtime (for
example via ``monkeypatch.setenv``) and see the new value on the next
call.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env_bool(name: str, default: bool = False) -> bool:
    """Parse a truthy/falsy environment variable into a Python ``bool``."""
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _env_tuple(name: str, default: str = "") -> tuple[str, ...]:
    """Parse a comma-separated environment variable into a tuple."""
    raw = os.getenv(name, default)
    return tuple(item.strip() for item in raw.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    """Engine settings materialized from the environment at startup.

    The dataclass is frozen so the settings snapshot cannot be mutated
    after construction; every request handler can rely on it being
    stable for the lifetime of the request.
    """

    service_name: str = "boss-engine"
    environment: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/v1"
    cors_origins: tuple[str, ...] = ("*",)
    auth_enabled: bool = False
    jwt_issuer: str = "boss-engine"
    jwt_audience: str = "boss-engine"
    jwt_secret: str = ""
    flight_recorder_path: str = "/var/lib/boss/flight-recorder.jsonl"
    neo4j_uri: str = ""
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"
    metrics_enabled: bool = True
    otel_endpoint: str = ""
    admin_tokens: tuple[str, ...] = field(default_factory=tuple)


def get_settings() -> Settings:
    """Return a freshly read :class:`Settings` from the current environment.

    Reading every field inside this function (rather than as dataclass
    defaults evaluated at import time) guarantees that environment
    overrides set after module import — the normal case in tests — are
    honoured on the next ``get_settings()`` call.
    """
    return Settings(
        service_name=os.getenv("BOSS_SERVICE_NAME", "boss-engine"),
        environment=os.getenv("BOSS_ENV", "development"),
        log_level=os.getenv("BOSS_LOG_LEVEL", "INFO"),
        api_prefix=os.getenv("BOSS_API_PREFIX", "/v1"),
        cors_origins=_env_tuple("BOSS_CORS_ORIGINS", "*"),
        auth_enabled=_env_bool("BOSS_AUTH_ENABLED", False),
        jwt_issuer=os.getenv("BOSS_JWT_ISSUER", "boss-engine"),
        jwt_audience=os.getenv("BOSS_JWT_AUDIENCE", "boss-engine"),
        jwt_secret=os.getenv("BOSS_JWT_SECRET", ""),
        flight_recorder_path=os.getenv(
            "BOSS_FLIGHT_RECORDER_PATH", "/var/lib/boss/flight-recorder.jsonl"
        ),
        neo4j_uri=os.getenv("BOSS_NEO4J_URI", ""),
        neo4j_user=os.getenv("BOSS_NEO4J_USER", "neo4j"),
        neo4j_password=os.getenv("BOSS_NEO4J_PASSWORD", ""),
        neo4j_database=os.getenv("BOSS_NEO4J_DATABASE", "neo4j"),
        metrics_enabled=_env_bool("BOSS_METRICS_ENABLED", True),
        otel_endpoint=os.getenv("BOSS_OTEL_ENDPOINT", ""),
        admin_tokens=_env_tuple("BOSS_ADMIN_TOKENS", ""),
    )
