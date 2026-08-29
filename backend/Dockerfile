# ========================================
# Builder Stage: Install dependencies
# ========================================
FROM python:3.11-slim AS builder

ARG INSTALL_DEV=false

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock* ./

RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
    if [ "$INSTALL_DEV" = "true" ]; then \
      poetry install --no-root --with dev; \
    else \
      poetry install --no-root --without dev; \
    fi

# ========================================
# Runtime Stage: Final image
# ========================================
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app \
    PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system --gid 1001 appuser \
    && useradd --system --uid 1001 --gid appuser --no-create-home appuser

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY . .

RUN mkdir -p /app/storage /app/storage/uploads /app/logs \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--loop", "uvloop"]
