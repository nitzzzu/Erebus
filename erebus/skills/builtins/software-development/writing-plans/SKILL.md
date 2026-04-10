---
name: writing-plans
description: Write comprehensive implementation plans with bite-sized tasks, exact file paths, and complete code examples.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["software-development", "planning", "documentation"]
---

# Writing Implementation Plans

Use this skill when you need to write detailed implementation plans.

## When to Use

- Before starting a multi-file implementation
- When the user wants a detailed roadmap
- For architecture documentation
- When planning a refactoring

## Plan Template

```markdown
# Plan: [Feature Name]

## Overview
[2-3 sentences describing what we're building and why]

## Prerequisites
- [Required tools, packages, configurations]

## Tasks

### Task 1: [Title] (estimated: 2-5 min)
**Files**: `path/to/file.py`
**What**: [Clear description of changes]
**Why**: [Rationale]

### Task 2: [Title] (estimated: 2-5 min)
...

## Testing
- [ ] Unit tests for [component]
- [ ] Integration test for [flow]
- [ ] Manual verification: [steps]

## Risks
| Risk | Mitigation |
|------|------------|
| [What could go wrong] | [How to prevent/handle] |
```

## Rules

- Each task should take 2-5 minutes
- Include exact file paths and function names
- Tasks should be independently verifiable
- Order tasks by dependency (no forward references)
