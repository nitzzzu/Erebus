# ⚡ Erebus

**The ultimate AI agent** — combining the [Agno](https://docs.agno.com) framework with [Hermes Agent](https://github.com/NousResearch/hermes-agent)–style skills, MCP integration, agentic memory, cron scheduling, soul/personality, multi-model support, and multi-channel messaging.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Agno](https://img.shields.io/badge/Agno-v2.5.15-brightgreen.svg)](https://docs.agno.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Features

| Feature | Description |
|---------|-------------|
| **Unified Gateway** | Single process serves API, web UI, Telegram, and Teams — `erebus gateway` |
| **Docker Support** | Multi-stage Dockerfile + Docker Compose for one-command deployment |
| **47 Skills** | Hermes-style SKILL.md skills organized in 17 categories — research, coding, creative, productivity, DevOps, and more |
| **GitHub Skills** | Load and sync skills directly from GitHub repositories |
| **MCP Integration** | Connect to any Model Context Protocol server (stdio, SSE, HTTP) via config file |
| **Multi-Model** | Switch between any LLM provider with `provider:model_id` syntax — OpenAI, Anthropic, Google, OpenRouter, Ollama, and more |
| **TOML/JSON Config** | Agent configuration via `erebus.toml` or `erebus.json` — models, skills, MCP servers, and more |
| **Recursive Skill Loader** | Hermes-style nested directory skill discovery from folders and subfolders |
| **Agentic Memory** | Agent-curated persistent memory per user via Agno MemoryManager + SQLite |
| **Session Storage** | Conversation history persisted across sessions |
| **Cron Scheduler** | Natural-language–described cron jobs with timezone support and delivery to any channel |
| **Soul / Personality** | SOUL.md–style personality definitions that shape agent behavior |
| **Telegram Bot** | Full Telegram integration via Agno's built-in Telegram interface |
| **Microsoft Teams** | Teams bot via Bot Framework SDK |
| **Web UI** | Next.js + Shadcn dashboard with chat, memory, skills, schedules, soul, channels, and settings |
| **Rich CLI** | Interactive terminal with panels, tables, spinners, markdown rendering, and syntax highlighting |
| **REST API** | FastAPI backend powering both the CLI and web UI |
| **External Skills** | Load custom skills from any directory — share skills across projects |
| **Onboarding** | Automatic setup page when agent not yet configured |
| **Progressive Disclosure** | Skills use lazy loading — agent sees summaries, loads full instructions on demand |

---

## Skills Library (47 Skills in 17 Categories)

| Category | Skills | Description |
|----------|--------|-------------|
| **MCP** | native-mcp, mcporter | Model Context Protocol server integration |
| **Research** | arxiv, blogwatcher, llm-wiki, polymarket | Academic papers, RSS feeds, knowledge bases, prediction markets |
| **Creative** | ascii-art, excalidraw, manim-video, p5js, popular-web-designs, songwriting | ASCII art, diagrams, animations, generative art, design systems, music |
| **Productivity** | google-workspace, linear, nano-pdf, notion, ocr-and-documents, powerpoint | Gmail/Calendar/Drive, Linear issues, PDF editing, Notion, OCR, slides |
| **Software Dev** | plan, code-review, subagent-development, systematic-debugging, tdd, writing-plans | Planning, review, TDD, debugging, implementation workflows |
| **GitHub** | codebase-inspection, github-auth, github-code-review, github-issues, github-pr-workflow, github-repo-management | Full GitHub workflow automation |
| **Data Science** | jupyter-live-kernel | Interactive Jupyter kernels for data exploration |
| **DevOps** | webhook-subscriptions | Event-driven automation with webhooks |
| **Social Media** | xitter | X (Twitter) posting, search, and management |
| **Email** | himalaya | Full email client via Himalaya CLI |
| **Media** | gif-search, youtube-content | GIF search, YouTube transcript extraction |
| **Note-Taking** | obsidian | Obsidian vault management |
| **Smart Home** | openhue | Philips Hue light control |
| **Autonomous Agents** | claude-code, codex, opencode | Delegate to AI coding agents |
| **MLOps** | huggingface-hub | Hugging Face models and datasets |
| **Leisure** | find-nearby | Local place discovery via OpenStreetMap |
| **QA Testing** | dogfood | Systematic web app QA testing |

---

## Architecture

```
erebus/
├── gateway/        # Unified gateway (API + channels + web UI)
│   ├── server.py   # Gateway app factory
│   └── channels/   # Channel subsystem
│       ├── base.py           # Abstract BaseChannel
│       ├── manager.py        # Channel manager (enable/disable)
│       ├── telegram_channel.py  # Telegram via Agno interface
│       └── teams_channel.py     # Teams via Bot Framework
├── core/           # Agent factory (Agno Agent + multi-model + MCP)
├── memory/         # MemoryManager facade
├── skills/         # Hermes-style skill system
│   ├── loader.py        # Recursive skill discovery from nested dirs
│   ├── registry.py      # Skill metadata registry + categories
│   ├── github_loader.py # GitHub skill sync + caching
│   └── builtins/        # 47 skills in 17 categories
├── scheduler/      # Cron scheduler (croniter + JSON persistence)
├── soul/           # SOUL.md loader and personality management
├── channels/       # Legacy channel implementations
├── cli/            # Rich-powered interactive terminal
├── api/            # FastAPI REST API server
├── mcp.py          # MCP server config and connection management
├── agent_config.py # TOML/JSON config file loader
└── config.py       # pydantic-settings configuration

web/                # Next.js + Shadcn web UI
├── src/
│   ├── app/        # App Router pages
│   ├── components/ # Shadcn UI components + sidebar
│   ├── hooks/      # Custom React hooks
│   └── lib/        # API client + utilities
└── ...

Dockerfile          # Multi-stage build (Node.js + Python)
docker-compose.yml  # Single-command deployment
.env.example        # Environment variable template
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for web UI)
- An LLM API key (OpenAI, Anthropic, etc.)

### Option A: Docker (Recommended)

The fastest way to get started — everything runs in a single container:

```bash
# Clone the repository
git clone https://github.com/nitzzzu/Erebus.git
cd Erebus

# Copy and configure environment
cp .env.example .env
# Edit .env to add your API key(s)

# Start with Docker Compose
docker compose up -d

# Open http://localhost:8741
```

The unified gateway serves everything:
- **Web UI** at `/`
- **REST API** at `/api/`
- **Telegram bot** at `/telegram/webhook` (if configured)
- **Teams bot** at `/api/messages` (if configured)

If no API key is configured, the gateway shows an onboarding page with setup instructions.

### Option B: Local Install

#### 1. Install the Python Backend

```bash
# Clone the repository
git clone https://github.com/nitzzzu/Erebus.git
cd Erebus

# Install with pip
pip install -e ".[all]"
```

#### 2. Configure

Create a `.env` file in the project root:

```env
# Required: at least one model provider key
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...
# or
OPENROUTER_API_KEY=sk-or-...

# Optional: override the default model
EREBUS_DEFAULT_MODEL=openai:gpt-4o

# Optional: add a reasoning model for complex tasks
EREBUS_REASONING_MODEL=anthropic:claude-sonnet-4-20250514

# Optional: Telegram bot
EREBUS_TELEGRAM_TOKEN=123456:ABC-DEF...

# Optional: Microsoft Teams
EREBUS_TEAMS_APP_ID=...
EREBUS_TEAMS_APP_PASSWORD=...
```

#### 3. Agent Config File (Optional)

Create `erebus.toml` for advanced configuration:

```toml
[agent]
name = "Erebus"
# default_model = "openai:gpt-4o"

[skills]
# extra_dirs = ["~/my-skills"]
# disabled = ["red-teaming"]

# Load skills from GitHub
# [[skills.github]]
# repo = "owner/repo"
# path = "skills"
# ref = "main"

# Add MCP servers
[[mcp.servers]]
name = "filesystem"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/home"]

[[mcp.servers]]
name = "brave-search"
url = "https://mcp.brave.com/sse"
transport = "sse"
env = { BRAVE_API_KEY = "your-key" }
```

See `erebus.toml.example` for all options.

#### 4. Start the Unified Gateway (Recommended)

```bash
erebus gateway
```

This starts a single process that serves the API, web UI, and all configured channels (Telegram, Teams).

#### 5. Or Start Individual Services

```bash
# Interactive CLI chat
erebus chat

# API server only
erebus serve

# Build and run the web UI (development mode)
cd web && npm install && npm run dev
```

---

## Multi-Model Support

Erebus uses Agno's model-as-string syntax. Switch models at any time:

```bash
# In the CLI
/model openai:gpt-4o
/model anthropic:claude-sonnet-4-20250514
/model openrouter:meta-llama/llama-3-70b-chat-hf
/model google:gemini-2.5-pro
/model ollama:llama3.2
```

Supported providers: OpenAI, Anthropic, Google, Groq, Ollama, OpenRouter, Together, Mistral, Azure AI Foundry, LiteLLM, and more.

---

## Skills System

### Hermes-Style Organization

Skills are organized in nested category directories, just like Hermes Agent:

```
erebus/skills/builtins/
├── mcp/
│   ├── DESCRIPTION.md          # Category description
│   ├── native-mcp/
│   │   └── SKILL.md            # Skill instructions
│   └── mcporter/
│       └── SKILL.md
├── research/
│   ├── arxiv/SKILL.md
│   ├── blogwatcher/SKILL.md
│   └── ...
└── software-development/
    ├── plan/SKILL.md
    ├── test-driven-development/SKILL.md
    └── ...
```

### Progressive Disclosure

1. **Browse**: Agent sees skill names and descriptions in its system prompt
2. **Load**: When a task matches a skill, the agent loads full instructions
3. **Reference**: Agent accesses detailed documentation as needed
4. **Execute**: Agent can run scripts from the skill

### Creating Custom Skills

Create a new skill in `~/.erebus/skills/` or any external directory:

```
my-skill/
├── SKILL.md           # Required: YAML frontmatter + instructions
├── scripts/           # Optional: executable scripts
│   └── helper.py
└── references/        # Optional: reference documentation
    └── guide.md
```

SKILL.md format:

```markdown
---
name: my-skill
description: Short description of what this skill does
metadata:
  tags: ["category", "keywords"]
---

# My Skill

Instructions for the agent on when and how to use this skill...
```

### Loading External Skills

Add external skill directories via config:

```toml
[skills]
extra_dirs = ["~/my-skills", "/shared/team-skills"]
```

### Loading Skills from GitHub

Sync skills directly from GitHub repositories:

```toml
# In erebus.toml
[[skills.github]]
repo = "owner/repo"           # GitHub repository
path = "skills"               # Subdirectory containing skills (default: root)
ref = "main"                  # Branch/tag/commit (default: repo default)

[[skills.github]]
repo = "another-org/more-skills"
```

Skills are cached in `~/.erebus/skills/github/` and synced on startup.

---

## MCP (Model Context Protocol) Integration

Connect to any MCP-compatible server for extended tool access:

```toml
# In erebus.toml
[[mcp.servers]]
name = "filesystem"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/home"]

[[mcp.servers]]
name = "database"
url = "https://db-mcp.example.com/sse"
transport = "sse"
env = { DB_CONNECTION = "postgresql://..." }
```

Supported transports:
- **stdio**: Local servers launched as child processes
- **SSE**: Remote servers with Server-Sent Events
- **streamable-http**: Remote servers with HTTP streaming

---

## Configuration

Erebus supports three layers of configuration:

| Layer | Source | Priority |
|-------|--------|----------|
| **Environment** | `.env` file + OS env vars | Base |
| **Config File** | `erebus.toml` or `erebus.json` | Override |
| **CLI** | Command-line flags | Highest |

Config file search order:
1. `EREBUS_CONFIG` environment variable
2. `./erebus.toml` or `./erebus.json` (current directory)
3. `~/.erebus/erebus.toml` or `~/.erebus/erebus.json`

---

## Cron Scheduler

Schedule automated agent tasks with natural-language descriptions:

```python
from erebus.scheduler.cron import ErebusScheduler

scheduler = ErebusScheduler()
scheduler.create(
    name="daily-briefing",
    cron="0 8 * * *",
    description="Generate and send a daily news briefing",
    timezone="America/New_York",
)
```

Manage schedules via CLI (`/schedules`), API, or Web UI.

---

## Soul / Personality

Customize the agent's personality by editing `~/.erebus/SOUL.md`:

```markdown
You are **Erebus**, a concise and insightful AI assistant.

## Core Traits
- Friendly but direct
- Always cite sources
- Use tools proactively

## Communication Style
- Prefer tables for structured data
- Keep responses focused
```

Edit via the Web UI's Soul page or through the API.

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send a message to the agent |
| `/api/chat/start` | POST | Start a streaming chat session |
| `/api/chat/stream` | GET | SSE endpoint for streaming responses |
| `/api/memory/{user_id}` | GET | List memories for a user |
| `/api/memory/{memory_id}` | DELETE | Delete a memory |
| `/api/skills` | GET | List all skills |
| `/api/skills/categories` | GET | List skill categories |
| `/api/skills/category/{name}` | GET | List skills in a category |
| `/api/skills` | POST | Create a new skill |
| `/api/mcp/servers` | GET | List configured MCP servers |
| `/api/config` | GET | Get agent configuration |
| `/api/schedules` | GET | List all schedules |
| `/api/schedules` | POST | Create a schedule |
| `/api/schedules/{id}` | PUT | Update a schedule |
| `/api/schedules/{id}` | DELETE | Delete a schedule |
| `/api/soul` | GET | Get soul/personality content |
| `/api/soul` | PUT | Update soul content |
| `/api/channels` | GET | List channel status |
| `/api/settings` | GET | Get current settings |
| `/api/settings` | PUT | Update settings |
| `/api/health` | GET | Health check |

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Lint Python code
ruff check erebus/

# Build the web UI
cd web && npm run build
```

---

## License

MIT