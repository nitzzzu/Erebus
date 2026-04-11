"""Agno Toolkit for interacting with an Obsidian vault via the Local REST API.

Requires the `obsidian-local-rest-api` plugin:
https://github.com/coddingtonbear/obsidian-local-rest-api

Configuration (env vars):
    EREBUS_OBSIDIAN_API_URL  — base URL, e.g. ``https://localhost:27124``
    EREBUS_OBSIDIAN_API_KEY  — API key shown in the plugin settings
"""

from __future__ import annotations

import json
import logging
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

from agno.tools.toolkit import Toolkit

logger = logging.getLogger(__name__)


class ObsidianTools(Toolkit):
    """Agent tools for reading, searching, and writing Obsidian notes via the Local REST API."""

    def __init__(self, api_url: str, api_key: str) -> None:
        self._api_url = api_url.rstrip("/")
        self._api_key = api_key
        # The plugin uses a self-signed TLS cert by default — skip verification
        self._ssl_ctx = ssl.create_default_context()
        self._ssl_ctx.check_hostname = False
        self._ssl_ctx.verify_mode = ssl.CERT_NONE
        super().__init__(name="obsidian")
        self.register(self.list_notes)
        self.register(self.get_note)
        self.register(self.create_or_update_note)
        self.register(self.append_to_note)
        self.register(self.delete_note)
        self.register(self.search_notes)
        self.register(self.list_tags)

    # ── Internal helpers ──────────────────────────────────────────────────

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[bytes] = None,
        content_type: str = "application/json",
    ) -> tuple[int, str]:
        url = f"{self._api_url}{path}"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
        }
        if body is not None:
            headers["Content-Type"] = content_type
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, context=self._ssl_ctx, timeout=30) as resp:
                return resp.status, resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            body_txt = exc.read().decode("utf-8", errors="replace")
            return exc.code, body_txt
        except Exception as exc:
            return 0, str(exc)

    def _note_path(self, path: str) -> str:
        """Ensure path ends with .md."""
        if not path.endswith(".md"):
            path = path + ".md"
        return path

    # ── Tools ──────────────────────────────────────────────────────────────

    def list_notes(self, directory: str = "") -> str:
        """List notes in the Obsidian vault.

        Parameters
        ----------
        directory:
            Sub-directory to list (empty = vault root).

        Returns
        -------
        str
            JSON array of note paths, or an error message.
        """
        encoded = urllib.parse.quote(directory, safe="")
        path = f"/vault/{encoded}" if directory else "/vault/"
        status, body = self._request("GET", path)
        if status == 200:
            try:
                data = json.loads(body)
                files = data.get("files", [])
                return json.dumps(files, indent=2)
            except json.JSONDecodeError:
                return body
        return f"Error {status}: {body}"

    def get_note(self, note_path: str) -> str:
        """Read the content of a note.

        Parameters
        ----------
        note_path:
            Path to the note relative to the vault root (e.g. ``Folder/Note.md``).

        Returns
        -------
        str
            Note content (markdown), or an error message.
        """
        encoded = urllib.parse.quote(self._note_path(note_path), safe="")
        status, body = self._request("GET", f"/vault/{encoded}")
        if status == 200:
            return body
        return f"Error {status}: {body}"

    def create_or_update_note(self, note_path: str, content: str) -> str:
        """Create or fully replace a note.

        Parameters
        ----------
        note_path:
            Path to the note (e.g. ``Research/Topic.md``).
        content:
            Full markdown content for the note.

        Returns
        -------
        str
            Success message or error.
        """
        encoded = urllib.parse.quote(self._note_path(note_path), safe="")
        body = content.encode("utf-8")
        status, resp = self._request("PUT", f"/vault/{encoded}", body=body, content_type="text/markdown")
        if status in (200, 204):
            return f"Note '{note_path}' saved successfully."
        return f"Error {status}: {resp}"

    def append_to_note(self, note_path: str, content: str) -> str:
        """Append content to an existing note (or create it if absent).

        Parameters
        ----------
        note_path:
            Path to the note.
        content:
            Markdown text to append.

        Returns
        -------
        str
            Success message or error.
        """
        encoded = urllib.parse.quote(self._note_path(note_path), safe="")
        body = content.encode("utf-8")
        status, resp = self._request("POST", f"/vault/{encoded}", body=body, content_type="text/markdown")
        if status in (200, 204):
            return f"Content appended to '{note_path}'."
        return f"Error {status}: {resp}"

    def delete_note(self, note_path: str) -> str:
        """Delete a note from the vault.

        Parameters
        ----------
        note_path:
            Path to the note to delete.

        Returns
        -------
        str
            Success message or error.
        """
        encoded = urllib.parse.quote(self._note_path(note_path), safe="")
        status, resp = self._request("DELETE", f"/vault/{encoded}")
        if status in (200, 204):
            return f"Note '{note_path}' deleted."
        return f"Error {status}: {resp}"

    def search_notes(self, query: str, context_length: int = 200) -> str:
        """Search notes using Dataview-compatible simple search.

        Uses the ``/search/simple/`` endpoint of the Local REST API.

        Parameters
        ----------
        query:
            Text to search for across all notes.
        context_length:
            Characters of context to return around each match (default 200).

        Returns
        -------
        str
            JSON list of matches with filename and context, or an error message.
        """
        params = urllib.parse.urlencode({"query": query, "contextLength": context_length})
        status, body = self._request("POST", f"/search/simple/?{params}")
        if status == 200:
            try:
                results = json.loads(body)
                if not results:
                    return "No matching notes found."
                return json.dumps(results, indent=2)
            except json.JSONDecodeError:
                return body
        return f"Error {status}: {body}"

    def list_tags(self) -> str:
        """Return all tags used in the vault.

        Returns
        -------
        str
            JSON object mapping tag names to usage counts, or an error message.
        """
        status, body = self._request("GET", "/tags/")
        if status == 200:
            return body
        return f"Error {status}: {body}"
