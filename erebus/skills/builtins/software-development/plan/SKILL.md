---
name: plan
description: Plan mode for writing structured markdown implementation plans without executing code.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["software-development", "planning", "architecture"]
---

# Plan Mode

Use this skill to create structured implementation plans before coding.

## When to Use

- User says "plan", "create a plan", or "think about how to"
- Before starting a complex implementation
- When the user wants to review the approach before execution
- For architecture and design decisions

## Plan Format

```markdown
# Implementation Plan: [Title]

## Goal
[One-sentence description of what we're building]

## Tasks

- [ ] Task 1: [Description]
  - Files: `path/to/file.py`
  - Changes: [What changes]
- [ ] Task 2: [Description]
  - Files: `path/to/other.py`
  - Changes: [What changes]

## Risks
- [Potential issues and mitigations]

## Testing Strategy
- [How to verify the implementation]
```

## Process

1. **Analyze**: Understand the full scope of what's needed
2. **Decompose**: Break into atomic tasks (2-5 min each)
3. **Order**: Arrange tasks in dependency order
4. **Document**: Write the plan with exact file paths
5. **Review**: Present the plan for user approval
