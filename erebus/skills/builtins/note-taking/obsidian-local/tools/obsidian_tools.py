"""Obsidian Local REST API tools for CodeAgent.

Requires the Obsidian Local REST API plugin:
https://github.com/coddingtonbear/obsidian-local-rest-api

Environment variables:
    OBSIDIAN_API_URL  — e.g. https://127.0.0.1:27124
    OBSIDIAN_API_KEY  — API key from plugin settings
"""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from typing import Any

_API_URL = os.environ.get("OBSIDIAN_API_URL", "https://127.0.0.1:27124")
_API_KEY = os.environ.get("OBSIDIAN_API_KEY", "")

# Obsidian Local REST API uses self-signed certs by default
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE


def _request(
    method: str,
    path: str,
    body: bytes | None = None,
    content_type: str = "application/json",
) -> tuple[int, str]:
    """Make an HTTP request to the Obsidian API."""
    url = f"{_API_URL}{path}"
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {_API_KEY}")
    if body is not None:
        req.add_header("Content-Type", content_type)
    try:
        with urllib.request.urlopen(req, timeout=30, context=_SSL_CTX) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return 0, f"Obsidian API error: {exc}"


def obsidian_search(query: str, context_length: int = 100) -> str:
    """Full-text search across all Obsidian vault notes.

    Parameters
    ----------
    query:
        Search query string.
    context_length:
        Characters of surrounding context per match.

    Returns
    -------
    str
        Formatted search results.
    """
    params = json.dumps({
        "query": query, "contextLength": context_length,
    }).encode()
    status, body = _request("POST", "/search/simple/", params)
    if status == 200:
        try:
            results = json.loads(body)
            parts = []
            for r in results[:20]:
                fname = r.get("filename", "")
                matches = r.get("matches", [])
                ctx = "; ".join(
                    m.get("match", {}).get("content", "")[:200]
                    for m in matches[:3]
                )
                parts.append(f"**{fname}**: {ctx}")
            return "\n".join(parts) or "No results."
        except (json.JSONDecodeError, KeyError):
            return body[:2000]
    return f"Search failed ({status}): {body[:500]}"


def obsidian_read(path: str) -> str:
    """Read an Obsidian note by vault path.

    Parameters
    ----------
    path:
        Note path relative to vault root (e.g. ``"Projects/notes.md"``).

    Returns
    -------
    str
        Note content or error message.
    """
    encoded = urllib.request.quote(path, safe="")
    status, body = _request("GET", f"/vault/{encoded}")
    if status == 200:
        return body
    return f"Read failed ({status}): {body[:500]}"


def obsidian_write(path: str, content: str) -> str:
    """Create or overwrite an Obsidian note.

    Parameters
    ----------
    path:
        Note path (e.g. ``"Daily/2024-01-01.md"``).
    content:
        Full note content.

    Returns
    -------
    str
        Confirmation or error.
    """
    encoded = urllib.request.quote(path, safe="")
    status, body = _request(
        "PUT", f"/vault/{encoded}",
        body=content.encode("utf-8"),
        content_type="text/markdown",
    )
    if status in (200, 204):
        return f"Note saved: {path}"
    return f"Write failed ({status}): {body[:500]}"


def obsidian_append(path: str, content: str) -> str:
    """Append content to an existing Obsidian note.

    Parameters
    ----------
    path:
        Note path.
    content:
        Text to append.

    Returns
    -------
    str
        Confirmation or error.
    """
    encoded = urllib.request.quote(path, safe="")
    status, body = _request(
        "POST", f"/vault/{encoded}",
        body=content.encode("utf-8"),
        content_type="text/markdown",
    )
    if status in (200, 204):
        return f"Appended to: {path}"
    return f"Append failed ({status}): {body[:500]}"


def obsidian_list(folder: str = "/") -> list[str]:
    """List files in an Obsidian vault folder.

    Parameters
    ----------
    folder:
        Folder path (default: vault root).

    Returns
    -------
    list[str]
        File paths.
    """
    encoded = urllib.request.quote(folder.strip("/"), safe="")
    endpoint = f"/vault/{encoded}/" if encoded else "/vault/"
    status, body = _request("GET", endpoint)
    if status == 200:
        try:
            data = json.loads(body)
            return data.get("files", []) if isinstance(data, dict) else data
        except json.JSONDecodeError:
            return [body[:1000]]
    return [f"List failed ({status}): {body[:500]}"]


def obsidian_delete(path: str) -> str:
    """Delete an Obsidian note.

    Parameters
    ----------
    path:
        Note path.

    Returns
    -------
    str
        Confirmation or error.
    """
    encoded = urllib.request.quote(path, safe="")
    status, body = _request("DELETE", f"/vault/{encoded}")
    if status in (200, 204):
        return f"Deleted: {path}"
    return f"Delete failed ({status}): {body[:500]}"


# -- TOOLS dict: required export for CodeAgent skill tool loading --
TOOLS: dict[str, Any] = {
    "obsidian_search": obsidian_search,
    "obsidian_read": obsidian_read,
    "obsidian_write": obsidian_write,
    "obsidian_append": obsidian_append,
    "obsidian_list": obsidian_list,
    "obsidian_delete": obsidian_delete,
}
