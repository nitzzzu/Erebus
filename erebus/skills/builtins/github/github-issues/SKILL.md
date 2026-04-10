---
name: github-issues
description: Create, search, triage, and manage GitHub issues with labels, assignments, and templates.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["github", "issues", "project-management"]
---

# GitHub Issues Management

Use this skill to manage GitHub issues.

## When to Use

- User wants to create a GitHub issue
- User needs to search or filter issues
- User wants to triage issues (label, assign, close)
- User needs to manage issue templates

## Operations

### Create Issue
```bash
gh issue create --title "Bug: ..." --body "Description" --label "bug"
```

### List Issues
```bash
gh issue list --state open --label "bug" --limit 20
```

### Search Issues
```bash
gh issue list --search "keyword in:title,body"
```

### Update Issue
```bash
gh issue edit {number} --add-label "priority:high" --add-assignee "@me"
gh issue close {number} --reason "completed"
```

## Process

1. **Identify**: What issue operation is needed?
2. **Execute**: Run the gh command
3. **Verify**: Confirm the operation
4. **Report**: Show the result with issue URL
