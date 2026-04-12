---
name: executing-plans
description: Use when you have a written implementation plan to execute, especially in a separate session or when subagents are unavailable — load plan, review critically, execute all tasks, verify at checkpoints.
metadata:
  version: "2.0.0"
  author: erebus
  tags: ["software-development", "implementation", "planning", "execution"]
---

# Executing Plans

Load a plan, review it critically, execute all tasks in order, and verify at each checkpoint.

**When to use this vs. subagent-development:**
- No subagent support available → use this skill
- Tasks are tightly coupled (shared state) → use this skill
- Tasks are independent and subagents available → use subagent-development instead

## The Process

### Step 1: Load and Review Plan

1. Read the plan file completely
2. Review critically — identify questions or concerns
3. If concerns exist: raise them with the user before starting
4. Create a task list (TodoWrite or equivalent) tracking each task's status

### Step 2: Set Up Workspace

Before executing any code:
```bash
# Never implement on main/master without explicit user consent
git status  # confirm you're on the right branch
```

If starting fresh, use the **using-git-worktrees** skill first.

### Step 3: Execute Tasks

For each task in order:

1. Mark as `in_progress`
2. Follow each step exactly as written — the plan has bite-sized steps
3. Run verifications as specified in the plan
4. Mark as `completed` only after verification passes

### Step 4: Checkpoints (Every 3 Tasks)

After every 3 completed tasks:
1. Run the full test suite
2. Report status to user: `Completed tasks 1-3. Tests: X passing, 0 failing. Continuing...`
3. Proceed unless user intervenes

### Step 5: Complete Development

When all tasks are complete:
- Announce: "All tasks complete. Moving to branch completion."
- Use the **finishing-a-development-branch** skill

## When to Stop and Ask

**STOP executing immediately when:**
- A blocker is encountered (missing dependency, repeated test failure, unclear instruction)
- The plan has a critical gap that prevents starting the next task
- You don't understand an instruction (never guess)
- Verification fails and you don't know why

**Ask for clarification rather than guessing.**

## Revisiting Steps

**Return to Step 1 (Review) when:**
- User updates the plan based on your feedback
- The fundamental approach needs rethinking

**Do NOT force through blockers** — stop and ask.

## Rules

- Follow plan steps exactly — no improvising
- Never skip verifications
- Never start implementation on main/master without explicit consent
- Stop when blocked; don't guess and proceed
- One change at a time — don't combine multiple tasks

## Integration

**Requires:**
- A written plan (from **writing-plans** skill)
- Clean workspace (ideally from **using-git-worktrees** skill)

**After completion:** Use **finishing-a-development-branch** skill
