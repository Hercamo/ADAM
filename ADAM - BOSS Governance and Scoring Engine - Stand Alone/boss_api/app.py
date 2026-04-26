"""FastAPI application factory for the BOSS AI Governance & Risk Engine."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from boss_api.config import Settings, get_settings
from boss_api.routers import (
    config_router,
)
from boss_api.routers import (
    exceptions as exceptions_router,
)
from boss_api.routers import (
    flight_recorder as flight_recorder_router,
)
from boss_api.routers import (
    graph as graph_router,
)
from boss_api.routers import (
    health as health_router,
)
from boss_api.routers import (
    intent as intent_router,
)
from boss_api.routers import (
    receipts as receipts_router,
)
from boss_api.routers import (
    score as score_router,
)
from boss_api.telemetry import configure_logging
from boss_core.version import __version__


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and return a FastAPI application instance."""
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="BOSS AI Governance & Risk Engine",
        description=(
            "Standalone implementation of the ADAM Business Operations Sovereignty "
            "Score (BOSS), independent of any specific agent framework."
        ),
        version=__version__,
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
        contact={
            "name": "ADAM — Autonomy Doctrine & Architecture Model",
            "url": "https://github.com/Hercamo/ADAM",
        },
        license_info={
            "name": "ADAM Copyright and Use Agreement",
            "url": "https://github.com/Hercamo/ADAM",
        },
    )

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
        )

    prefix = settings.api_prefix
    app.include_router(health_router.router, prefix=prefix)
    app.include_router(intent_router.router, prefix=prefix)
    app.include_router(score_router.router, prefix=prefix)
    app.include_router(exceptions_router.router, prefix=prefix)
    app.include_router(receipts_router.router, prefix=prefix)
    app.include_router(config_router.router, prefix=prefix)
    app.include_router(graph_router.router, prefix=prefix)
    app.include_router(flight_recorder_router.router, prefix=prefix)

    return app


app = create_app()


def main() -> None:
    """CLI entry point (``boss-api``): run the API under ``uvicorn``.

    The entry point honours the same environment variables consumed by
    :class:`boss_api.config.Settings`, plus a small set of uvicorn
    knobs:

    * ``BOSS_HOST`` (default ``0.0.0.0``)
    * ``BOSS_PORT`` (default ``8080``)
    * ``BOSS_UVICORN_WORKERS`` (default ``1``)
    * ``BOSS_UVICORN_PROXY_HEADERS`` (default ``true``)
    """
    import os

    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "boss_api.app:app",
        host=os.getenv("BOSS_HOST", "0.0.0.0"),  # noqa: S104 — bind for container deploys
        port=int(os.getenv("BOSS_PORT", "8080")),
        workers=int(os.getenv("BOSS_UVICORN_WORKERS", "1")),
        proxy_headers=os.getenv("BOSS_UVICORN_PROXY_HEADERS", "true").lower()
        in {"1", "true", "yes", "on"},
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
