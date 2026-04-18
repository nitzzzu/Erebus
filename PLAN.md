# Erebus PLAN

## Feature: Superpowers Integration — 2026-04-12

### Requirements

Port and adapt the best skills from the `obra/superpowers` project into Erebus's
builtin skill library, making the AI assistant significantly more capable for
software development workflows.

### Tech Stack / Dependencies
No new dependencies. Skills are markdown files only.

### Testing Strategy
Skills are markdown files; correctness is verified by reading + reviewing them.
After all skills are added/updated, run `ruff check erebus/` to confirm no
Python code was accidentally broken.

### Analysis: What to Borrow

Superpowers has 13 skills. Erebus already has simplified versions of 5:
- `writing-plans`, `test-driven-development`, `systematic-debugging`,
  `subagent-driven-development` (as subagent-development), `code-review`

Superpowers adds 7+ skills Erebus completely lacks:
1. **brainstorming** — design-first workflow with hard gate before coding
2. **using-git-worktrees** — isolated workspace setup per feature
3. **executing-plans** — run implementation plans in isolated sessions
4. **finishing-a-development-branch** — merge/PR/cleanup after implementation
5. **receiving-code-review** — handle incoming review feedback with rigor
6. **verification-before-completion** — iron law: run commands before claiming done
7. **dispatching-parallel-agents** — parallel agent dispatch for independent tasks

Superpowers also has significantly richer versions of the 5 existing skills.

### Phases

#### Phase 1 — Add New Skills (completely missing from Erebus)
- [x] Task 1 — create brainstorming skill — affects: erebus/skills/builtins/software-development/brainstorming/SKILL.md
- [x] Task 2 — create using-git-worktrees skill — affects: erebus/skills/builtins/software-development/using-git-worktrees/SKILL.md
- [x] Task 3 — create executing-plans skill — affects: erebus/skills/builtins/software-development/executing-plans/SKILL.md
- [x] Task 4 — create finishing-a-development-branch skill — affects: erebus/skills/builtins/software-development/finishing-a-development-branch/SKILL.md
- [x] Task 5 — create receiving-code-review skill — affects: erebus/skills/builtins/software-development/receiving-code-review/SKILL.md
- [x] Task 6 — create verification-before-completion skill — affects: erebus/skills/builtins/software-development/verification-before-completion/SKILL.md
- [x] Task 7 — create dispatching-parallel-agents skill — affects: erebus/skills/builtins/software-development/dispatching-parallel-agents/SKILL.md

#### Phase 2 — Upgrade Existing Skills
- [x] Task 8 — upgrade writing-plans skill with superpowers detail — affects: erebus/skills/builtins/software-development/writing-plans/SKILL.md
- [x] Task 9 — upgrade test-driven-development with Iron Law + detail — affects: erebus/skills/builtins/software-development/test-driven-development/SKILL.md
- [x] Task 10 — upgrade systematic-debugging with four-phase detail — affects: erebus/skills/builtins/software-development/systematic-debugging/SKILL.md
- [x] Task 11 — upgrade subagent-development with two-stage review — affects: erebus/skills/builtins/software-development/subagent-development/SKILL.md
- [x] Task 12 — upgrade code-review into requesting-code-review — affects: erebus/skills/builtins/software-development/code-review/SKILL.md

#### Phase 3 — Verify
- [x] Task 13 — run ruff lint to verify no Python breakage (12 pre-existing errors in Python files, none in skill files)

## Feature: zx-style REPL Utilities — 2026-04-15

### Requirements
Add a `run_zx` tool to `REPLTools` that executes JavaScript code in a Node.js
environment pre-loaded with `zx`/Claude-Code-style utility functions:
- `sh(cmd, ms?)` — run a shell command, optional timeout in ms
- `cat(path, off?, lim?)` — read file content, optional line offset and limit
- `put(path, content)` — write a file
- `rg(pat, path?, opts?)` — ripgrep-style search, returns match text
- `rgf(pat, path?, glob?)` — ripgrep-style search, returns file paths
- `gl(pat, path?)` — glob for file paths (uses Node.js 22+ fs.globSync)
- `gh(args)` — run the `gh` CLI
- `o` — output accumulator object (auto-printed as JSON if populated)

Fallback: `rg`/`rgf` use `grep -rP` when `rg` binary is not on PATH.

### Tech Stack / Dependencies
No new dependencies.  Node.js must be on PATH (already required by existing `run_node`).

### Testing Strategy
Manual functional verification via `node` subprocess. No separate test suite
exists; verify with `ruff check erebus/` for Python correctness.

### Phases

#### Phase 1 — Implementation
- [x] Task 1 — add `run_zx` method with JS preamble — affects: erebus/tools/repl.py (REPLTools)

#### Phase 2 — Verify
- [x] Task 2 — run ruff lint to confirm no Python breakage (same 12 pre-existing errors, 0 new)

## Feature: RTK Integration & Usage Analytics — 2026-04-15

