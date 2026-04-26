# syntax=docker/dockerfile:1.7
#
# Multi-stage build for the BOSS AI Governance & Risk Engine.
#
#   stage 1 (ui-builder):       compiles the React Vite console into /app/dist
#   stage 2 (python-builder):   builds the Python wheel and its dependencies
#   stage 3 (runtime):          minimal, non-root runtime image
#
# Build:
#   docker buildx build -t ghcr.io/hercamo/boss-engine:3.2.0 .
#
# Run:
#   docker run --rm -p 8080:8080 ghcr.io/hercamo/boss-engine:3.2.0
#
# The runtime image starts the FastAPI app under uvicorn behind the default
# port 8080. The compiled React console is served from /ui/.

ARG PYTHON_VERSION=3.12
ARG NODE_VERSION=20
ARG DEBIAN_RELEASE=bookworm

# -----------------------------------------------------------------------------
# Stage 1 — Evidence Console bundle (Vite + TypeScript + Tailwind)
# -----------------------------------------------------------------------------
FROM node:${NODE_VERSION}-${DEBIAN_RELEASE}-slim AS ui-builder

ENV CI=1 \
    NODE_ENV=production \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false

WORKDIR /app
COPY boss_console/package.json boss_console/package-lock.json* ./
# If a lockfile is present, npm ci is preferred; fall back to install otherwise.
RUN if [ -f package-lock.json ]; then npm ci --no-audit --no-progress; \
    else npm install --no-audit --no-progress; fi

COPY boss_console/ ./
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2 — Python wheel builder
# -----------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-${DEBIAN_RELEASE} AS python-builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore

RUN apt-get update \
 && apt-get install --no-install-recommends -y \
      build-essential \
      libffi-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY pyproject.toml README.md LICENSE* NOTICE* ./
COPY boss_core ./boss_core
COPY boss_api ./boss_api
COPY boss_graph ./boss_graph
COPY boss_adapters ./boss_adapters

RUN python -m pip install --upgrade pip build
RUN python -m build --wheel --outdir /wheels
RUN python -m pip install --prefix=/install --no-compile /wheels/*.whl \
    "fastapi>=0.115,<0.120" \
    "pydantic>=2.8,<3.0" \
    "pydantic-settings>=2.4,<3.0" \
    "uvicorn[standard]>=0.30,<0.40" \
    "python-json-logger>=2.0,<3.0" \
    "PyJWT>=2.9,<3.0" \
    "cryptography>=43.0,<46.0" \
    "prometheus-client>=0.20,<0.22"

# -----------------------------------------------------------------------------
# Stage 3 — Runtime (distroless-like slim image, non-root)
# -----------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-${DEBIAN_RELEASE} AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    BOSS_ENV=production \
    BOSS_SERVICE_NAME=boss-engine \
    BOSS_API_PREFIX=/v1 \
    BOSS_FLIGHT_RECORDER_PATH=/var/lib/boss/flight-recorder.jsonl \
    BOSS_METRICS_ENABLED=1 \
    PATH="/opt/boss/bin:${PATH}" \
    PYTHONPATH=/opt/boss/lib/python3.12/site-packages

LABEL org.opencontainers.image.title="BOSS AI Governance & Risk Engine" \
      org.opencontainers.image.source="https://github.com/Hercamo/ADAM" \
      org.opencontainers.image.description="Standalone BOSS scoring, exception, and evidence service for the ADAM model." \
      org.opencontainers.image.vendor="ADAM Project" \
      org.opencontainers.image.licenses="ADAM-Copyright-and-Use-Agreement" \
      org.opencontainers.image.version="3.2.0"

RUN apt-get update \
 && apt-get install --no-install-recommends -y \
      tini \
      ca-certificates \
      curl \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd --system --gid 1000 boss \
 && useradd --system --uid 1000 --gid boss --home-dir /home/boss --create-home \
      --shell /usr/sbin/nologin boss \
 && install -d -o boss -g boss -m 0750 /var/lib/boss /var/log/boss

COPY --from=python-builder /install /opt/boss
COPY --from=ui-builder /app/dist /opt/boss/ui
COPY boss_graph/schema.cypher boss_graph/seed.cypher /opt/boss/share/boss_graph/
COPY scripts /opt/boss/share/scripts

USER boss
WORKDIR /home/boss

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8080/v1/healthz || exit 1

ENTRYPOINT ["tini", "--"]
CMD ["uvicorn", "boss_api.app:create_app", "--factory", \
     "--host", "0.0.0.0", "--port", "8080", \
     "--workers", "2", "--proxy-headers", "--forwarded-allow-ips=*"]
