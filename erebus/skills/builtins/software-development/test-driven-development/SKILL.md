---
name: test-driven-development
description: RED-GREEN-REFACTOR cycle — write a failing test first, implement minimal code, then refactor.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["software-development", "tdd", "testing"]
---

# Test-Driven Development

Use this skill to implement features using the TDD cycle.

## When to Use

- User wants to build a feature with tests first
- User asks for test-driven development
- Building a new module, function, or component
- When code correctness is critical

## The Cycle

### 🔴 RED — Write a Failing Test
```
1. Write the smallest test that specifies desired behavior
2. Run it — it MUST fail
3. Verify it fails for the right reason
```

### 🟢 GREEN — Make It Pass
```
1. Write the MINIMUM code to make the test pass
2. No more, no less
3. It's okay if the code is ugly
```

### 🔵 REFACTOR — Clean Up
```
1. Improve the code structure
2. Remove duplication
3. Run tests again — they must still pass
```

## Rules

- Never write production code without a failing test
- Write only enough test to fail
- Write only enough code to pass
- Refactor in small steps, running tests after each

## Process

1. **Understand**: What behavior do we need?
2. **Test**: Write the test first (RED)
3. **Implement**: Minimal code to pass (GREEN)
4. **Clean**: Refactor while tests stay green (REFACTOR)
5. **Repeat**: Next test case
