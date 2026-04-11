---
name: obsidian
description: Read, search, create, and manage notes in an Obsidian vault via the Local REST API.
metadata:
  version: "2.0.0"
  author: erebus
  tags: ["note-taking", "obsidian", "markdown", "knowledge"]
---

# Obsidian Vault Manager

Use this skill to interact with an Obsidian vault through the **obsidian-local-rest-api** plugin.
All operations go through the REST API — no direct filesystem access required.

## Prerequisites

The user must have the [obsidian-local-rest-api](https://github.com/coddingtonbear/obsidian-local-rest-api)
plugin installed and running in Obsidian, and the following env vars set:

- `EREBUS_OBSIDIAN_API_URL` — e.g. `https://localhost:27124`
- `EREBUS_OBSIDIAN_API_KEY` — the API key shown in the plugin settings

## Available Tools

| Tool | Description |
|------|-------------|
| `list_notes(directory="")` | List notes in a vault directory |
| `get_note(note_path)` | Read the full content of a note |
| `create_or_update_note(note_path, content)` | Create or replace a note |
| `append_to_note(note_path, content)` | Append text to an existing note |
| `delete_note(note_path)` | Delete a note |
| `search_notes(query)` | Full-text search across all notes |
| `list_tags()` | List all tags used in the vault |

## When to Use

- User wants to create or edit notes in their Obsidian vault
- User needs to search across their notes
- User wants to organize notes with tags and links
- User references their Obsidian vault
- User asks to save information to Obsidian

## Process

1. **List or search** to understand what exists before creating
2. **Use `[[wikilinks]]`** syntax when cross-referencing notes
3. **Use `#tag` format** for consistent organization
4. **Prefer `append_to_note`** when adding to existing notes instead of overwriting

## Note Path Format

Paths are relative to the vault root. Omit the leading `/`.
The `.md` extension is automatically added if omitted.

Examples:
- `Daily Notes/2024-01-15`
- `Projects/MyProject/Overview`
- `Inbox/Quick Note`

