"""Agno Toolkit for web search and page fetching via the Agentic Fetch API.

Uses the self-hosted Agentic Fetch service:
https://github.com/nitzzzu/agentic-fetch

Configuration (env var):
    EREBUS_AGENTIC_FETCH_URL — base URL, e.g. ``http://localhost:3001``

When the URL is not configured, all tool calls return a descriptive error
so the agent can surface the issue to the user rather than failing silently.

Supported tools
---------------
- search_web          — Google (or any engine) full-web search
- search_hackernews   — Hacker News search with min-points filter
- search_reddit       — Reddit search with sort / time-filter
- search_github       — GitHub repository search with sort / date-from filter
- fetch_url           — Fetch a URL and return readable markdown
- grep_url            — Grep a fetched page for a regex pattern
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Optional

from agno.tools.toolkit import Toolkit

logger = logging.getLogger(__name__)

_DEFAULT_MAX_LENGTH = 8000
_USER_AGENT = (
    "Mozilla/5.0 (compatible; Erebus/1.0; +https://github.com/nitzzzu/Erebus)"
)


class WebFetchTools(Toolkit):
    """Agent tools for web search and page fetching via the Agentic Fetch API."""

    def __init__(self, api_url: Optional[str] = None, max_length: int = _DEFAULT_MAX_LENGTH) -> None:
        self._api_url = api_url.rstrip("/") if api_url else None
        self._max_length = max_length
        super().__init__(name="web_fetch")
        self.register(self.search_web)
        self.register(self.search_hackernews)
        self.register(self.search_reddit)
        self.register(self.search_github)
        self.register(self.fetch_url)
        self.register(self.grep_url)

    def _post(self, path: str, params: dict) -> tuple[int, str]:
        if not self._api_url:
            return 0, "EREBUS_AGENTIC_FETCH_URL is not configured."
        url = f"{self._api_url}{path}"
        body = json.dumps(params).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"User-Agent": _USER_AGENT, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.status, resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8", errors="replace")
        except urllib.error.URLError as exc:
            return 0, str(exc.reason)
        except Exception as exc:
            return 0, str(exc)

    def _format_results(self, body: str, max_results: int) -> str:
        """Parse a /search response body and return formatted text."""
        try:
            data = json.loads(body)
            results = data if isinstance(data, list) else data.get("results", data)
            if not results:
                return "No results found."
            parts: list[str] = []
            for r in results[:max_results]:
                title = r.get("title", "")
                url = r.get("url", r.get("link", ""))
                snippet = r.get("snippet", r.get("description", r.get("content", "")))
                parts.append(f"**{title}**\n{url}\n{snippet}")
            return "\n\n".join(parts)
        except (json.JSONDecodeError, KeyError):
            return body[:self._max_length]

    # ------------------------------------------------------------------
    # Search tools
    # ------------------------------------------------------------------

    def search_web(self, query: str, max_results: int = 5, engine: str = "google") -> str:
        """Search the web for information.

        Parameters
        ----------
        query:
            The search query.
        max_results:
            Maximum number of results to return (default 5).
        engine:
            Search engine to use. One of: ``google`` (default), ``hackernews``,
            ``reddit``, ``github``.

        Returns
        -------
        str
            Formatted search results with title, URL, and snippet, or an error message.
        """
        if not self._api_url:
            return "Web search is not available: EREBUS_AGENTIC_FETCH_URL is not set."

        status, body = self._post("/search", {"query": query, "engine": engine, "max_results": max_results})
        if status == 200:
            return self._format_results(body, max_results)
        return f"Search failed ({status}): {body[:500]}"

    def search_hackernews(self, query: str, max_results: int = 5, min_points: int = 50) -> str:
        """Search Hacker News for discussions and articles.

        Parameters
        ----------
        query:
            The search query.
        max_results:
            Maximum number of results to return (default 5).
        min_points:
            Minimum HN points / upvotes to filter by (default 50).

        Returns
        -------
        str
            Formatted HN results with title, URL, points, and comment count.
        """
        if not self._api_url:
            return "Web search is not available: EREBUS_AGENTIC_FETCH_URL is not set."

        status, body = self._post("/search", {
            "query": query,
            "engine": "hackernews",
            "max_results": max_results,
            "min_points": min_points,
        })
        if status == 200:
            return self._format_results(body, max_results)
        return f"HN search failed ({status}): {body[:500]}"

    def search_reddit(
        self,
        query: str,
        max_results: int = 5,
        sort: str = "top",
        time_filter: str = "month",
    ) -> str:
        """Search Reddit for community discussions.

        Parameters
        ----------
        query:
            The search query.
        max_results:
            Maximum number of results to return (default 5).
        sort:
            Sort order. One of: ``top`` (default), ``new``, ``hot``, ``relevance``.
        time_filter:
            Time window. One of: ``day``, ``week``, ``month`` (default), ``year``, ``all``.

        Returns
        -------
        str
            Formatted Reddit results with title, subreddit, URL, and snippet.
        """
        if not self._api_url:
            return "Web search is not available: EREBUS_AGENTIC_FETCH_URL is not set."

        status, body = self._post("/search", {
            "query": query,
            "engine": "reddit",
            "max_results": max_results,
            "sort": sort,
            "time_filter": time_filter,
        })
        if status == 200:
            return self._format_results(body, max_results)
        return f"Reddit search failed ({status}): {body[:500]}"

    def search_github(
        self,
        query: str,
        max_results: int = 5,
        sort: str = "stars",
        date_from: Optional[str] = None,
    ) -> str:
        """Search GitHub for repositories.

        Parameters
        ----------
        query:
            The search query.
        max_results:
            Maximum number of results to return (default 5).
        sort:
            Sort order. One of: ``stars`` (default), ``updated``, ``forks``.
        date_from:
            Only include repos updated on or after this date (ISO format, e.g. ``2026-01-01``).

        Returns
        -------
        str
            Formatted GitHub results with repo name, stars, language, and description.
        """
        if not self._api_url:
            return "Web search is not available: EREBUS_AGENTIC_FETCH_URL is not set."

        payload: dict = {
            "query": query,
            "engine": "github",
            "max_results": max_results,
            "sort": sort,
        }
        if date_from:
            payload["date_from"] = date_from

        status, body = self._post("/search", payload)
        if status == 200:
            return self._format_results(body, max_results)
        return f"GitHub search failed ({status}): {body[:500]}"

    # ------------------------------------------------------------------
    # Fetch / grep tools
    # ------------------------------------------------------------------

    def fetch_url(
        self,
        url: str,
        max_length: Optional[int] = None,
        include_links: bool = False,
    ) -> str:
        """Fetch the content of a URL and return readable markdown text.

        Parameters
        ----------
        url:
            The URL to fetch. Must start with ``http://`` or ``https://``.
        max_length:
            Maximum number of characters to return (default 8000).
        include_links:
            When True, hyperlinks are preserved in the markdown output (default False).

        Returns
        -------
        str
            Page content as markdown text, or an error message.
        """
        if not self._api_url:
            return "Web fetch is not available: EREBUS_AGENTIC_FETCH_URL is not set."

        if not url.startswith(("http://", "https://")):
            return f"Invalid URL: must start with http:// or https:// — got: {url}"

        max_len = max_length or self._max_length
        status, body = self._post("/fetch", {"url": url, "include_links": include_links})
        if status == 200:
            try:
                data = json.loads(body)
                content = data.get("markdown", data.get("content", data.get("text", body)))
                if isinstance(content, str):
                    if len(content) > max_len:
                        content = (
                            content[:max_len]
                            + f"\n\n[Content truncated at {max_len} characters.]"
                        )
                    return content
            except (json.JSONDecodeError, KeyError):
                pass
            # Plain text response
            if len(body) > max_len:
                body = (
                    body[:max_len]
                    + f"\n\n[Content truncated at {max_len} characters.]"
                )
            return body
        return f"Failed to fetch {url} ({status}): {body[:500]}"

    def grep_url(self, url: str, pattern: str, context_lines: int = 3) -> str:
        """Fetch a URL and grep its content for a regex pattern.

        Useful for quickly locating specific information within a page without
        reading the full content — e.g. checking docs for a flag, option, or
        code snippet.

        Parameters
        ----------
        url:
            The URL to search. Must start with ``http://`` or ``https://``.
        pattern:
            Regular expression pattern to search for (case-insensitive).
        context_lines:
            Number of lines to show before and after each match (default 3).

        Returns
        -------
        str
            Matching lines with context, or a message when no matches are found.
        """
        if not self._api_url:
            return "Web fetch is not available: EREBUS_AGENTIC_FETCH_URL is not set."

        if not url.startswith(("http://", "https://")):
            return f"Invalid URL: must start with http:// or https:// — got: {url}"

        # Warm the server-side cache first so /grep can find the page.
        fetch_status, fetch_body = self._post("/fetch", {"url": url})
        if fetch_status != 200:
            return f"Failed to fetch {url} ({fetch_status}): {fetch_body[:500]}"

        status, body = self._post("/grep", {
            "url": url,
            "pattern": pattern,
            "context_lines": context_lines,
            "ignore_case": True,
        })
        if status == 200:
            try:
                data = json.loads(body)
                return data.get("result", body)
            except (json.JSONDecodeError, KeyError):
                return body[:self._max_length]
        return f"Grep failed ({status}): {body[:500]}"
