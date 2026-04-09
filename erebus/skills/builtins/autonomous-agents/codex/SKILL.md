---
name: codex
description: Delegate coding tasks to OpenAI Codex CLI agent for one-shot tasks, background operations, and batch processing.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["autonomous-agents", "codex", "openai", "coding"]
---

# OpenAI Codex Agent Delegation

Use this skill to delegate tasks to the Codex CLI agent.

## When to Use

- User needs one-shot coding tasks executed
- User wants background long-running operations
- User needs batch processing of multiple issues
- Tasks that are well-defined and self-contained

## Usage

```bash
# One-shot task
codex run "Add input validation to all API endpoints"

# Background mode
codex run --background "Migrate database schema to v2"

# Batch processing
for issue in $(gh issue list --label "good-first-issue" -q '.[].number'); do
  codex run "Fix issue #$issue"
done
```

## Process

1. **Define**: Write a clear task description
2. **Execute**: Run codex with the task
3. **Monitor**: Check progress for background tasks
4. **Review**: Verify the output
5. **Commit**: Accept or reject changes
