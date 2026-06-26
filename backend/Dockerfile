# =============================================================================
# Backend Dockerfile - Multi-stage Python 3.12
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

LABEL maintainer="Lithology AI Team <team@lithology.ai>"
LABEL description="Automated Lithology Classification System - Backend Builder"

# Build arguments
ARG BUILDKIT_INLINE_CACHE=1

# Set environment variables for build stage
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
WORKDIR /build
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Production
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS production

LABEL maintainer="Lithology AI Team <team@lithology.ai>"
LABEL description="Automated Lithology Classification System - Backend Production"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app \
    APP_USER=appuser \
    APP_GROUP=appgroup \
    PORT=8000

# Install runtime system dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create non-root user and group
RUN groupadd --gid 1001 ${APP_GROUP} && \
    useradd --uid 1001 --gid ${APP_GROUP} --shell /bin/bash \
            --create-home --home-dir /home/${APP_USER} ${APP_USER}

# Create application directory and required directories
RUN mkdir -p ${APP_HOME}/uploads \
             ${APP_HOME}/model_weights \
             ${APP_HOME}/faiss_index \
             ${APP_HOME}/knowledge_base \
             ${APP_HOME}/logs \
    && chown -R ${APP_USER}:${APP_GROUP} ${APP_HOME}

# Set working directory
WORKDIR ${APP_HOME}

# Copy application source code
COPY --chown=${APP_USER}:${APP_GROUP} . .

# Create entrypoint script
RUN cat > /entrypoint.sh << 'EOF'
#!/bin/bash
set -e

echo "🪨 Starting Lithology Classification System Backend..."
echo "Environment: ${ENVIRONMENT:-production}"
echo "Port: ${PORT:-8000}"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

echo "Starting uvicorn server..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers ${WORKERS:-1} \
    --loop uvloop \
    --http httptools \
    --log-level ${LOG_LEVEL:-info} \
    --access-log \
    --proxy-headers \
    --forwarded-allow-ips='*'
EOF

RUN chmod +x /entrypoint.sh

# Switch to non-root user
USER ${APP_USER}

# Expose application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]
