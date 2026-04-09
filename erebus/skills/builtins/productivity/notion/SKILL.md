---
name: notion
description: Create and manage Notion pages, databases, and blocks via the Notion API using curl.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["productivity", "notion", "notes", "databases"]
required_environment_variables:
  - name: NOTION_API_KEY
    prompt: "Enter your Notion Integration Token"
---

# Notion Integration

Use this skill to create and manage Notion pages, databases, and blocks.

## When to Use

- User wants to create or update Notion pages
- User needs to query a Notion database
- User wants to add content blocks to a page
- User needs to search their Notion workspace

## API Base

```bash
NOTION_BASE="https://api.notion.com/v1"
NOTION_HEADERS="-H 'Authorization: Bearer $NOTION_API_KEY' -H 'Notion-Version: 2022-06-28' -H 'Content-Type: application/json'"
```

## Common Operations

### Search
```bash
curl -s -X POST "$NOTION_BASE/search" $NOTION_HEADERS \
  -d '{"query": "search term"}'
```

### Create Page
### Query Database
### Append Blocks

## Process

1. **Identify**: What Notion operation is needed?
2. **Locate**: Find the target page/database ID
3. **Execute**: Make the API call
4. **Verify**: Confirm the operation succeeded
5. **Link**: Provide the Notion page URL
