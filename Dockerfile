# ─── Erebus — Multi-stage Dockerfile ─────────────────────────────────────────
# Stage 1: Build the Next.js web UI (static export)
# Stage 2: Tools builder (usql, rar, duckdb, ripgrep, fd, sd, ouch)
# Stage 3: Build ErebusLite (Go / Eino)
# Stage 4: Python runtime with the backend + pre-built frontend + Go binary
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

# ── Stage 2: Tools builder ──────────────────────────────────────────────────
FROM python:3.14-slim AS tools-builder

ARG USQL_VERSION=0.20.8
ARG RAR_VERSION=624
ARG DUCKDB_VERSION=1.4.4
ARG RIPGREP_VERSION=15.1.0
ARG FD_VERSION=10.3.0
ARG SD_VERSION=1.0.0
ARG OUCH_VERSION=0.6.1

# Install download tools
RUN apt-get update && \
    apt-get install -y \
    curl unzip bzip2 wget xz-utils \
    ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Download and prepare all tool binaries
WORKDIR /tmp
RUN mkdir -p /tools-binaries

# usql
RUN curl -fsSL https://github.com/xo/usql/releases/download/v${USQL_VERSION}/usql-${USQL_VERSION}-linux-amd64.tar.bz2 | tar xjf - -C /tools-binaries

# rar/unrar
RUN wget -q https://www.rarlab.com/rar/rarlinux-x64-${RAR_VERSION}.tar.gz && \
    tar -zxf rarlinux-x64-${RAR_VERSION}.tar.gz && \
    cp rar/rar rar/unrar /tools-binaries/ && \
    rm -rf rar rarlinux-x64-${RAR_VERSION}.tar.gz

# DuckDB
RUN curl -L https://github.com/duckdb/duckdb/releases/download/v${DUCKDB_VERSION}/duckdb_cli-linux-amd64.zip -o duckdb.zip && \
    unzip -q duckdb.zip -d /tools-binaries && \
    rm duckdb.zip

# ripgrep
RUN curl -L https://github.com/BurntSushi/ripgrep/releases/download/${RIPGREP_VERSION}/ripgrep-${RIPGREP_VERSION}-x86_64-unknown-linux-musl.tar.gz | tar xzf - && \
    mv ripgrep-${RIPGREP_VERSION}-x86_64-unknown-linux-musl/rg /tools-binaries/ && \
    rm -rf ripgrep-${RIPGREP_VERSION}-x86_64-unknown-linux-musl

# fd
RUN curl -L https://github.com/sharkdp/fd/releases/download/v${FD_VERSION}/fd-v${FD_VERSION}-x86_64-unknown-linux-musl.tar.gz | tar xzf - && \
    mv fd-v${FD_VERSION}-x86_64-unknown-linux-musl/fd /tools-binaries/ && \
    rm -rf fd-v${FD_VERSION}-x86_64-unknown-linux-musl

# sd
RUN curl -L https://github.com/chmln/sd/releases/download/v${SD_VERSION}/sd-v${SD_VERSION}-x86_64-unknown-linux-musl.tar.gz | tar xzf - && \
    mv sd-v${SD_VERSION}-x86_64-unknown-linux-musl/sd /tools-binaries/ && \
    rm -rf sd-v${SD_VERSION}-x86_64-unknown-linux-musl

# ouch
RUN curl -L https://github.com/ouch-org/ouch/releases/download/${OUCH_VERSION}/ouch-x86_64-unknown-linux-musl.tar.gz | tar xzf - && \
    mv ouch-x86_64-unknown-linux-musl/ouch /tools-binaries/ && \
    rm -rf ouch-x86_64-unknown-linux-musl

# Make all binaries executable
RUN chmod +x /tools-binaries/*

# ── Stage 3: Build ErebusLite (Go) ──────────────────────────────────────────
# FROM golang:1.24-alpine AS go-builder

# WORKDIR /build/erebuslite

# # Copy go module files first (layer caching)
# COPY erebuslite/go.mod erebuslite/go.sum ./
# RUN go mod download

# # Copy source and build
# COPY erebuslite/ ./
# RUN CGO_ENABLED=0 go build -o /erebuslite ./cmd/main.go

# ── Stage 4: Python runtime ─────────────────────────────────────────────────
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

# Copy ErebusLite binary from stage 3
#COPY --from=go-builder /erebuslite ./erebuslite

# Copy tool binaries from tools-builder
COPY --from=tools-builder /tools-binaries/* /usr/local/bin/

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
