---
name: dispatching-parallel-agents
description: Use when facing 2+ independent tasks (test failures, bugs, subsystems) that can be worked on concurrently without shared state or sequential dependencies.
metadata:
  version: "2.0.0"
  author: erebus
  tags: ["software-development", "agents", "parallel", "automation"]
---

# Dispatching Parallel Agents

When you have multiple unrelated failures or independent problems, investigating
them sequentially wastes time. Each investigation is independent and can happen
in parallel.

**Core principle:** One agent per independent problem domain. Let them work concurrently.

## When to Use

**Use when:**
- 2+ test files failing with different root causes
- Multiple subsystems broken independently
- Each problem can be understood without context from others
- No shared state between investigations

**Don't use when:**
- Failures are related (fixing one might fix others)
- Need to understand full system state first
- Agents would interfere (editing same files, using same resources)
- You don't yet know what's broken (investigate yourself first)

## The Pattern

### 1. Identify Independent Domains

Group failures by what's broken, not by symptom:

```
File A tests: Authentication flow (3 failures)
File B tests: Data export behavior (2 failures)
File C tests: Background job processing (4 failures)
```

Each domain is independent — fixing auth doesn't affect export tests.

### 2. Create Focused Agent Tasks

Each agent gets exactly:
- **Specific scope** — one test file or subsystem
- **Clear goal** — what "done" looks like
- **Constraints** — what NOT to change
- **Expected output** — summary of what was found and fixed

### 3. Dispatch in Parallel

Dispatch all independent agents at the same time, not sequentially.

### 4. Review and Integrate

When agents return:
- Read each agent's summary
- Verify fixes don't conflict with each other
- Run the full test suite
- Integrate all changes

## Agent Prompt Structure

Good agent prompts are focused, self-contained, and specific about output.

**Template:**
```markdown
Fix the <N> failing tests in <path/to/test_file.py>:

1. "<test name>" — expects <behavior>
2. "<test name>" — expects <behavior>

These failures appear to be <your diagnosis>.

Your task:
1. Read the test file and understand what each test verifies
2. Identify the root cause
3. Fix the root cause (not just the tests)
4. Run the tests to verify they pass
5. Verify no other tests broke

Constraints:
- Do NOT change files outside <scope>
- Do NOT just adjust test expectations to match broken behavior

Return: Summary of root cause and what you changed.
```

## Common Mistakes

**Too broad:**
```
❌ "Fix all the tests" — agent gets lost
✅ "Fix agent-tool-abort.test.ts" — focused scope
```

**No context:**
```
❌ "Fix the race condition" — agent doesn't know where
✅ Paste exact error messages and test names
```

**No constraints:**
```
❌ No constraints → agent refactors everything
✅ "Do NOT change production code" or "Fix tests only"
```

**Vague expected output:**
```
❌ "Fix it"
✅ "Return summary of root cause and changes made"
```

## When NOT to Use

- Related failures (fix one might fix others)
- Need full context to understand the problem
- Still in exploratory debugging phase (don't know what's broken yet)
- Shared state (agents would interfere editing same files)

## Integration

After parallel agents complete:
1. Read all summaries
2. Run full test suite
3. If any new failures → investigate (may be conflicts between fixes)
4. Commit integrated result
