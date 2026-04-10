# ⚡ Erebus Web UI

Modern web dashboard for the Erebus AI agent, built with **Next.js 16**, **Shadcn/UI**, and **Tailwind CSS**.

---

## Features

### 💬 Chat Interface
- **Real-time streaming** — SSE-powered streaming responses with token-by-token display
- **Tool call visualization** — See when the agent uses tools (search, files, shell) with live status
- **Session management** — Create, switch between, rename, and delete chat sessions
- **Markdown rendering** — Full markdown support with syntax-highlighted code blocks
- **Auto-title** — Sessions automatically titled based on first message

### 🧠 Memory Management
- View all agent-curated memories per user
- Delete individual memories
- Memories persist across sessions for personalized interactions

### 🎯 Skills Browser
- Browse 47 skills organized in 17 categories
- View skill details, descriptions, and metadata
- Skills are sourced from built-in, user-created, and external directories
- Category filtering and search

### ⏰ Cron Scheduler
- Create and manage scheduled agent tasks
- Visual cron expression builder
- Enable/disable schedules
- Timezone support

### 👤 Soul / Personality Editor
- Edit the agent's personality and behavior rules
- Live preview of SOUL.md content
- Changes take effect on next conversation

### 📡 Channel Status
- View connected messaging channels (Web, Telegram, Teams)
- Configuration status for each channel

### ⚙️ Settings
- View and modify agent settings
- Model selection and switching
- Skills directory configuration

---

## Quick Start

### Prerequisites

- **Node.js 18+** (recommended: 20+)
- **Erebus API server** running on `http://localhost:8741`

### Installation

```bash
# Navigate to the web directory
cd web

# Install dependencies
npm install

# Start the development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production Build

```bash
npm run build
npm start
```

---

## Architecture

```
web/src/
├── app/                    # Next.js App Router
│   ├── page.tsx           # Home / redirect to chat
│   ├── chat/              # Chat interface
│   ├── memory/            # Memory management
│   ├── skills/            # Skills browser
│   ├── schedules/         # Cron scheduler
│   ├── soul/              # Personality editor
│   ├── channels/          # Channel status
│   └── settings/          # Configuration
├── components/            # Shared UI components
│   ├── ui/               # Shadcn/UI primitives
│   ├── app-sidebar.tsx   # Navigation sidebar
│   └── ...
├── hooks/                # Custom React hooks
├── lib/                  # Utilities
│   ├── api-client.ts    # API client for Erebus backend
│   └── utils.ts         # Helper functions
└── store/               # State management
    └── chat-context.tsx # Chat state (React Context + useReducer)
```

### State Management

The chat interface uses **React Context + useReducer** for state management:
- `ChatProvider` wraps the chat page
- Manages sessions, messages, streaming state, and tool calls
- SSE streaming via `EventSource` for real-time responses

### API Communication

All backend communication goes through `lib/api-client.ts`:
- Chat: `POST /api/chat/start` → `GET /api/chat/stream?stream_id=...`
- Sessions: `GET/POST/PUT/DELETE /api/sessions`
- Skills: `GET /api/skills`, `GET /api/skills/categories`
- Memory: `GET /api/memory/{user_id}`
- Config: `GET /api/config`, `GET /api/mcp/servers`

### Styling

- **Tailwind CSS** for utility-first styling
- **Shadcn/UI** component library for consistent design
- Dark mode support
- Responsive layout with collapsible sidebar

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8741` | Erebus API server URL |

Create a `.env.local` file if you need to customize:

```env
NEXT_PUBLIC_API_URL=http://your-server:8741
```

---

## Development

```bash
# Lint
npm run lint

# Type check
npx tsc --noEmit

# Build
npm run build
```

---

## Tech Stack

| Technology | Purpose |
|-----------|---------|
| [Next.js 16](https://nextjs.org) | React framework with App Router |
| [Shadcn/UI](https://ui.shadcn.com) | Component library |
| [Tailwind CSS](https://tailwindcss.com) | Utility-first CSS |
| [Lucide Icons](https://lucide.dev) | Icon library |
| [React Context](https://react.dev/reference/react/useContext) | State management |
| [SSE (EventSource)](https://developer.mozilla.org/en-US/docs/Web/API/EventSource) | Real-time streaming |

---

## License

MIT
