---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes — four-phase root cause investigation: find cause, find pattern, form hypothesis, implement fix.
metadata:
  version: "2.0.0"
  author: erebus
  tags: ["software-development", "debugging", "troubleshooting"]
---

# Systematic Debugging

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting any fix. Symptom fixes are failure.

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes that didn't work
- You don't fully understand the issue yet

**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)

## Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

### 1. Read Error Messages Carefully

- Don't skip past errors or warnings
- They often contain the exact solution
- Read stack traces completely — top to bottom
- Note line numbers, file paths, error codes

### 2. Reproduce Consistently

- Can you trigger it reliably?
- What are the exact steps?
- Does it happen every time?
- If NOT reproducible → gather more data, don't guess

### 3. Check Recent Changes

- What changed that could cause this?
- `git diff`, `git log --oneline -10`
- New dependencies, config changes
- Environmental differences

### 4. Gather Evidence in Multi-Component Systems

When the system has multiple components (API → service → database, CI → build → deploy):

**BEFORE proposing fixes, add diagnostic instrumentation:**

```bash
# Layer 1: Entry point
echo "=== Input at layer 1: $INPUT"

# Layer 2: Processing
echo "=== State after layer 2: $STATE"

# Layer 3: Output
echo "=== Result at layer 3: $RESULT"
```

Run once to gather evidence showing WHERE it breaks.
Then analyze evidence to identify the failing component.
Then investigate THAT specific component.

### 5. Trace Data Flow

When the error is deep in a call stack:
- Where does the bad value originate?
- What called this with the bad value?
- Trace UP the call stack until you find the source
- Fix at the source, not at the symptom

## Phase 2: Pattern Analysis

**Find the pattern before fixing:**

1. **Find working examples** — locate similar working code in the same codebase
2. **Compare against references** — if implementing a pattern, read the reference implementation completely
3. **Identify differences** — what's different between working and broken? List every difference.
4. **Understand dependencies** — what does this code assume about its environment?

## Phase 3: Hypothesis and Testing

**Scientific method:**

1. **Form one hypothesis** — "I think X is the root cause because Y" — write it down
2. **Test minimally** — make the SMALLEST possible change to test the hypothesis
3. **One variable at a time** — don't combine multiple fixes
4. **Verify before continuing** — did it work?
   - Yes → Phase 4
   - No → form NEW hypothesis, return to Phase 1 with new information

**When you don't know:** Say "I don't understand X" — don't pretend to know.

## Phase 4: Implementation — Fix the Root Cause

**Fix the root cause, not the symptom:**

1. **Create failing test case** — simplest possible reproduction as an automated test
2. **Use TDD** — apply the test-driven-development skill to write the fix
3. **Verify fix** — run the test, watch it turn green
4. **Check for similar bugs** — search codebase for the same pattern elsewhere
5. **Document** — if the bug reveals a non-obvious invariant, add a comment

## Rules

- **Never fix before understanding** — complete Phases 1-3 before writing any fix
- **One change at a time** — don't combine multiple fixes
- **Always add a regression test** — every bug fix needs a test that would have caught it
- **Fix at the source** — don't add null checks at call sites when the bug is the caller

## Common Anti-Patterns

| Anti-Pattern | Consequence |
|-------------|-------------|
| Trying multiple random fixes | Creates new bugs, wastes time |
| Fixing symptoms instead of root cause | Bug comes back in different form |
| "Quick patch" under time pressure | Technical debt, harder to debug later |
| Combining multiple hypothesis tests | Can't tell which change fixed it |
| Skipping the regression test | Same bug reappears later |
