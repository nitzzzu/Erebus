---
name: claude-code
description: Delegate coding tasks to Claude Code agent for refactoring, implementation, PR reviews, and complex operations.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["autonomous-agents", "claude", "coding", "delegation"]
---

# Claude Code Agent Delegation

Use this skill to delegate coding tasks to the Claude Code CLI agent.

## When to Use

- User needs complex refactoring across many files
- User wants an independent code review
- User needs implementation of a well-defined feature
- Tasks that benefit from a fresh context

## Usage

```bash
# One-shot task
claude -p "Refactor the authentication module to use JWT tokens"

# Interactive session
claude

# With specific model
claude --model claude-sonnet-4-20250514 -p "Fix the failing tests"
```

## Delegation Patterns

### Feature Implementation
```bash
claude -p "Implement user registration: create User model, API endpoint, and tests"
```

### Code Review
```bash
git diff main | claude -p "Review this diff for bugs, security issues, and code quality"
```

### Parallel Work
```bash
# Use git worktrees for parallel tasks
git worktree add ../feature-a feature-a
cd ../feature-a && claude -p "Implement feature A"
```

## Process

1. **Define Task**: Write a clear, self-contained task description
2. **Set Context**: Provide file paths and requirements
3. **Delegate**: Run claude with the task
4. **Review**: Check the output before accepting
5. **Integrate**: Merge the changes if approved
