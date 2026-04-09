---
name: memory
description: Store and recall user preferences, facts, and context across conversations.
license: MIT
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["memory", "personalization", "context"]
---

# Memory Skill

Use this skill to manage persistent memory across conversations.

## When to Use

- User shares preferences, facts about themselves, or important context
- User asks what you remember about them
- Previous context is needed to personalize responses
- User explicitly asks to remember or forget something

## Process

1. **Identify Memorable Info**: Recognize when the user shares something worth remembering
2. **Store Proactively**: Use agentic memory to save facts without being asked
3. **Recall Naturally**: Weave remembered information naturally into responses
4. **Respect Privacy**: Only store relevant, non-sensitive information

## What to Remember

- User's name and preferences
- Project or domain context
- Communication style preferences (formal/casual, detail level)
- Frequently used tools or technologies
- Goals and constraints the user has mentioned

## Best Practices

- Confirm with the user before storing sensitive information
- Summarize what you've remembered when relevant
- Update memories when the user provides corrections
- Don't reference memories in a way that feels surveillance-like
