"""
ADAM DNA Tool - FastAPI Application Entry Point
AI-powered conversational engine for ADAM DNA configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import structlog
import os

from app.core.config import settings
from app.api.routes import router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()

app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ADAM DNA Configuration Tool — AI-powered conversational engine that guides users
    through implementing the Autonomous Doctrine & Architecture Model.

    Replaces the static DNA Questionnaire with an intelligent, document-aware
    conversational interface that analyzes uploaded strategy documents, asks targeted
    questions, and generates deployment-ready ADAM configurations.
    """,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(router, prefix="/api")

# Serve frontend static files in production
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")


@app.on_event("startup")
async def startup():
    logger.info(
        "ADAM DNA Tool starting",
        version=settings.APP_VERSION,
        ai_provider=settings.AI_PROVIDER,
        debug=settings.DEBUG,
    )

    # Ensure directories exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)


@app.on_event("shutdown")
async def shutdown():
    logger.info("ADAM DNA Tool shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
