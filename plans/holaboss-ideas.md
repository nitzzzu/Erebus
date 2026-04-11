# Ideas from Holaboss for Erebus

> Analysis date: 2026-04-11  
> Source repo: https://github.com/holaboss-ai/holaboss-ai  
> Erebus repo: https://github.com/nitzzzu/Erebus

---

## TL;DR

Holaboss is a workspace-centric, long-horizon agent desktop built in TypeScript/Electron.
Erebus is a Python + Next.js agent with great tooling but a run-centric design.
The gap is almost entirely about **continuity, memory structure, and workspace depth**.
Most ideas below require touching at most 2-3 files and plug directly into existing
Erebus patterns — no re-architecture needed.

---

## Side-by-Side Comparison

| Concern | Erebus today | Holaboss approach |
|---|---|---|
| Workspace policy | Global AGENTS.md / SOUL.md injected at agent start | Per-workspace `AGENTS.md` + separate `workspace.yaml` runtime plan |
| Per-workspace skills | Global builtins + user-skills only | `skills/` directory inside each workspace root |
| Memory model | Flat Agno MemoryManager rows in SQLite | Typed memories: `preference`, `identity`, `fact`, `procedure`, `blocker`, `reference` |
| Session continuity | `num_history_runs=10`, history replayed | Compact `session-memory` snapshot restored on next run |
| History growth control | Fixed 10-run window (context keeps growing) | Stable/volatile prompt sections + compaction boundaries |
| Workspace portability | No export | Zip export omitting state, .env, build artifacts |
| Workspace templates | No template concept | Scaffold from local dir or GitHub template |
| Tool visibility per run | All tools always loaded | Capability manifest decided per run from workspace config |
| Git checkpointing | None | Each workspace is its own git repo |
| Turn result records | Agno session storage only | Explicit `turn_results` rows: token usage, stop reason, fingerprint |

---

## Tier 1 — Quick Wins (1–2 files, low risk)

These are nearly zero-effort and plug directly into existing hooks.

### 1. Per-Workspace `AGENTS.md` and `WORKSPACE.md`

**What Holaboss does:** Each workspace contains `AGENTS.md` (human instructions) and
`workspace.yaml` (machine-readable runtime plan). These are loaded instead of — or in
addition to — the global config.

**Erebus fit:** `erebus/core/agent.py:_load_context_files()` already loads
`~/.erebus/AGENTS.md` and cwd `AGENTS.md`. One-liner: also load
`<effective_workspace>/AGENTS.md` and `<effective_workspace>/WORKSPACE.md` (a
free-form markdown brief the user writes about the workspace goal).

**Files to change:**
- `erebus/core/agent.py` — extend `_load_context_files()` to accept workspace path
  and read those two files from it.

**Effort:** ~10 lines.

---

### 2. Per-Workspace Skill Auto-Discovery

**What Holaboss does:** Each workspace can have a `skills/` subdirectory with its own
`SKILL.md` files that are only active for that workspace.

**Erebus fit:** `erebus/core/agent.py:_build_skills()` already iterates a list of
`skill_dirs`. Add `<effective_workspace>/skills/` to that list whenever a workspace is
active. Skills from there are only loaded in sessions rooted to that workspace.

**Files to change:**
- `erebus/core/agent.py` — pass `workspace_path` into `_build_skills()` and append it.

**Effort:** ~5 lines.

---

### 3. Workspace Git Auto-Init

**What Holaboss does:** Every workspace is initialized as a git repository so the agent's
file changes become checkpointed commits, enabling rollback and audit.

**Erebus fit:** `erebus/workspace/manager.py:WorkspaceManager.create()` already has the
workspace path at creation time. Run `git init` (subprocess) there. Subsequent agent
ShellTools operations inside the workspace will naturally be in a git tree.

**Files to change:**
- `erebus/workspace/manager.py` — add optional `git_init: bool = True` param and call
  `subprocess.run(["git", "init", str(resolved)])` on create.

**Effort:** ~10 lines.

---

### 4. Typed Memory Categories

**What Holaboss does:** Memory is stored with an explicit type tag:
- `preference` — stable user preferences (e.g. "prefer dark mode", "reply in Spanish")
- `identity` — stable user context (name, role, company)
- `fact` — workspace-sensitive knowledge (captured during a run)
- `procedure` — reusable how-to (e.g. "deploy with `make deploy`")
- `blocker` — known obstacles the agent hit (e.g. "API key expires monthly")
- `reference` — time-sensitive info, needs reconfirmation before acting