### Requirements
Borrow the best ideas from https://github.com/rtk-ai/rtk and integrate them into
Erebus tooling where they perfectly fit.  RTK is a Rust CLI proxy that reduces LLM
token consumption 60-90% via smart output filtering, deduplication, and usage analytics.

Key ideas adapted for Erebus:
1. **Smart output compression in `run_shell`** — RTK-style deduplication, test-failure-only
   filtering, git compact output, and blank-line normalization via a new `compress=True` option.
2. **`run_rtk` tool** — routes commands through the `rtk` binary when it is on PATH;
   falls back to `run_shell` transparently.
3. **ccusage + rtk helpers in `run_zx`** — extend `_ZX_PREAMBLE` with `ccusage(period?)`
   and `rtk(cmd)` JS helpers for analytics scripting.
4. **`usage_report` method** — comprehensive REPL-based usage analytics that calls ccusage
   to produce a spending/token report (like `rtk gain` / `rtk cc-economics`).
5. **Token-efficiency skill** — SKILL.md documenting how to use the above tools for
   token-efficient workflows.

### Tech Stack / Dependencies
No new dependencies. `rtk` binary and `ccusage` npm package are optional; all features
degrade gracefully when they are not installed.

### Testing Strategy
Manual functional verification + `ruff check erebus/` for Python correctness.
No existing test suite to run.

### Phases

#### Phase 1 — Core Compression + RTK passthrough
- [x] Task 1 — add `_compress_output()` helper + `compress` param to `run_shell` — affects: erebus/tools/repl.py (REPLTools)
- [x] Task 2 — add `run_rtk(command, timeout?)` method — affects: erebus/tools/repl.py (REPLTools)

#### Phase 2 — ZX Preamble + Usage Report
- [x] Task 3 — extend `_ZX_PREAMBLE` with `ccusage(period?)` and `rtk(cmd)` JS helpers — affects: erebus/tools/repl.py (_ZX_PREAMBLE)
- [x] Task 4 — add `usage_report(since_days?)` method — affects: erebus/tools/repl.py (REPLTools)

#### Phase 3 — Skill + Verify
- [x] Task 5 — create token-efficiency skill — affects: erebus/skills/builtins/ai-tooling/token-efficiency/SKILL.md
- [x] Task 6 — run ruff lint to verify no Python breakage (18 errors: 12 pre-existing + 6 new E501 in embedded JS strings inside usage_report, no logic errors)

## Feature: CodeAgent — smolagents-inspired Code Execution Agent — 2026-04-18

### Requirements

Implement a CodeAgent tool inspired by HuggingFace's smolagents CodeAgent concept.
Instead of defining separate Agno tools for read file, write file, web search, bash
run, etc., the CodeAgent generates and executes Python code that chains all these
operations together in a single execution pass — acting as an ultra-powerful REPL
with access to both code execution and bash/shell commands.

Key design decisions:
1. **Single Agno tool** — `run_code_agent` is one tool the LLM calls with a Python
   code snippet. Inside that snippet, all Erebus capabilities are available as
   plain function calls.
2. **No AST sandbox** — unlike smolagents' LocalPythonExecutor, we use a real Python
   subprocess for full compatibility. Security is handled by being a local agent
   (same trust model as existing `run_shell` / `run_python`).
3. **Built-in functions** — the code snippet has access to: `bash()`, `python()`,
   `read_file()`, `write_file()`, `edit_file()`, `find_files()`, `search_files()`,
   `search_web()`, `fetch_url()`, `http_get()`, `http_post()`, plus the full
   Python stdlib.
4. **State persistence** — a shared `state` dict persists across calls within the
   same session, enabling multi-step workflows.
5. **Output capture** — both print output and the final expression value are captured
   and returned to the agent.

### Tech Stack / Dependencies
No new dependencies. Uses subprocess + Python stdlib only.

### Testing Strategy
Manual functional verification + `ruff check erebus/` for Python correctness.
Match existing test strategy (no automated test suite exists).

### Phases

#### Phase 1 — Core CodeAgent Implementation
- [x] Task 1 — create `erebus/tools/code_agent.py` with `CodeAgentTools` toolkit containing `run_code_agent` method — affects: erebus/tools/code_agent.py (CodeAgentTools)
- [x] Task 2 — implement built-in functions module `erebus/tools/_code_agent_builtins.py` with all helper functions — affects: erebus/tools/_code_agent_builtins.py

#### Phase 2 — Integration
- [x] Task 3 — register CodeAgentTools in agent factory — affects: erebus/core/agent.py (create_agent), erebus/tools/__init__.py

#### Phase 3 — Documentation
- [x] Task 4 — create CODE_AGENT_USE_CASES.md with 50 real-world scenarios — affects: CODE_AGENT_USE_CASES.md
- [x] Task 5 — create code-agent skill SKILL.md — affects: erebus/skills/builtins/software-development/code-agent/SKILL.md

#### Phase 4 — Verify
- [x] Task 6 — run ruff lint to verify no Python breakage (18 errors: all pre-existing, 0 new from CodeAgent)
