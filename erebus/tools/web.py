"""Agno Toolkit for web search and page fetching via the Agentic Fetch API.

Uses the self-hosted Agentic Fetch service:
https://github.com/nitzzzu/agentic-fetch

Configuration (env var):
    EREBUS_AGENTIC_FETCH_URL — base URL, e.g. ``http://localhost:3001``

When the URL is not configured, all tool calls return a descriptive error
so the agent can surface the issue to the user rather than failing silently.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
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
        self.register(self.fetch_url)

    def _get(self, path: str, params: dict) -> tuple[int, str]:
        if not self._api_url:
            return 0, "EREBUS_AGENTIC_FETCH_URL is not configured."
        qs = urllib.parse.urlencode(params)
        url = f"{self._api_url}{path}?{qs}"
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.status, resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8", errors="replace")
        except urllib.error.URLError as exc:
            return 0, str(exc.reason)
        except Exception as exc:
            return 0, str(exc)

    def search_web(self, query: str, max_results: int = 5) -> str:
        """Search the web for information.

        Parameters
        ----------
        query:
            The search query.
        max_results:
            Maximum number of results to return (default 5).

        Returns
        -------
        str
            JSON list of search results with title, url, and snippet, or an error message.
        """
        if not self._api_url:
            return "Web search is not available: EREBUS_AGENTIC_FETCH_URL is not set."

        status, body = self._get("/search", {"q": query, "limit": max_results})
        if status == 200:
            try:
                data = json.loads(body)
                results = data if isinstance(data, list) else data.get("results", data)
                if not results:
                    return "No results found."
                output_parts: list[str] = []
                for r in results[:max_results]:
                    title = r.get("title", "")
                    url = r.get("url", r.get("link", ""))
                    snippet = r.get("snippet", r.get("description", r.get("content", "")))
                    output_parts.append(f"**{title}**\n{url}\n{snippet}")
                return "\n\n".join(output_parts)
            except (json.JSONDecodeError, KeyError):
                return body[:self._max_length]
        return f"Search failed ({status}): {body[:500]}"

    def fetch_url(
        self,
        url: str,
        max_length: Optional[int] = None,
    ) -> str:
        """Fetch the content of a URL and return readable text.

        Parameters
        ----------
        url:
            The URL to fetch. Must start with ``http://`` or ``https://``.
        max_length:
            Maximum number of characters to return (default 8000).

        Returns
        -------
        str
            Page content as plain text, or an error message.
        """
        if not self._api_url:
            return "Web fetch is not available: EREBUS_AGENTIC_FETCH_URL is not set."

        if not url.startswith(("http://", "https://")):
            return f"Invalid URL: must start with http:// or https:// — got: {url}"

        max_len = max_length or self._max_length
        status, body = self._get("/fetch", {"url": url})
        if status == 200:
            try:
                data = json.loads(body)
                content = data.get("content", data.get("text", body))
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

