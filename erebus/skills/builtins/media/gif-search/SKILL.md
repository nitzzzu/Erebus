---
name: gif-search
description: Search and download GIFs using the Tenor API with multiple format options and content filtering.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["media", "gif", "tenor", "search"]
required_environment_variables:
  - name: TENOR_API_KEY
    prompt: "Enter your Tenor API key (get one at https://developers.google.com/tenor)"
---

# GIF Search (Tenor)

Use this skill to search for and share GIFs.

## When to Use

- User asks for a GIF or reaction image
- User wants to find a GIF for a specific emotion or situation
- User needs animated content for a presentation or message

## API Usage

```bash
curl -s "https://tenor.googleapis.com/v2/search?q={query}&key=$TENOR_API_KEY&limit=5"
```

## Process

1. **Search**: Query Tenor with relevant keywords
2. **Select**: Choose the best matching GIF
3. **Present**: Provide the GIF URL and preview
