---
name: llm-wiki
description: Build and maintain a persistent interlinked markdown knowledge base with layered knowledge architecture.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["research", "knowledge-base", "wiki", "markdown"]
---

# LLM Wiki — Knowledge Base Builder

Use this skill to build and maintain a persistent, interlinked markdown knowledge base.

## When to Use

- User wants to organize research into a structured knowledge base
- User needs to create interlinked notes on a topic
- User wants to build a personal wiki from gathered information
- User needs to synthesize information from multiple sources

## Architecture

### Layer 1 — Raw Sources
Store raw materials (articles, papers, notes) as-is:
```
wiki/sources/
├── paper-title.md
├── article-summary.md
└── interview-notes.md
```

### Layer 2 — Wiki Pages
Synthesized, interlinked knowledge pages:
```
wiki/pages/
├── concept-name.md      # [[links]] to other pages
├── person-name.md
└── methodology.md
```

### Layer 3 — Schema / Index
High-level organization and navigation:
```
wiki/index.md            # Master table of contents
wiki/schema.md           # Ontology / concept map
```

## Process

1. **Gather**: Collect raw information into Layer 1
2. **Synthesize**: Create wiki pages in Layer 2 with `[[wikilinks]]`
3. **Organize**: Build index and schema in Layer 3
4. **Maintain**: Update pages as new information arrives
5. **Query**: Navigate the wiki to answer questions

## Best Practices

- Use `[[wikilinks]]` for cross-referencing between pages
- Include source citations in every wiki page
- Keep pages focused on a single concept
- Update the index when adding new pages
