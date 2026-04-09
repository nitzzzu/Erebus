---
name: codebase-inspection
description: Analyze repositories for lines of code, language breakdown, file counts, and code-vs-comment ratios using pygount.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["github", "code-analysis", "metrics", "statistics"]
---

# Codebase Inspection

Use this skill to analyze repository structure and code metrics.

## When to Use

- User wants to understand a codebase's size and composition
- User needs language breakdown statistics
- User wants code quality metrics
- User asks "how big is this repo" or "what languages"

## Tools

### pygount
```bash
pip install pygount
pygount --format=summary /path/to/repo
pygount --format=cloc-xml /path/to/repo
```

### Quick Analysis
```bash
# Language breakdown
find . -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -20

# Lines of code
find . -name '*.py' | xargs wc -l | tail -1
```

## Process

1. **Clone/Navigate**: Get to the repository
2. **Scan**: Run pygount or find-based analysis
3. **Summarize**: Present language breakdown, LOC, file counts
4. **Exclude**: Skip node_modules, .git, venv, build dirs
5. **Present**: Format as a table
