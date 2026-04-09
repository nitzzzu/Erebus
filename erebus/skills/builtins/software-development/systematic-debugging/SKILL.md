---
name: systematic-debugging
description: Four-phase root cause investigation — RED (find cause), PATTERN (compare), HYPOTHESIS (test), IMPLEMENTATION.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["software-development", "debugging", "troubleshooting"]
---

# Systematic Debugging

Use this skill for methodical bug investigation and resolution.

## When to Use

- User reports a bug that isn't immediately obvious
- Test failures with unclear cause
- Production issues requiring root cause analysis
- Complex bugs that span multiple components

## Four Phases

### Phase 1: RED — Find the Cause
- Reproduce the bug reliably
- Identify the exact error message and stack trace
- Determine when the bug was introduced (git bisect)
- Narrow down the affected code path

### Phase 2: PATTERN — Compare
- Compare working vs. broken states
- Check recent changes (git log, git diff)
- Look for similar bugs in issue trackers
- Identify common patterns

### Phase 3: HYPOTHESIS — Test
- Form a specific hypothesis about the root cause
- Design a minimal test to confirm or deny
- Execute the test
- If denied, return to Phase 1 with new information

### Phase 4: IMPLEMENTATION — Fix
- Write the minimal fix
- Add a regression test
- Verify the fix resolves the original issue
- Check for similar bugs elsewhere in the codebase

## Rules

- **Never fix before understanding**: Complete Phase 1-3 before writing any fix
- **One change at a time**: Don't combine fixes
- **Always add a test**: Every bug fix needs a regression test
