---
name: using-git-worktrees
description: Use when starting feature work that needs isolation from the current workspace, or before executing implementation plans — creates isolated git worktrees with safety verification.
metadata:
  version: "2.0.0"
  author: erebus
  tags: ["software-development", "git", "workflow", "isolation"]
---

# Using Git Worktrees

Git worktrees create isolated workspaces sharing the same repository, allowing
parallel work on multiple branches without context switching.

**Core principle:** Systematic directory selection + safety verification = reliable isolation.

## When to Use

- Starting a new feature that should not pollute the current workspace
- Before executing an implementation plan (required before writing-plans output)
- Working on a bug fix in parallel with other work
- Any time you need a clean baseline environment

## Directory Selection Process

Follow this priority order:

### 1. Check Existing Directories

```bash
ls -d .worktrees 2>/dev/null    # Preferred (hidden)
ls -d worktrees  2>/dev/null    # Alternative
```

If found: use that directory. If both exist, `.worktrees` wins.

### 2. Check Project Config

```bash
grep -i "worktree.*director" CLAUDE.md 2>/dev/null
grep -i "worktree.*director" .erebus.toml 2>/dev/null
```

If a preference is specified: use it without asking.

### 3. Ask User

If no directory exists and no config preference:

```
No worktree directory found. Where should I create worktrees?

1. .worktrees/ (project-local, hidden)
2. ~/.config/erebus/worktrees/<project-name>/ (global location)

Which would you prefer?
```

## Safety Verification

### For Project-Local Directories

MUST verify the directory is ignored before creating a worktree:

```bash
git check-ignore -q .worktrees 2>/dev/null || echo "NOT IGNORED"
```

If NOT ignored: add to `.gitignore` and commit that change first.

Why critical: prevents accidentally committing worktree contents to the repository.

### For Global Directory

No `.gitignore` verification needed — outside project entirely.

## Creation Steps

```bash
# 1. Detect project name
project=$(basename "$(git rev-parse --show-toplevel)")

# 2. Create worktree on new branch
git worktree add .worktrees/<branch-name> -b <branch-name>
cd .worktrees/<branch-name>

# 3. Run project setup (auto-detect)
[ -f package.json ]      && npm install
[ -f requirements.txt ]  && pip install -r requirements.txt
[ -f pyproject.toml ]    && pip install -e ".[all]" 2>/dev/null || pip install -e .
[ -f Cargo.toml ]        && cargo build
[ -f go.mod ]            && go mod download

# 4. Verify clean baseline (run existing tests)
# Use the project's test command
```

## Baseline Verification

Run the project's test suite before starting:

```bash
pytest / npm test / cargo test / go test ./...
```

**If tests fail:** Report failures and ask whether to proceed or investigate first.
**If tests pass:** Report ready.

### Report Format

```
Worktree ready at <full-path>
Branch: <branch-name>
Tests passing (<N> tests, 0 failures)
Ready to implement <feature-name>
```

## Quick Reference

| Situation | Action |
|-----------|--------|
| `.worktrees/` exists | Use it (verify ignored) |
| `worktrees/` exists | Use it (verify ignored) |
| Both exist | Use `.worktrees/` |
| Neither exists | Check config → ask user |
| Directory not ignored | Add to .gitignore + commit first |
| Tests fail at baseline | Report + ask before proceeding |

## Common Mistakes

**Skipping ignore verification** — worktree contents get tracked, pollute git status.

**Proceeding with failing baseline tests** — you can't distinguish new bugs from pre-existing ones.

**Hardcoding setup commands** — always auto-detect from project files.

## Cleanup

When work is complete (handled by finishing-a-development-branch skill):

```bash
git worktree remove .worktrees/<branch-name>
```
