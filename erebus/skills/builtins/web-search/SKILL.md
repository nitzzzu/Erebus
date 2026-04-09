---
name: web-search
description: Search the web using DuckDuckGo for current information, news, and facts.
license: MIT
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["web", "search", "information"]
---

# Web Search Skill

Use this skill when the user needs current information from the internet.

## When to Use

- User asks about recent events, news, or time-sensitive information
- User needs facts that may have changed since training data cutoff
- User asks about products, prices, or availability
- User needs to verify current information

## Process

1. **Formulate Query**: Create a clear, concise search query based on the user's request
2. **Execute Search**: Use the `duckduckgo_search` tool to find relevant results
3. **Synthesize Results**: Combine and summarize the most relevant information
4. **Cite Sources**: Always mention where the information came from

## Best Practices

- Use specific keywords for better results
- Search multiple queries if needed to get comprehensive information
- Prefer authoritative sources (official sites, reputable news)
- Clearly distinguish search results from your own knowledge
