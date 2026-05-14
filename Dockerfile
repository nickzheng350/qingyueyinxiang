# =============================================================================
# HydraFlow AI - Production Dockerfile
# Multi-stage build for minimal image size and fast deployment
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - compile Python dependencies
# -----------------------------------------------------------------------------
FROM python:3.10-slim AS builder

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        build-essential \
        libssl-dev \
        libffi-dev \
        python3-dev \
        cargo \
        rustc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifests first (layer cache optimization)
COPY requirements.txt pyproject.toml ./

# Pre-install wheelhouse to avoid repeated compilation
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip wheel && \
    /opt/venv/bin/pip wheel --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Runtime - minimal production image
# -----------------------------------------------------------------------------
FROM python:3.10-slim AS runtime

# Security: run as non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        libssl1.1 \
        libffi7 \
        libgomp1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built Python packages from builder stage
COPY --from=builder /opt/venv /app/.venv

# Set Python environment
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    VIRTUAL_ENV=/app/.venv

# Copy application source
COPY --chown=appuser:appuser src/ src/
COPY --chown=appuser:appuser config/ config/
COPY --chown=appuser:appuser main.py ./
COPY --chown=appuser:appuser prompts/ prompts/ 2>/dev/null || true
COPY --chown=appuser:appuser plugins/ plugins/ 2>/dev/null || true
COPY --chown=appuser:appuser skills/ skills/ 2>/dev/null || true
COPY --chown=appuser:appuser dist/requirements.txt ./

# Create required directories
RUN mkdir -p /app/data /app/logs /app/uploads /app/config /app/prompts /app/plugins /app/skills && \
    touch /app/config/.gitkeep /app/prompts/.gitkeep /app/plugins/.gitkeep /app/skills/.gitkeep && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check (as root for curl)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -sf http://localhost:8000/health/ || exit 1

# Run with uvicorn, binding to all interfaces
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "4", "--loop", "uvloop", "--http", "httptools"]