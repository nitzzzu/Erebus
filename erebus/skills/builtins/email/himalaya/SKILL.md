---
name: himalaya
description: Full IMAP/SMTP email client via Himalaya CLI — list, read, search, compose, reply, and forward emails.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["email", "imap", "smtp", "himalaya"]
---

# Himalaya Email Client

Use this skill to manage email via the Himalaya CLI.

## When to Use

- User wants to read, send, or search emails
- User needs to manage multiple email accounts
- User wants to compose emails from the terminal
- User needs to reply to or forward emails

## Installation

```bash
# macOS
brew install himalaya

# Linux
cargo install himalaya
```

## Operations

### List Messages
```bash
himalaya list --folder INBOX --page-size 10
```

### Read Message
```bash
himalaya read {id}
```

### Search
```bash
himalaya search "subject:meeting from:boss@company.com"
```

### Send Email
```bash
himalaya send <<EOF
From: me@example.com
To: recipient@example.com
Subject: Hello

Body of the email here.
EOF
```

### Reply / Forward
```bash
himalaya reply {id}
himalaya forward {id}
```

## Process

1. **Verify Config**: Ensure himalaya is configured with account credentials
2. **Execute**: Run the requested email operation
3. **Present**: Format email content for readable display
4. **Confirm**: Always confirm before sending emails
