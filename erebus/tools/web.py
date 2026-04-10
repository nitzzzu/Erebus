"""Agno Toolkit for fetching web page content.

Retrieves a URL and returns readable text (HTML stripped).  Useful for
reading documentation, pulling in reference material, or summarising
a web page without leaving the agent context.
"""

from __future__ import annotations

import html
import logging
import re
import urllib.error
import urllib.request
from typing import Optional

from agno.tools.toolkit import Toolkit

logger = logging.getLogger(__name__)

_DEFAULT_MAX_LENGTH = 8000
_USER_AGENT = (
    "Mozilla/5.0 (compatible; Erebus/1.0; +https://github.com/nitzzzu/Erebus)"
)


def _strip_html(raw_html: str) -> str:
    """Best-effort HTML → plain text conversion without dependencies."""
    # Remove <script> and <style> blocks entirely
    text = re.sub(
        r"<(script|style)[^>]*>.*?</(script|style)>",
        "",
        raw_html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    # Replace common block elements with newlines
    text = re.sub(r"</(p|div|li|h[1-6]|tr|br)[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode HTML entities
    text = html.unescape(text)
    # Collapse whitespace while preserving newlines
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    text = "\n".join(line for line in lines if line)
    # Collapse 3+ blank lines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


class WebFetchTools(Toolkit):
    """Agent tool for fetching and reading web page content."""

    def __init__(self, max_length: int = _DEFAULT_MAX_LENGTH) -> None:
        self._max_length = max_length
        super().__init__(name="web_fetch")
        self.register(self.fetch_url)

    def fetch_url(
        self,
        url: str,
        max_length: Optional[int] = None,
        raw: bool = False,
    ) -> str:
        """Fetch the content of a URL and return readable text.

        HTML pages are automatically converted to plain text.  Binary
        responses (images, PDFs, etc.) are not supported and will return
        an error message.

        Parameters
        ----------
        url:
            The URL to fetch.  Must start with ``http://`` or ``https://``.
        max_length:
            Maximum number of characters to return (default 8000).
        raw:
            If True, return the raw response body instead of stripped text.

        Returns
        -------
        str
            Page content (plain text) or an error message.
        """
        max_len = max_length or self._max_length
        if not url.startswith(("http://", "https://")):
            return f"Invalid URL: must start with http:// or https:// — got: {url}"

        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                content_type = resp.headers.get("Content-Type", "")
                text_types = (
                    "text/",
                    "application/json",
                    "application/xml",
                    "application/xhtml",
                )
                if not any(ct in content_type for ct in text_types):
                    return (
                        f"Unsupported content type: {content_type}"
                        " \u2014 only text content can be fetched."
                    )
                body_bytes = resp.read(max_len * 6)  # read more than needed before stripping
                charset = "utf-8"
                if "charset=" in content_type:
                    charset = content_type.split("charset=")[-1].split(";")[0].strip()
                body = body_bytes.decode(charset, errors="replace")
        except urllib.error.HTTPError as exc:
            return f"HTTP {exc.code} error fetching {url}: {exc.reason}"
        except urllib.error.URLError as exc:
            return f"Failed to fetch {url}: {exc.reason}"
        except TimeoutError:
            return f"Request to {url} timed out."
        except Exception as exc:
            return f"Error fetching {url}: {exc}"

        if raw or "text/html" not in content_type:
            text = body
        else:
            text = _strip_html(body)

        if len(text) > max_len:
            text = (
                text[:max_len]
                + f"\n\n[Content truncated at {max_len} characters."
                " Call with a higher max_length to read more.]"
            )

        return text
