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
