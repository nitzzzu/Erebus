---
name: finishing-a-development-branch
description: Use when implementation is complete and all tests pass — guides completion of development work by verifying tests and presenting structured options for merge, PR, or cleanup.
metadata:
  version: "2.0.0"
  author: erebus
  tags: ["software-development", "git", "workflow", "merge", "pr"]
---

# Finishing a Development Branch

Guide completion of development work by verifying tests, then presenting clear
options for integrating or discarding the work.

**Core principle:** Verify tests → Present options → Execute choice → Clean up.

## Step 1: Verify Tests

Before presenting any options, run the project's test suite:

```bash
pytest / npm test / cargo test / go test ./...
```

**If tests fail:**

```
Tests failing (<N> failures). Must fix before completing:

[Show failures]

Cannot proceed with merge/PR until tests pass.
```

Stop. Do not proceed to Step 2 until tests pass.

## Step 2: Determine Base Branch

```bash
git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null
git log --oneline -5  # show recent commits
```

## Step 3: Present Options

Present exactly these 4 options:

```
Implementation complete. What would you like to do?

1. Merge back to <base-branch> locally
2. Push and create a Pull Request
3. Keep the branch as-is (I'll handle it later)
4. Discard this work

Which option?
```

Do not add extra explanation — keep options concise.

## Step 4: Execute Choice

### Option 1: Merge Locally

```bash
git checkout <base-branch>
git pull
git merge <feature-branch>
# Verify tests on merged result
<test command>
# If tests pass:
git branch -d <feature-branch>
```

Then: Cleanup worktree (Step 5).

### Option 2: Push and Create PR

```bash
git push -u origin <feature-branch>
gh pr create --title "<title>" --body "## Summary
- <bullet 1>
- <bullet 2>

## Test Plan
- [ ] <verification step>"
```

Then: Cleanup worktree (Step 5).

### Option 3: Keep As-Is

Report: "Keeping branch `<name>`. Worktree preserved at `<path>`."

Do NOT cleanup worktree.

### Option 4: Discard

**Confirm first:**

```
This will permanently delete:
- Branch: <name>
- All commits: <commit-list>
- Worktree at: <path>

Type 'discard' to confirm.
```

Wait for exact word "discard". If confirmed:

```bash
git checkout <base-branch>
git branch -D <feature-branch>
```

Then: Cleanup worktree (Step 5).

## Step 5: Cleanup Worktree

For Options 1, 2, and 4 (NOT Option 3):

```bash
git worktree list | grep $(git branch --show-current)
git worktree remove <worktree-path>
```

## Quick Reference

| Option | Merge | Push | Keep Worktree | Delete Branch |
|--------|-------|------|---------------|---------------|
| 1. Merge locally | ✓ | — | — | ✓ |
| 2. Create PR | — | ✓ | ✓ | — |
| 3. Keep as-is | — | — | ✓ | — |
| 4. Discard | — | — | — | ✓ (force) |

## Common Mistakes

- **Skipping test verification** — never present options until tests pass
- **Automatic worktree cleanup on Option 2/3** — keep it for Option 2 and 3
- **No confirmation for discard** — always require typed "discard" confirmation
- **Merging without verifying tests on merge result** — always re-verify after merge

## Rules

**Never:**
- Proceed with failing tests
- Delete work without typed confirmation
- Force-push without explicit request

**Always:**
- Verify tests before offering options
- Present exactly 4 options
- Re-verify tests after merge (Option 1)
