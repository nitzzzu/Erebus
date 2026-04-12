---
name: subagent-development
description: Use when executing implementation plans with independent tasks — dispatch fresh subagent per task with two-stage review (spec compliance, then code quality) for high quality, fast iteration.
metadata:
  version: "2.0.0"
  author: erebus
  tags: ["software-development", "subagents", "implementation", "automation"]
---

# Subagent-Driven Development

Execute a plan by dispatching a fresh subagent per task, with two-stage review after each.

**Why subagents:** Fresh context per task = no context pollution. Precise instructions = focused success.
Each subagent gets exactly what it needs — not your full session history.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration.

## When to Use vs. Executing Plans

**Use subagent-development when:**
- Tasks are mostly independent
- Subagent support is available
- You want isolated context per task

**Use executing-plans instead when:**
- No subagent support available
- Tasks are tightly coupled (must share state)
- Sequential execution is required

## Architecture

```
Orchestrator (you)
├── Task 1 → Implementer subagent → Spec reviewer → Quality reviewer → ✓ merge
├── Task 2 → Implementer subagent → Spec reviewer → Quality reviewer → ✓ merge
└── Task 3 → Implementer subagent → Spec reviewer → Quality reviewer → ✓ merge
```

## The Process

### Setup

1. Read the complete plan file
2. Extract all tasks with their full text
3. Note shared context (repo structure, tech stack, conventions)
4. Create task list with status tracking

### Per-Task Loop

For each task:

**1. Dispatch implementer subagent**

Give it:
- The COMPLETE task text from the plan (not a summary)
- Shared context (repo layout, test command, conventions)
- Clear "done" criteria
- Constraint: run tests, commit, self-review before returning

**2. Handle questions**

If the implementer asks questions: answer them, then re-dispatch.

**3. Two-Stage Review**

After implementer completes:

**Stage 1 — Spec Compliance Review**

Dispatch spec-reviewer subagent with:
- The original task spec
- The git diff of what was implemented
- Question: "Does the implementation match the spec? What's missing or wrong?"

If gaps found: send back to implementer to fix. Re-review.

**Stage 2 — Code Quality Review**

Dispatch code-quality-reviewer subagent with:
- The git diff
- Question: "Is this code clean, tested, and maintainable? Any issues?"

If issues found: send back to implementer to fix. Re-review.

**4. Mark task complete**

Only after both reviews pass.

### After All Tasks

1. Run the full test suite one final time
2. Dispatch a final overall code reviewer for the complete implementation
3. Use **finishing-a-development-branch** skill to complete the work

## Two-Stage Review Detail

### Stage 1: Spec Compliance

Check:
- Does the implementation address all requirements in the task?
- Are all specified files created/modified?
- Does the interface match what the spec described?
- Are there missing pieces?

### Stage 2: Code Quality

Check:
- Is the code clean and readable?
- Are there tests? Do they test behavior (not just coverage)?
- Any obvious performance issues?
- Naming, duplication, complexity?

## Rules

- Fresh subagent per task — never reuse a subagent across tasks
- Do NOT pass your full session history to subagents
- Both review stages are mandatory — never skip either
- Fix issues before marking a task complete
- If implementer is stuck after 2 attempts: escalate to you (the orchestrator) to unblock

## Common Mistakes

**Passing full session context** — subagents need focused context, not everything you know.

**Skipping review stages** — "it looks fine" is not a review. Both stages required.

**Moving on with open issues** — fix Critical and Important issues before the next task.

**Summarizing the task instead of quoting it** — give the implementer the exact task text.
