# =============================================================
# ADAM DNA Tool - Backend Dockerfile
# Multi-stage build for production-ready Python FastAPI backend
# =============================================================

# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system deps for document processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

LABEL maintainer="ADAM Framework <adam@example.com>"
LABEL description="ADAM DNA Tool Backend - AI-Powered DNA Configuration Engine"
LABEL version="1.1.0"

# Non-root user
RUN groupadd -r adam && useradd -r -g adam -m adam

# Copy Python packages
COPY --from=builder /install /usr/local

# Create working directories
RUN mkdir -p /app /tmp/adam-dna-uploads /tmp/adam-dna-output /app/adam-docs /app/dna-tool && \
    chown -R adam:adam /app /tmp/adam-dna-uploads /tmp/adam-dna-output

WORKDIR /app

# Copy application code
COPY --chown=adam:adam app/ /app/app/

# Copy ADAM documentation (mounted in K8s via ConfigMap or volume)
# These are optional - can be mounted at runtime
# COPY --chown=adam:adam adam-docs/ /app/adam-docs/

USER adam

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8000/api/health'); r.raise_for_status()" || exit 1

# Run with uvicorn
CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--log-level", "info"]
