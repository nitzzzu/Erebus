---
name: github-pr-workflow
description: Full pull request lifecycle — branch, commit, push, open PR, monitor CI, merge with squash/rebase options.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["github", "pull-requests", "workflow", "ci"]
---

# GitHub PR Workflow

Use this skill for the complete pull request lifecycle.

## When to Use

- User wants to create a PR from current changes
- User needs to manage the PR lifecycle
- User wants to monitor CI and fix failures
- User needs to merge a PR

## Workflow

### 1. Branch
```bash
git checkout -b feature/description
```

### 2. Commit
```bash
git add -A
git commit -m "feat: description of changes"
```

### 3. Push & Create PR
```bash
git push -u origin feature/description
gh pr create --title "feat: description" --body "## Changes\n- ..."
```

### 4. Monitor CI
```bash
gh pr checks {number} --watch
```

### 5. Fix CI Failures
```bash
gh pr checks {number}  # See what failed
# Fix the issue
git add -A && git commit -m "fix: ci failure" && git push
```

### 6. Merge
```bash
gh pr merge {number} --squash --auto
```

## Process

1. **Branch**: Create a feature branch
2. **Implement**: Make changes and commit
3. **PR**: Push and open a pull request
4. **CI**: Monitor and fix CI failures
5. **Review**: Address review comments
6. **Merge**: Squash and merge when approved
