---
name: subagent-development
description: Execute implementation plans via fresh subagents per task with two-stage review for quality assurance.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["software-development", "subagents", "implementation", "automation"]
---

# Subagent-Driven Development

Use this skill to execute complex implementations by delegating tasks to focused subagents.

## When to Use

- Large implementation with many independent tasks
- Need isolated contexts for different parts of the work
- Want to parallelize development tasks
- Need independent review of each component

## Architecture

```
Orchestrator Agent
├── Task 1 → Subagent A → Review → Merge
├── Task 2 → Subagent B → Review → Merge
└── Task 3 → Subagent C → Review → Merge
```

## Two-Stage Review

### Stage 1: Spec Compliance
- Does the implementation match the task specification?
- Are all requirements addressed?
- Is the interface correct?

### Stage 2: Code Quality
- Is the code clean and maintainable?
- Are there tests?
- Performance considerations?

## Process

1. **Plan**: Break work into independent, atomic tasks
2. **Delegate**: Assign each task to a fresh subagent
3. **Review Stage 1**: Verify spec compliance
4. **Review Stage 2**: Check code quality
5. **Integrate**: Merge approved changes
6. **Verify**: Run full test suite after integration