**Erebus fit:** Agno's MemoryManager stores rows with `memory` + `topics`. Topics are
already a list field. The simplest approach is to prefix the memory string with the type
(e.g. `[procedure] Deploy with \`make deploy\``) or add `type` to the `topics` list.
A cleaner approach is a thin wrapper that serializes type into the `topics` array so no
DB schema change is needed.

Surface in the UI: the memory page at `web/src/app/memory/` can render each type with a
distinct icon/badge — no API changes needed if type is in topics.

**Files to change:**
- `erebus/memory/manager.py` — add `create_memory(content, type, user_id)` helper that
  encodes type in topics.
- `erebus/api/server.py` — add optional `type` query param to `GET /api/memory` for
  filtered retrieval.
- `web/src/app/memory/` — render type badges in the memory list.

**Effort:** ~40 lines Python + ~20 lines TSX.

---

## Tier 2 — Moderate Work (2–4 files, meaningful impact)

### 5. Session-Memory Snapshot (Continuity Without Growing Context)

**What Holaboss does:** After every run, the runtime writes a compact markdown summary
to `memory/workspace/<id>/runtime/session-memory/latest.md`. The next run restores from
this snapshot instead of replaying the full transcript. This keeps token cost bounded.

**Erebus fit:** Today Erebus uses `add_history_to_context=True` with `num_history_runs=10`.
When that window fills up, old context is simply dropped. Instead, we can write a compact
session summary to `<workspace>/.erebus/session-memory/latest.md` at the end of each
session, and inject it at the top of the next session's instructions.

**Files to change:**
- `erebus/core/agent.py` — add `session_summary_path` injection into instructions when
  the file exists.
- `erebus/api/server.py` — after a chat `run_response` completes, call a new
  `write_session_summary()` helper.
- New `erebus/memory/session_summary.py` — generate compact summary from last N tool
  calls + assistant turn and write to `<workspace>/.erebus/session-memory/latest.md`.

**Why it matters:** Without this, every 10th message "resets" the agent's working memory.
With it, the agent picks up right where it left off across any number of messages.

**Effort:** ~100 lines Python.

---

### 6. Workspace Templates

**What Holaboss does:** New workspaces can be created from a local template folder or a
marketplace template. The template is scaffolded into the new workspace directory,
creating `AGENTS.md`, `workspace.yaml`, a `skills/` subdirectory, etc.

**Erebus fit:** Erebus already has `WorkspaceManager.create()`. Add a `template` param
that accepts either:
- A built-in template name (maps to `erebus/workspace/templates/<name>/`)
- A GitHub repo URL (clones into temp, copies non-git contents)

Ship a few starter templates:
- `blank` — empty workspace with minimal AGENTS.md scaffold
- `coding` — AGENTS.md tuned for software dev, `skills/coding/` pre-populated
- `research` — AGENTS.md tuned for research, `skills/research/` pre-populated
- `devops` — AGENTS.md tuned for DevOps, relevant skills

**Files to change:**
- `erebus/workspace/manager.py` — add `template` param + scaffolding logic.
- `erebus/workspace/templates/` — new directory with 3-4 template subdirectories.
- `erebus/api/server.py` — pass `template` from `POST /api/workspaces` body.
- `web/src/app/` — workspace creation dialog adds template picker dropdown.

**Effort:** ~150 lines Python + ~60 lines TSX.

---

### 7. Workspace Export / Packaging

**What Holaboss does:** Workspaces can be exported as a portable zip that includes
authored files (AGENTS.md, skills/, apps/) but omits runtime state, .holaboss/, .env*,
node_modules, logs, and database files. The zip can be shared and imported elsewhere.

**Erebus fit:** Straightforward streaming zip endpoint. The exclusion list is:
`.git/`, `node_modules/`, `__pycache__/`, `.env*`, `*.db`, `*.sqlite`, `.erebus/`,
`*.log`.

**Files to change:**
- `erebus/api/server.py` — add `GET /api/workspaces/{name}/export` that streams a zip.
- `web/src/app/` — add "Export" button to workspace settings or the workspaces list page.

**Effort:** ~60 lines Python + ~20 lines TSX.

---

### 8. Workspace-Local `workspace.yaml` / Config Override

**What Holaboss does:** `workspace.yaml` is a machine-readable runtime plan living at
the workspace root. It declares skills, apps, model preference, tool visibility, and
links to `AGENTS.md`. The runtime _compiler_ reads it before each run.

**Erebus fit:** A simpler version: when a workspace has an `erebus.toml` (or
`workspace.yaml`) in its root, merge it with the global config — letting the workspace
override default model, enabled tools, extra skill dirs, and extra MCP servers. This lets
you create, e.g., a "research" workspace that always uses a cheaper model and only has
web search tools enabled.

