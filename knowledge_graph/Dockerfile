# Dockerfile for Knowledge Graph API
# Multi-stage build for production deployment

# Stage 1: Build environment
FROM ghcr.io/prefix-dev/pixi:latest AS builder

WORKDIR /app

# Copy project files
COPY pixi.toml pixi.lock ./
COPY memory_core/ ./memory_core/
COPY scripts/ ./scripts/
COPY content/ ./content/
COPY edges/ ./edges/
COPY schema/ ./schema/

# Install dependencies
RUN pixi install

# Build artifacts
RUN pixi run build-memory || echo "Build may require pre-built memory_store"

# Stage 2: Runtime environment
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy built artifacts from builder
COPY --from=builder /app/memory_store/ ./memory_store/
COPY --from=builder /app/memory_core/ ./memory_core/

# Copy Pixi environment (lighter than full Pixi)
COPY --from=builder /app/.pixi/envs/default/lib/python3.11/site-packages/ \
     /usr/local/lib/python3.11/site-packages/

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run API server
CMD ["python", "-m", "memory_core.server", "--host", "0.0.0.0", "--port", "8000"]

# Metadata
LABEL maintainer="Knowledge Graph Team"
LABEL description="Knowledge Graph API with semantic search"
LABEL version="1.0.0"
