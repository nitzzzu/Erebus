---
name: obsidian-local
description: Obsidian Local REST API tools for the CodeAgent — manage vault notes, search, and metadata
platforms: [linux, macos, windows]
---

# Obsidian Local REST API — CodeAgent Tools

## Overview

This skill extends the CodeAgent with Obsidian vault management functions.
When the Obsidian Local REST API plugin is running, these tools let you
search, read, create, and update notes directly from code snippets.

## Setup

1. Install the [Obsidian Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) plugin
2. Set environment variables:
   - `OBSIDIAN_API_URL` — e.g. `https://127.0.0.1:27124`
   - `OBSIDIAN_API_KEY` — your API key from the plugin settings

## CodeAgent Functions

These functions are automatically available in `run_code_agent` when this skill is present:

- `obsidian_search(query, context_length=100)` — full-text search across all notes
- `obsidian_read(path)` — read a note's content by vault path
- `obsidian_write(path, content)` — create or overwrite a note
- `obsidian_append(path, content)` — append to an existing note
- `obsidian_list(folder="/")` — list files in a vault folder
- `obsidian_delete(path)` — delete a note

## Example

```python
# Search for all notes about "project alpha"
results = obsidian_search("project alpha")
print(results)

# Read a specific note
content = obsidian_read("Projects/Alpha/notes.md")
print(content)

# Create a daily note
from datetime import date
today = date.today().isoformat()
obsidian_write(f"Daily/{today}.md", f"# {today}\n\n- [ ] Morning review\n")
```