**Files to change:**
- `erebus/agent_config.py` — add `load_workspace_config(workspace_path)` that reads
  `<workspace>/erebus.toml` and deep-merges into the global config.
- `erebus/core/agent.py:create_agent()` — call `load_workspace_config` when
  `effective_workspace` is set, use results to override model/tool selections.

**Effort:** ~80 lines Python.

---

## Tier 3 — Bigger / Higher Impact

These are worth doing but require more thought and testing.

### 9. Prompt Section Layering (Stable vs Volatile)

**What Holaboss does:** The system prompt is split into named sections with explicit
precedence: `runtime_core → execution_policy → session_policy → capability_policy →
workspace_policy → harness_quirks → recent_runtime_context`. Stable sections (soul,
workspace instructions) are hashed and can be cached at the model provider level.
Volatile sections (session memory, recent context) change every run.

**Erebus fit:** `create_agent()` currently concatenates soul + config + context + workspace
into one big `instructions` string. Refactor to a list of `PromptSection(id, content,
volatile: bool)` objects that get assembled in order. Two immediate benefits:
1. With Anthropic/OpenAI prompt caching enabled, stable sections don't count toward
   repeated token cost.
2. Easier to understand what's in the prompt for debugging.

**Files to change:**
- `erebus/core/agent.py` — internal refactor of instructions assembly.
- `erebus/core/prompt_sections.py` — new dataclass + assembly helper.

**Effort:** ~150 lines Python, no external API changes.

---

### 10. Bounded History + Auto-Compaction

**What Holaboss does:** When a session grows long, the runtime writes a compaction
boundary: a durable artifact containing a compact summary of prior turns, preserved turn
IDs, and a restoration order. The next run restores from the boundary instead of
replaying history.

**Erebus fit:** Simpler version — when the agent exceeds `num_history_runs` threshold, a
background task generates a bullet-point summary of the last N turns (via a fast model
call) and writes it to `session-memory/latest.md`. The agent's next invocation loads this
as context instead of the full history. This is a complement to idea #5 and makes long
conversations truly seamless.

**Files to change:**
- `erebus/memory/session_summary.py` — extend with compaction logic.
- `erebus/core/agent.py` — trigger compaction check on session start.
- `erebus/api/server.py` — expose `GET /api/sessions/{id}/summary` endpoint.

**Effort:** ~200 lines Python.

---

## What Does NOT Make Sense for Erebus

| Holaboss concept | Why skip it |
|---|---|
| Electron desktop app | Erebus is web-first + headless; completely different product direction |
| Full harness abstraction | Complexity for complexity's sake; Agno already handles model routing |
| Request snapshot fingerprinting | Very low ROI for a single-user / self-hosted agent |
| `prompt_cache_profile` with explicit fingerprints | Only matters at high request volume; provider caching works at header level already |
| Multi-tenant workspace isolation | Holaboss is a multi-user product; Erebus is personal-use |
| Marketplace / cloud sync | Holaboss has a hosted backend; Erebus is fully local |

---

## Recommended Implementation Order

| Priority | Idea | Files touched | Effort |
|---|---|---|---|
| 1 | Per-workspace `AGENTS.md` + `WORKSPACE.md` loading | `core/agent.py` | XS |
| 2 | Per-workspace `skills/` auto-discovery | `core/agent.py` | XS |
| 3 | Workspace git auto-init | `workspace/manager.py` | XS |
| 4 | Typed memory categories | `memory/manager.py`, `api/server.py`, UI | S |
| 5 | Workspace templates | `workspace/manager.py`, `api/server.py`, UI | M |
| 6 | Session-memory snapshot | `memory/session_summary.py`, `api/server.py`, `core/agent.py` | M |
| 7 | Workspace export / packaging | `api/server.py`, UI | M |
| 8 | Workspace-local config override | `agent_config.py`, `core/agent.py` | M |
| 9 | Prompt section layering | `core/agent.py`, new `core/prompt_sections.py` | L |
| 10 | Bounded history + auto-compaction | `memory/session_summary.py`, `core/agent.py` | L |

---

## Notes

- Ideas 1–3 can ship in a single PR touching only `erebus/core/agent.py` and
  `erebus/workspace/manager.py`.
- Ideas 5 and 10 are tightly related — session-memory snapshot is the prerequisite for
  a full compaction strategy.
- Typed memory (idea 4) has the highest user-visible impact for the lowest risk.
- Workspace templates (idea 5 in tier 2) would make Erebus feel like a product rather
  than a power-user tool.
