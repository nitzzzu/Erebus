---
name: google-workspace
description: Interact with Gmail, Calendar, Drive, Contacts, Sheets, and Docs via Python with OAuth2 authentication.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["productivity", "google", "gmail", "calendar", "drive"]
required_environment_variables:
  - name: GOOGLE_CLIENT_ID
    prompt: "Enter your Google OAuth Client ID"
  - name: GOOGLE_CLIENT_SECRET
    prompt: "Enter your Google OAuth Client Secret"
---

# Google Workspace Integration

Use this skill to interact with Google services (Gmail, Calendar, Drive, Sheets, Docs).

## When to Use

- User wants to read/send emails via Gmail
- User needs to check/create calendar events
- User wants to upload/download files from Drive
- User needs to read/write Google Sheets or Docs

## Setup

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

## Authentication

Uses OAuth2 with automatic token refresh. Tokens stored at `~/.erebus/google_token.json`.

## Services

### Gmail
- List messages, read content, send emails, search inbox
- Support for attachments and labels

### Calendar
- List upcoming events, create events, update events
- Timezone handling and recurring events

### Drive
- List files, upload, download, share
- Folder management and permissions

### Sheets
- Read ranges, write data, create spreadsheets
- Formula support and formatting

## Process

1. **Authenticate**: Ensure OAuth tokens are valid
2. **Identify Service**: Determine which Google service is needed
3. **Execute**: Make the API call
4. **Format**: Present results clearly to the user
