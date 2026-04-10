# ErebusLite

A lightweight Go reimplementation of [Erebus](https://github.com/nitzzzu/Erebus) powered by [Cloudwego Eino](https://github.com/cloudwego/eino).

ErebusLite provides the same core features and API endpoints as the main Erebus agent, minus the legacy Python-specific components, and is accessible through the **same web UI**.

## Features

- **Eino AI Framework** — Built on Cloudwego's Eino with `ChatModelAgent` and ADK runner
- **Same API** — Drop-in replacement for the Erebus Python backend; same endpoints, same SSE streaming protocol
- **Same Web UI** — Serves the pre-built Next.js frontend from `web/out/`
- **Skills System** — Loads SKILL.md files from hermes-style nested directories
- **MCP Integration** — Connects to MCP servers (stdio, SSE, streamable-http) via eino-ext
- **Session Management** — JSON-file-backed chat sessions with full CRUD
- **Cron Scheduler** — Create, update, delete scheduled tasks via API
- **Soul/Personality** — SOUL.md-based agent customization
- **Notification System** — Webhook-based notification channels
- **Multi-Model Support** — OpenAI, OpenRouter, and any OpenAI-compatible API
- **Tool Calling** — Shell execution, file read/write, web search via Eino's ReAct agent

## Quick Start

### 1. Build

```bash
cd erebuslite
go build -o erebuslite ./cmd/main.go
```

### 2. Configure

```bash
export EREBUS_OPENAI_API_KEY=sk-...
# or
export OPENAI_API_KEY=sk-...
```

Optional: create `erebus.toml` for MCP servers, skills, etc. (same format as main Erebus).

### 3. Run

```bash
./erebuslite
# → ErebusLite gateway starting on 0.0.0.0:8741
```

### 4. Build & Serve Web UI

```bash
cd ../web
npm ci && npm run build
cd ../erebuslite
./erebuslite
# → Web UI served from ../web/out/
```

## API Endpoints

All endpoints match the main Erebus API for full web UI compatibility:

| Endpoint | Method | Description |
|---|---|---|
| `/api/chat` | POST | Sync chat |
| `/api/chat/start` | POST | Start streaming chat (returns stream_id) |
| `/api/chat/stream` | GET | SSE stream (connect with stream_id) |
| `/api/sessions` | GET/POST | List/create sessions |
| `/api/sessions/{id}` | GET/DELETE | Get/delete session |
| `/api/sessions/{id}/rename` | PUT | Rename session |
| `/api/memory/{user_id}` | GET | List memories |
| `/api/skills` | GET/POST | List/create skills |
| `/api/skills/categories` | GET | List skill categories |
| `/api/mcp/servers` | GET | List MCP servers |
| `/api/schedules` | GET/POST | List/create schedules |
| `/api/schedules/{id}` | PUT/DELETE | Update/delete schedule |
| `/api/soul` | GET/PUT | Get/update soul |
| `/api/settings` | GET/PUT | Get/update settings |
| `/api/notifications/channels` | GET/POST | List/create notification channels |
| `/api/notifications/test` | POST | Send test notification |
| `/api/channels` | GET | List messaging channels |
| `/api/health` | GET | Health check |
| `/api/config` | GET | Get agent config |
| `/api/context` | GET | Get AGENTS.md context |

## Configuration

ErebusLite reads the same configuration as main Erebus:

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `EREBUS_OPENAI_API_KEY` | — | OpenAI API key |
| `EREBUS_DEFAULT_MODEL` | `openai:gpt-4o` | Default model (provider:model) |
| `EREBUS_API_HOST` | `0.0.0.0` | API listen host |
| `EREBUS_API_PORT` | `8741` | API listen port |
| `EREBUS_DATA_DIR` | `~/.erebus` | Data directory |
| `EREBUS_SKILLS_DIR` | — | Additional skills directory |
| `EREBUS_SOUL_FILE` | — | Custom SOUL.md path |

### Config File (erebus.toml)

```toml
[agent]
name = "Erebus"
default_model = "openai:gpt-4o"

[skills]
extra_dirs = ["~/my-skills"]

[[mcp.servers]]
name = "filesystem"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/home"]
transport = "stdio"
```

## Architecture

```
erebuslite/
├── cmd/main.go                    # Entry point
├── internal/
│   ├── config/config.go           # Settings from env + TOML
│   ├── agent/agent.go             # Eino ChatModelAgent + tools
│   ├── api/server.go              # REST API (all endpoints)
│   ├── gateway/gateway.go         # Unified server (API + web UI)
│   ├── sessions/sessions.go       # JSON-file session store
│   ├── skills/skills.go           # SKILL.md loader & registry
│   ├── mcp/mcp.go                 # MCP server connections
│   ├── scheduler/scheduler.go     # Cron schedule CRUD
│   ├── soul/soul.go               # SOUL.md personality system
│   └── notifications/notifications.go  # Webhook notifications
├── go.mod
└── README.md
```

## What's Not Included (vs. main Erebus)

ErebusLite is deliberately lighter. These features are **not** ported:

- **Agentic Memory** — No automatic memory extraction (Agno-specific)
- **Telegram/Teams channels** — No messaging channel integrations
- **GitHub OAuth / Authelia auth** — No authentication middleware
- **Legacy Python skills** — No Python code skill execution
- **GitHub skills sync** — No auto-sync from GitHub repos
- **Rich CLI REPL** — No interactive terminal UI

## Docker

ErebusLite can be built as part of the Erebus Docker image. The Dockerfile includes a Go build stage:

```dockerfile
FROM golang:1.24-alpine AS go-builder
WORKDIR /build/erebuslite
COPY erebuslite/ ./
RUN go build -o /erebuslite ./cmd/main.go
```

## License

MIT — Same as main Erebus.
