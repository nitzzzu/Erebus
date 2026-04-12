---
name: verification-before-completion
description: Use before claiming work is complete, fixed, or passing — run verification commands and confirm output before making any success claims. Evidence before assertions, always.
metadata:
  version: "2.0.0"
  author: erebus
  tags: ["software-development", "verification", "quality", "testing"]
---

# Verification Before Completion

Claiming work is complete without verification is dishonesty, not efficiency.

**Core principle:** Evidence before claims, always.

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this response, you cannot claim it passes.

## The Gate Function

Before claiming any status or expressing satisfaction:

1. **IDENTIFY** — What command proves this claim?
2. **RUN** — Execute the FULL command (fresh, complete run — not partial)
3. **READ** — Full output, check exit code, count failures
4. **VERIFY** — Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. **ONLY THEN** — Make the claim

Skip any step = claiming without evidence.

## Required Evidence by Claim Type

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
| Regression test works | RED then GREEN verified | Test passes once |
| Requirements met | Line-by-line checklist | Tests passing |

## Red Flags — STOP

Stop and run verification if you're about to say any of these:

- "should work now"
- "probably passes"
- "seems to be fixed"
- "looks correct"
- "I'm confident"
- "Done!" / "Complete!" / "All set!" (before verification)

These phrases mean you haven't verified. Run the command first.

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence ≠ evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter ≠ compiler |
| "Partial check is enough" | Partial proves nothing |
| "I'm tired" | Exhaustion ≠ excuse |

## Regression Test Verification

For TDD, verification is more strict:

```
WRITE test → RUN (must FAIL) → WRITE code → RUN (must PASS)
```

If you can't show the test failing first, you don't know if it tests the right thing.

## Correct Patterns

**Tests:**
```
✅ [Run: pytest -v] [Output: 34 passed] → "All 34 tests pass"
❌ "Should pass now" / "Looks correct"
```

**Build:**
```
✅ [Run: npm run build] [Output: exit 0] → "Build succeeds"
❌ "Linter passed" (linter doesn't check compilation)
```

**Bug fix:**
```
✅ [Run: pytest tests/test_bug.py] [Output: 1 passed] → "Bug is fixed"
❌ "I changed the code so it should be fixed"
```

**Requirements:**
```
✅ Re-read plan → check each item → "Items 1-5 complete, item 6 not started"
❌ "Tests pass, phase complete"
```

## Why This Matters

- Trust is broken when claims are made without evidence
- Code that "should work" often doesn't
- Partial checks miss the failures that matter most
- Automated tests exist precisely to eliminate guesswork

## When to Apply

Before ANY of these actions:
- Committing or pushing code
- Creating a PR
- Moving to the next task
- Reporting a phase complete
- Claiming a bug is fixed
- Delegating to another agent
