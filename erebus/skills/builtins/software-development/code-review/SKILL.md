---
name: code-review
description: Use when completing tasks, implementing major features, or before merging — request a thorough review that checks spec compliance, code quality, security, and tests.
metadata:
  version: "2.0.0"
  author: erebus
  tags: ["software-development", "code-review", "quality", "security"]
---

# Requesting Code Review

Request a thorough code review to catch issues before they cascade.

**Core principle:** Review early, review often. Catch issues while they're cheap to fix.

## When to Request

**Mandatory:**
- After completing each task in subagent-driven development
- After completing a major feature
- Before merging to main/master

**Optional but valuable:**
- When stuck (fresh perspective helps)
- Before a large refactor (baseline check)
- After fixing a complex bug

## How to Request

**1. Get git SHAs:**

```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or: git rev-parse origin/main
HEAD_SHA=$(git rev-parse HEAD)
git log --oneline $BASE_SHA..$HEAD_SHA
```

**2. Provide to reviewer:**

- What was implemented (what does it do?)
- Plan or requirements it should meet
- Base SHA (starting commit)
- Head SHA (ending commit)
- Brief description

## Review Checklist

A thorough review covers all of these:

### Correctness
- Logic errors, off-by-one, null handling
- Edge cases and boundary conditions
- Error handling completeness
- Does behavior match requirements?

### Security
- Input validation and sanitization
- Authentication and authorization
- No secrets or credentials in code
- Injection vulnerabilities

### Code Quality
- Naming clarity and readability
- DRY principle — no unnecessary duplication
- Function length and complexity
- Code that's easy to change

### Testing
- Test coverage for new/changed code
- Tests verify behavior (not just implementation)
- Edge cases tested
- No tests deleted to make suite pass

### Performance
- Algorithm complexity appropriate for data size
- Database query efficiency
- Memory usage patterns

### Documentation
- Complex logic commented
- Public APIs documented
- README updated if behavior changed

## Acting on Feedback

**Severity levels:**

| Level | Action |
|-------|--------|
| **Critical** | Fix immediately before proceeding |
| **Important** | Fix before moving to next task |
| **Minor** | Note for later; don't block progress |

**If reviewer is wrong:**
- Push back with technical reasoning
- Reference working tests or code
- Ask for clarification

**If you agree with feedback:**
- Fix it and show the diff — no need to thank the reviewer
- Test each fix individually before the next

## Integration

**Part of subagent-driven development:** Review after EACH task — catch issues before they compound.

**Standalone use:** Review before merging — ensure the full feature meets requirements.

**After review:** Use **receiving-code-review** skill to handle feedback properly.

## Example Request

```
Reviewing Task 3: Add user authentication middleware

What was implemented:
  JWT validation middleware, token refresh logic, and associated tests

Requirements:
  Task 3 from docs/plans/auth-feature-plan.md

BASE_SHA: a7981ec
HEAD_SHA: 3df7661

Description:
  Added JWTMiddleware class with validate(), refresh(), and revoke() methods.
  4 unit tests, 1 integration test covering happy path and token expiry.
```
