---
name: obsidian
description: Read, search, create, and manage notes in an Obsidian vault with wikilinks and markdown support.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["note-taking", "obsidian", "markdown", "knowledge"]
---

# Obsidian Vault Manager

Use this skill to interact with Obsidian vaults.

## When to Use

- User wants to create or edit notes in their Obsidian vault
- User needs to search across their notes
- User wants to organize notes with tags and links
- User references their Obsidian vault

## Operations

### Find Vault
```bash
# Common vault locations
find ~/Documents -name ".obsidian" -type d 2>/dev/null
find ~ -name ".obsidian" -type d -maxdepth 4 2>/dev/null
```

### List Notes
```bash
find /path/to/vault -name "*.md" -not -path "*/.obsidian/*" | sort
```

### Search Notes
```bash
grep -rl "search term" /path/to/vault --include="*.md"
```

### Create Note
```bash
cat > "/path/to/vault/Note Title.md" << 'EOF'
# Note Title

Content here with [[wikilinks]] to other notes.

#tag1 #tag2
EOF
```

## Process

1. **Locate Vault**: Find the Obsidian vault path
2. **Execute**: Perform the requested operation
3. **Wikilinks**: Use `[[Note Name]]` for cross-references
4. **Tags**: Use `#tag` format for organization
