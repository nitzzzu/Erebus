---
name: receiving-code-review
description: Use when receiving code review feedback, before implementing suggestions — requires technical rigor and verification rather than performative agreement or blind implementation.
metadata:
  version: "2.0.0"
  author: erebus
  tags: ["software-development", "code-review", "quality"]
---

# Receiving Code Review Feedback

Code review requires technical evaluation, not emotional performance.

**Core principle:** Verify before implementing. Ask before assuming. Technical correctness over social comfort.

## The Response Pattern

```
1. READ: Complete feedback without reacting
2. UNDERSTAND: Restate requirement in own words (or ask for clarification)
3. VERIFY: Check against codebase reality
4. EVALUATE: Is this technically sound for THIS codebase?
5. RESPOND: Technical acknowledgment or reasoned pushback
6. IMPLEMENT: One item at a time, test each
```

## Forbidden Responses

**NEVER:**
- "You're absolutely right!" — performative agreement
- "Great point!" / "Excellent feedback!" — sycophantic
- "Let me implement that now" — before verification

**INSTEAD:**
- Restate the technical requirement
- Ask clarifying questions
- Push back with technical reasoning if wrong
- Just start working (actions over words)

## Handling Unclear Feedback

If ANY item is unclear: STOP. Do not implement anything yet.
Ask for clarification on ALL unclear items before proceeding.

Partial understanding = wrong implementation.

**Example:**
```
Reviewer: "Fix issues 1-6"
You understand 1, 2, 3, 6. Unclear on 4, 5.

❌ WRONG: Implement 1,2,3,6 now, ask about 4,5 later
✅ RIGHT: "I understand items 1,2,3,6. Need clarification on 4 and 5 before proceeding."
```

## Implementation Order

For multi-item feedback:
1. Clarify anything unclear FIRST
2. Then implement in this order:
   - Blocking issues (crashes, security)
   - Simple fixes (typos, imports)
   - Complex fixes (refactoring, logic)
3. Test each fix individually
4. Verify no regressions after all fixes

## When to Push Back

Push back when:
- Suggestion breaks existing functionality
- Reviewer lacks full context
- Violates YAGNI (unused feature being added)
- Technically incorrect for this stack
- Legacy/compatibility reasons exist
- Conflicts with prior architectural decisions

**How to push back:**
- Use technical reasoning, not defensiveness
- Ask specific questions
- Reference working tests or code
- Involve the user if it's an architectural conflict

## YAGNI Check

When reviewer suggests "implementing properly" or adding a feature:
- Search the codebase for actual usage
- If unused: "This isn't called anywhere — should I remove it instead (YAGNI)?"
- If used: then implement properly

## Acknowledging Correct Feedback

```
✅ "Fixed. [Brief description of what changed]"
✅ "Good catch — [specific issue]. Fixed in [location]."
✅ [Just fix it and show the diff]

❌ "You're absolutely right!"
❌ "Great point!"
❌ "Thanks for catching that!"
```

Actions speak. Just fix it. The code itself shows you heard the feedback.

## Correcting Your Own Pushback

If you pushed back and were wrong:
```
✅ "You were right — I checked [X] and it does [Y]. Implementing now."
✅ "Verified and you're correct. My initial understanding was wrong because [reason]. Fixing."

❌ Long apology
❌ Defending why you pushed back
❌ Over-explaining
```

State the correction factually and move on.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Performative agreement | State requirement or just act |
| Blind implementation | Verify against codebase first |
| Batch without testing | One at a time, test each |
| Assuming reviewer is right | Check if it breaks things |
| Avoiding pushback | Technical correctness > comfort |
| Implementing partial items | Clarify ALL unclear items first |
