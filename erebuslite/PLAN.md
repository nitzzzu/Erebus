# ErebusLite — Build Plan

## Requirements
- Reimplement Erebus core features in Go using Cloudwego Eino framework
- Same REST API endpoints for compatibility with the existing Next.js web UI
- Located in `erebuslite/` directory within the repository
- No legacy features: no Python skills, no Agno-specific memory, no Telegram/Teams

## Tech Stack
- Go 1.24 + Eino v0.8.8 (ChatModelAgent + ADK Runner)
- eino-ext/openai for ChatModel (OpenAI-compatible providers)
- eino-ext/mcp for MCP server integration
- mcp-go v0.47.1 for MCP client connections
- Standard library net/http for REST API (no external web framework)
- BurntSushi/toml for config parsing
- robfig/cron for schedule validation
- yaml.v3 for SKILL.md frontmatter parsing

## Phases & Tasks

### Phase 1: Project Scaffold
- [x] go mod init, directory structure
- [x] config package (env vars + TOML loading)
- [x] soul package (SOUL.md load/save)

### Phase 2: Core Agent
- [x] Eino ChatModelAgent with tools (shell, file read/write, web search)
- [x] MCP tool integration
- [x] Instruction building (soul + config + skills + context)

### Phase 3: Data Layer
- [x] Session store (JSON files, CRUD, caching)
- [x] Skills registry (SKILL.md loader, categories)
- [x] Scheduler (cron CRUD, JSON persistence)
- [x] Notifications (webhook channels, CRUD)

### Phase 4: REST API
- [x] All endpoints matching Python Erebus API
- [x] SSE streaming chat (/api/chat/start + /api/chat/stream)
- [x] CORS middleware

### Phase 5: Gateway
- [x] Unified server (API + web UI static files)
- [x] SPA fallback routing (Next.js static export)
- [x] Onboarding page when unconfigured
- [x] Dockerfile updated with Go build stage

### Phase 6: Documentation
- [x] README.md with usage, API reference, architecture
- [x] CONTEXT.md with Eino API reference
- [x] PLAN.md

## Risks
- ⚠️ Eino ADK streaming may not provide token-level granularity like Agno
- ⚠️ MCP stdio transport requires subprocess management in Go
- ⚠️ Memory system not ported (Agno-specific)
