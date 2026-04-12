---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code — creates comprehensive implementation plans with bite-sized tasks, exact file paths, and complete code in every step.
metadata:
  version: "2.0.0"
  author: erebus
  tags: ["software-development", "planning", "documentation"]
---

# Writing Implementation Plans

Write comprehensive plans assuming the engineer has zero context and questionable taste.
Document everything they need: which files to touch, exact code, how to test it.
Every task is bite-sized (2-5 minutes). DRY. YAGNI. TDD. Frequent commits.

## When to Use

- Before starting a multi-file implementation
- After brainstorming has produced an approved design spec
- When the user wants a detailed roadmap before execution
- For architecture documentation

## Plan Document Header

Every plan MUST start with this header:

```markdown
# [Feature Name] Implementation Plan

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

## File Structure Section

Before defining tasks, map out which files will be created or modified:

```markdown
## Files

**Created:**
- `src/path/new_file.py` — [one-sentence responsibility]

**Modified:**
- `src/path/existing.py` — [what changes]
- `tests/path/test_existing.py` — [what tests added]
```

Design units with clear boundaries. Each file should have one responsibility.
Files that change together should live together.

## Task Structure

Each task must follow this exact format:

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py`
- Test: `tests/exact/path/to/test_file.py`

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function_under_test(input_value)
    assert result == expected_output
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/path/test_file.py::test_specific_behavior -v
```

Expected: FAIL with "function_under_test not defined" or similar

- [ ] **Step 3: Write minimal implementation**

```python
def function_under_test(input_value):
    return expected_output
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/path/test_file.py::test_specific_behavior -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/path/test_file.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## Bite-Sized Task Granularity

Each step is ONE action (2-5 minutes):
- "Write the failing test" — step
- "Run it to see it fail" — step
- "Write minimal code to pass" — step
- "Run tests to confirm pass" — step
- "Commit" — step

## No Placeholders

These are **plan failures** — never write them:
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" (without showing the code)
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the code — tasks may be read out of order)
- Steps that describe what to do without showing how

Every step must contain the actual content an engineer needs.

## Self-Review

After writing the complete plan, review it:

1. **Spec coverage** — can you point to a task for every requirement?
2. **Placeholder scan** — any of the patterns above? Fix them.
3. **Type consistency** — do all types match across tasks?
4. **Command accuracy** — are file paths exact? Test commands correct?

Fix issues inline. Present the reviewed plan to the user.

## Rules

- Exact file paths always (never `path/to/file`)
- Complete code in every step — if a step changes code, show the code
- Exact commands with expected output
- Order tasks by dependency — no forward references
- DRY, YAGNI, TDD, frequent commits
