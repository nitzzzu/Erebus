---
name: opencode
description: Provider-agnostic AI coding agent with TUI — one-shot tasks, interactive sessions, and parallel work patterns.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["autonomous-agents", "opencode", "coding", "tui"]
---

# OpenCode Agent

Use this skill to delegate tasks to the OpenCode agent.

## When to Use

- User needs a provider-agnostic coding agent
- User wants an interactive TUI for coding
- User needs one-shot task execution
- Tasks that work well with any LLM provider

## Usage

```bash
# One-shot task
opencode run "Implement the caching layer for the API"

# Interactive mode
opencode

# With specific provider
OPENCODE_PROVIDER=anthropic opencode run "Write unit tests for auth module"
```

## Process

1. **Define**: Clear task description with context
2. **Execute**: Run opencode with the task
3. **Review**: Check the implementation
4. **Accept**: Merge the changes if correct
