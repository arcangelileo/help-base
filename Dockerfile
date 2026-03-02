# =============================================================================
# HelpBase — Production Dockerfile (multi-stage)
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Build — install dependencies in a temporary image
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install build-time system deps (gcc for bcrypt/cffi wheels)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a prefix we can copy later
COPY pyproject.toml ./
RUN pip install --no-cache-dir --prefix=/install .

# ---------------------------------------------------------------------------
# Stage 2: Runtime — lean final image
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Default config (override via env / .env)
    HELPBASE_DATABASE_URL=sqlite+aiosqlite:///app/data/helpbase.db \
    HELPBASE_BASE_URL=http://localhost:8000 \
    HELPBASE_DEBUG=false

WORKDIR /app

# Copy pre-built Python packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY src/ ./src/

# Create a non-root user and the data directory
RUN groupadd --gid 1000 helpbase && \
    useradd --uid 1000 --gid helpbase --shell /bin/bash --create-home helpbase && \
    mkdir -p /app/data && \
    chown -R helpbase:helpbase /app

USER helpbase

EXPOSE 8000

# Health check — hit the /health endpoint every 30 s
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]

# Run migrations then start uvicorn
# --workers 1 is fine for SQLite; scale horizontally with replicas instead
# Exec form ensures uvicorn is PID 1 and receives SIGTERM for graceful shutdown
CMD ["sh", "-c", "cd /app && python -m alembic upgrade head && exec uvicorn helpbase.app:app --host 0.0.0.0 --port 8000 --workers 1 --timeout-graceful-shutdown 30"]
