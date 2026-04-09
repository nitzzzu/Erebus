---
name: github-code-review
description: Review pull requests with inline comments, approve/request changes, and check CI status via GitHub API.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["github", "code-review", "pull-requests"]
---

# GitHub Code Review

Use this skill for reviewing pull requests on GitHub.

## When to Use

- User asks to review a PR
- User wants to leave review comments
- User needs to check PR CI status
- User wants to approve or request changes on a PR

## Operations

### View PR Diff
```bash
gh pr diff {number}
```

### Leave Review
```bash
gh pr review {number} --approve --body "LGTM!"
gh pr review {number} --request-changes --body "Please fix..."
gh pr review {number} --comment --body "Looks good overall..."
```

### Check CI Status
```bash
gh pr checks {number}
```

### Add Inline Comment
```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments \
  -f body="Suggestion: use a constant here" \
  -f path="src/file.py" \
  -F line=42 \
  -f side=RIGHT
```

## Process

1. **Fetch**: Get the PR diff and context
2. **Review**: Apply the code review checklist
3. **Comment**: Leave inline comments on specific lines
4. **Verdict**: Approve, request changes, or comment
