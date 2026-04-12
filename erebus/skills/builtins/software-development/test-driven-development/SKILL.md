---
name: test-driven-development
description: Use when implementing any feature or bugfix, before writing implementation code — enforces RED-GREEN-REFACTOR cycle: write failing test first, then minimal code to pass, then refactor.
metadata:
  version: "2.0.0"
  author: erebus
  tags: ["software-development", "tdd", "testing"]
---

# Test-Driven Development (TDD)

Write the test first. Watch it fail. Write minimal code to pass.

**Core principle:** If you didn't watch the test fail, you don't know if it tests the right thing.

## When to Use

**Always:**
- New features
- Bug fixes
- Refactoring
- Behavior changes

**Exceptions (ask the user):**
- Throwaway prototypes
- Generated/scaffolded code
- Configuration files

Thinking "skip TDD just this once"? Stop. That's rationalization.

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before the test? Delete it. Start over.

No exceptions:
- Don't keep it as "reference"
- Don't "adapt" it while writing tests
- Don't look at it while writing tests
- Delete means delete

## RED — Write a Failing Test

Write the SMALLEST test that specifies the desired behavior.

**Good test:**
```python
def test_retries_failed_operations_three_times():
    attempts = []
    def operation():
        attempts.append(1)
        if len(attempts) < 3:
            raise ValueError("fail")
        return "success"

    result = retry_operation(operation)

    assert result == "success"
    assert len(attempts) == 3
```
Clear name, tests real behavior, one thing.

**Bad test:**
```python
def test_retry():  # vague name
    mock = Mock(side_effect=[Exception(), Exception(), "success"])
    retry_operation(mock)  # tests mock, not code
    assert mock.call_count == 3
```

**Requirements for a good test:**
- Tests ONE behavior
- Name describes behavior (not "test_thing_works")
- Uses real code, not mocks (unless unavoidable)

## Verify RED — Watch It Fail

**MANDATORY. Never skip.**

```bash
pytest path/to/test_file.py::test_specific_behavior -v
```

Confirm:
- Test FAILS (not errors with a traceback from bad syntax)
- Failure message says what was expected
- Fails because feature is missing (not because of a typo)

**Test passes unexpectedly?** You're testing existing behavior. Fix the test.
**Test errors out?** Fix syntax error, re-run until it fails correctly.

## GREEN — Write Minimal Code

Write the SIMPLEST code to make the test pass.

**Good (minimal):**
```python
def retry_operation(fn):
    for i in range(3):
        try:
            return fn()
        except Exception:
            if i == 2:
                raise
```
Just enough to pass.

**Bad (over-engineered):**
```python
def retry_operation(fn, max_retries=3, backoff="linear", on_retry=None):
    # YAGNI — no test requires this
```

Don't add features, refactor other code, or "improve" beyond the test.

## Verify GREEN — Watch It Pass

**MANDATORY.**

```bash
pytest path/to/test_file.py::test_specific_behavior -v
# Also run full suite
pytest -v
```

Confirm:
- The new test PASSES
- All other tests still pass
- No unexpected output (warnings, errors)

**Test fails?** Fix the code, not the test.
**Other tests fail?** Fix them now before continuing.

## REFACTOR — Clean Up

After GREEN only:
- Remove duplication
- Improve names
- Extract helpers

Keep all tests green throughout. Don't add new behavior during refactor.

## Repeat

Write the next failing test for the next behavior. Loop.

## Good Test Names

| Good | Bad |
|------|-----|
| `test_returns_empty_list_when_no_results` | `test_results` |
| `test_raises_valueerror_on_negative_input` | `test_error` |
| `test_sends_notification_after_payment` | `test_payment_works` |

If "and" appears in a test name, split it into two tests.

## Why Order Matters

Tests written AFTER code pass immediately. That proves nothing:
- Might test implementation, not behavior
- Might miss edge cases you forgot
- You never saw it catch a bug

Test-first forces you to see the test fail, proving it tests the right thing.
