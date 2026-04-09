# ⚡ Erebus

**Feature-packed AI agent** combining the [Agno](https://docs.agno.com) framework with [Hermes Agent](https://github.com/NousResearch/hermes-agent)–style features: agentic memory, autonomous skills, cron scheduling, soul/personality, multi-model support, and multi-channel messaging.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Agno](https://img.shields.io/badge/Agno-v2.5.15-brightgreen.svg)](https://docs.agno.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Features

| Feature | Description |
|---------|-------------|
| **Multi-Model** | Switch between any LLM provider with `provider:model_id` syntax — OpenAI, Anthropic, Google, OpenRouter, Ollama, and more |
| **Agentic Memory** | Agent-curated persistent memory per user via Agno MemoryManager + SQLite |
| **Session Storage** | Conversation history persisted across sessions |
| **Skills System** | Built-in skills + user-created skills stored as JSON, auto-discovered at startup |
| **Cron Scheduler** | Natural-language–described cron jobs with timezone support and delivery to any channel |
| **Soul / Personality** | SOUL.md–style personality definitions that shape agent behavior |
| **Telegram Bot** | Full Telegram integration via Agno's built-in Telegram interface |
| **Microsoft Teams** | Teams bot via Bot Framework SDK |
| **Web UI** | Next.js + Shadcn dashboard with chat, memory, skills, schedules, soul, channels, and settings |
| **Rich CLI** | Interactive terminal with panels, tables, spinners, markdown rendering, and syntax highlighting |
| **REST API** | FastAPI backend powering both the CLI and web UI |

---

## Architecture

```
erebus/
├── core/           # Agent factory (Agno Agent + multi-model)
├── memory/         # MemoryManager facade
├── skills/         # Skill registry + built-in skills
│   └── builtins/   # Shipped skills (web search, etc.)
├── scheduler/      # Cron scheduler (croniter + JSON persistence)
├── soul/           # SOUL.md loader and personality management
├── channels/       # Telegram + Microsoft Teams integrations
├── cli/            # Rich-powered interactive terminal
│   ├── main.py     # Entry point (chat, serve, telegram, teams)
│   └── console.py  # Rich panels, tables, spinners, markdown
├── api/            # FastAPI REST API server
│   └── server.py   # All endpoints (chat, memory, skills, etc.)
└── config.py       # pydantic-settings configuration

web/                # Next.js + Shadcn web UI
├── src/
│   ├── app/        # App Router pages
│   │   ├── chat/       # Chat interface
│   │   ├── memory/     # Memory management
│   │   ├── skills/     # Skills management
│   │   ├── schedules/  # Cron schedule management
│   │   ├── soul/       # Personality editor
│   │   ├── channels/   # Channel status
│   │   └── settings/   # Configuration
│   ├── components/ # Shadcn UI components + sidebar
│   ├── hooks/      # Custom React hooks
│   └── lib/        # API client + utilities
└── ...
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for web UI)
- An LLM API key (OpenAI, Anthropic, etc.)

### 1. Install the Python Backend

```bash
# Clone the repository
git clone https://github.com/nitzzzu/Erebus.git
cd Erebus

# Install with pip
pip install -e ".[all]"
```

### 2. Configure

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

### 3. Start Chatting (CLI)

```bash
erebus chat
```

Available CLI commands:
| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/model [provider:id]` | Show or switch the active model |
| `/skills` | List registered skills |
| `/memory [user_id]` | List stored memories |
| `/schedules` | List cron schedules |
| `/soul` | Show current personality |
| `/new` | Start a new session |
| `/quit` | Exit |

### 4. Start the API Server

```bash
erebus serve
```

The REST API starts on `http://localhost:8741`.

### 5. Start the Web UI

```bash
cd web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) — the dashboard connects to the API at `localhost:8741`.

### 6. Start the Telegram Bot

```bash
erebus telegram
```

### 7. Start the Teams Bot

```bash
erebus teams
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

Skills are the agent's reusable capabilities. Built-in skills ship with Erebus, and you can create your own:

**Built-in skills** live in `erebus/skills/builtins/` — each is a Python module exposing `SKILL_META` and a `tools()` function.

**User skills** are JSON files in `~/.erebus/skills/`:

```json
{
  "name": "weather_lookup",
  "description": "Look up current weather for any city",
  "code": "..."
}
```

Create skills via the REST API or Web UI.

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

## Rich CLI Output

The terminal interface uses the [Rich](https://rich.readthedocs.io) library for:

- **Panels** — agent responses wrapped in styled borders
- **Tables** — skills, memories, schedules displayed as formatted tables
- **Spinners** — "Thinking…" status indicator while waiting for the agent
- **Markdown** — rendered markdown in the terminal
- **Syntax highlighting** — code blocks with syntax coloring

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send a message to the agent |
| `/api/memory/{user_id}` | GET | List memories for a user |
| `/api/memory/{memory_id}` | DELETE | Delete a memory |
| `/api/skills` | GET | List all skills |
| `/api/skills` | POST | Create a new skill |
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