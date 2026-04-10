---
name: github-auth
description: Set up GitHub authentication via HTTPS tokens, SSH keys, or gh CLI for repository access.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["github", "authentication", "ssh", "token"]
---

# GitHub Authentication

Use this skill to configure GitHub authentication.

## When to Use

- User needs to set up git authentication
- Push/pull operations fail with auth errors
- User wants to configure SSH keys
- User needs a personal access token

## Methods

### gh CLI (Recommended)
```bash
gh auth login
gh auth status
```

### HTTPS Token
```bash
git config --global credential.helper store
echo "https://username:TOKEN@github.com" > ~/.git-credentials
```

### SSH Key
```bash
ssh-keygen -t ed25519 -C "email@example.com"
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
# Add public key to GitHub Settings > SSH Keys
```

## Detection Flow

1. Check if `gh` CLI is installed and authenticated
2. Check for existing SSH keys
3. Check git credential helper configuration
4. Recommend the best method based on what's available
