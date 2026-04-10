# ─── Erebus — Multi-stage Dockerfile ─────────────────────────────────────────
# Stage 1: Build the Next.js web UI (static export)
# Stage 2: Build ErebusLite (Go / Eino)
# Stage 3: Python runtime with the backend + pre-built frontend + Go binary
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Build web UI ────────────────────────────────────────────────────
FROM node:22-slim AS web-builder

WORKDIR /build/web

# Install dependencies first (layer caching)
COPY web/package.json web/package-lock.json ./
RUN npm ci --ignore-scripts

# Copy source and build static export
COPY web/ ./
RUN npm run build

# ── Stage 2: Build ErebusLite (Go) ──────────────────────────────────────────
FROM golang:1.24-alpine AS go-builder

WORKDIR /build/erebuslite

# Copy go module files first (layer caching)
COPY erebuslite/go.mod erebuslite/go.sum ./
RUN go mod download

# Copy source and build
COPY erebuslite/ ./
RUN CGO_ENABLED=0 go build -o /erebuslite ./cmd/main.go

# ── Stage 3: Python runtime ─────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer caching)
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[all]" 2>/dev/null || true

# Copy the full application
COPY erebus/ ./erebus/
COPY pyproject.toml ./
COPY erebus.toml.example ./
COPY README.md ./

# Install the package
RUN pip install --no-cache-dir -e ".[all]"

# Copy the pre-built web UI from stage 1
COPY --from=web-builder /build/web/out ./web/out

# Copy ErebusLite binary from stage 2
COPY --from=go-builder /erebuslite ./erebuslite

# Create data directory
RUN mkdir -p /data

# Environment defaults
ENV EREBUS_DATA_DIR=/data \
    EREBUS_API_HOST=0.0.0.0 \
    EREBUS_API_PORT=8741 \
    PYTHONUNBUFFERED=1

EXPOSE 8741

VOLUME ["/data"]

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8741/api/health')" || exit 1

# Default: run the unified gateway
CMD ["erebus", "gateway"]
