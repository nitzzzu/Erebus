---
name: github-repo-management
description: Clone, create, fork repositories. Configure settings, branch protection, secrets, releases, and workflows.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["github", "repositories", "management", "admin"]
---

# GitHub Repository Management

Use this skill for repository-level GitHub operations.

## When to Use

- User wants to create a new repository
- User needs to configure repository settings
- User wants to set up branch protection rules
- User needs to manage secrets, releases, or workflows

## Operations

### Create Repo
```bash
gh repo create my-repo --public --clone
```

### Clone Repo
```bash
gh repo clone owner/repo
```

### Fork Repo
```bash
gh repo fork owner/repo --clone
```

### Configure Settings
```bash
gh repo edit --default-branch main --enable-issues --enable-wiki=false
```

### Branch Protection
```bash
gh api repos/{owner}/{repo}/branches/main/protection \
  -X PUT -f required_status_checks='{"strict":true,"contexts":["ci"]}' \
  -f enforce_admins=true
```

### Manage Secrets
```bash
gh secret set API_KEY --body "secret-value"
gh secret list
```

### Create Release
```bash
gh release create v1.0.0 --title "v1.0.0" --notes "Release notes"
```

## Process

1. **Identify**: What repository operation is needed?
2. **Check Permissions**: Verify access level
3. **Execute**: Run the appropriate command
4. **Verify**: Confirm the operation succeeded
