---
name: blogwatcher
description: Monitor blogs and RSS/Atom feeds for updates. Discover feeds, parse entries, and track changes.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["research", "rss", "feeds", "monitoring", "blogs"]
---

# Blog & Feed Watcher

Use this skill to monitor blogs, RSS feeds, and Atom feeds for new content.

## When to Use

- User wants to monitor a blog or website for updates
- User needs to read RSS/Atom feed content
- User wants to discover feeds on a website
- User needs to aggregate content from multiple sources

## Feed Discovery

Given a URL, try these feed locations:
1. Check `<link rel="alternate" type="application/rss+xml">` in HTML
2. Try common paths: `/feed`, `/rss`, `/atom.xml`, `/feed.xml`, `/rss.xml`
3. Parse the page for feed links

## Process

1. **Discover**: Find RSS/Atom feed URLs for given websites
2. **Fetch**: Download and parse feed XML
   ```bash
   curl -s "https://example.com/feed" | head -100
   ```
3. **Parse**: Extract entries with title, link, date, summary
4. **Filter**: Apply date/keyword filters as requested
5. **Summarize**: Present entries in a readable format

## Output Format

Present feed entries as a table:
| Date | Title | Source |
|------|-------|--------|
| 2024-01-15 | Article Title | blog.example.com |
