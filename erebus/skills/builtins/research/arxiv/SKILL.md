---
name: arxiv
description: Search and retrieve academic papers from arXiv. Query by topic, author, or ID. Generate BibTeX citations.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["research", "papers", "arxiv", "academic", "citations"]
---

# arXiv Paper Search

Use this skill to search, retrieve, and analyze academic papers from arXiv.

## When to Use

- User asks about recent research papers or preprints
- User needs to find papers on a specific topic
- User wants to summarize or analyze a paper
- User needs BibTeX citations
- User asks about state-of-the-art in a research area

## Process

1. **Search**: Use the arXiv API to find relevant papers
   ```bash
   curl -s "http://export.arxiv.org/api/query?search_query=all:{query}&max_results=10&sortBy=submittedDate&sortOrder=descending"
   ```

2. **Retrieve**: Get full paper details by arXiv ID
   ```bash
   curl -s "http://export.arxiv.org/api/query?id_list={arxiv_id}"
   ```

3. **Summarize**: Extract title, authors, abstract, and key findings

4. **Cross-reference**: Use Semantic Scholar for citation counts
   ```bash
   curl -s "https://api.semanticscholar.org/graph/v1/paper/ArXiv:{id}?fields=title,citationCount,influentialCitationCount,references"
   ```

5. **Cite**: Generate BibTeX entries for requested papers

## Best Practices

- Use specific search terms for better results
- Check publication date to ensure recency
- Cross-reference citation counts for impact assessment
- Provide both the abstract summary and a plain-language explanation
