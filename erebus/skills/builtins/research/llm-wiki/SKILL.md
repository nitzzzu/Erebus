---
name: llm-wiki
description: Build and maintain a persistent interlinked markdown knowledge base, optionally stored in an Obsidian vault.
metadata:
  version: "2.0.0"
  author: erebus
  tags: ["research", "knowledge-base", "wiki", "markdown", "obsidian"]
---

# LLM Wiki — Knowledge Base Builder

Use this skill to build and maintain a persistent, interlinked markdown knowledge base.
When Obsidian integration is configured, all notes are stored directly in the vault
using the `obsidian` tools. Otherwise, use the filesystem tools.

## Storage Backend

**With Obsidian** (`EREBUS_OBSIDIAN_API_URL` + `EREBUS_OBSIDIAN_API_KEY` configured):
- Use `create_or_update_note` and `append_to_note` to write notes
- Use `search_notes` to find existing notes
- Use `list_notes` to browse the wiki structure
- Store all wiki notes under a `wiki/` prefix (e.g. `wiki/pages/concept.md`)

**Without Obsidian** (filesystem fallback):
- Use `FileTools` / `FileEditTools` to write markdown files
- Store wiki under `~/wiki/` or the active workspace

## Architecture

### Layer 1 — Raw Sources
Store raw materials as-is:
```
wiki/sources/paper-title.md
wiki/sources/article-summary.md
```

### Layer 2 — Wiki Pages
Synthesized, interlinked knowledge pages:
```
wiki/pages/concept-name.md      # [[links]] to other pages
wiki/pages/person-name.md
```

### Layer 3 — Schema / Index
High-level organization:
```
wiki/index.md        # Master table of contents
wiki/schema.md       # Ontology / concept map
```

## Process

1. **Gather**: Collect raw information into Layer 1 sources
2. **Synthesize**: Create wiki pages in Layer 2 with `[[wikilinks]]`
3. **Organize**: Build and update `wiki/index.md`
4. **Maintain**: Update pages as new information arrives
5. **Query**: Search the wiki to answer questions

## Best Practices

- Use `[[wikilinks]]` for cross-referencing between pages
- Include source citations in every wiki page
- Keep pages focused on a single concept
- Update the index when adding new pages
- Use `search_notes` (Obsidian) or `grep` (filesystem) before creating duplicates
