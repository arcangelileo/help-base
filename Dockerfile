FROM python:3.13-slim AS base

# Prevent Python from writing .pyc and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir . && \
    apt-get purge -y --auto-remove gcc

# Copy application code
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY src/ ./src/

# Create data directory for SQLite
RUN mkdir -p /app/data

# Default environment
ENV HELPBASE_DATABASE_URL=sqlite+aiosqlite:///app/data/helpbase.db \
    HELPBASE_BASE_URL=http://localhost:8000 \
    HELPBASE_DEBUG=false

EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "helpbase.app:app", "--host", "0.0.0.0", "--port", "8000"]
