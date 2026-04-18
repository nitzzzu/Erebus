"""Built-in functions injected into CodeAgent execution environment.

These functions are available inside every ``run_code_agent`` code snippet as
plain Python calls.  They bridge the gap between "write Python logic" and
"interact with the OS / web / filesystem" so the LLM can chain operations
in a single code block instead of making many individual tool calls.

Security model
--------------
The CodeAgent runs in a subprocess with the **same privileges** as the
existing ``run_shell`` / ``run_python`` tools.  It is intended for local or
Docker-based deployments where the agent already has filesystem and network
access.  There is no AST sandbox — full Python is available.

State persistence
-----------------
A ``state`` dict is injected at the module level.  Values stored in
``state`` survive across multiple ``run_code_agent`` invocations within the
same session, enabling multi-step workflows.

Output contract
---------------
- Anything written to stdout via ``print()`` is captured.
- The special ``final_answer(value)`` function signals the result and
  stops execution (by raising ``_FinalAnswerSignal``).  The value is
  serialised and returned to the calling agent.
"""

from __future__ import annotations

import glob as _glob_mod
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import textwrap
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Sentinel for final_answer()
# ---------------------------------------------------------------------------

_AGENTIC_FETCH_URL: str | None = None  # set by the bootstrap wrapper
_WORKSPACE_PATH: str | None = None     # set by the bootstrap wrapper


class _FinalAnswerSignal(BaseException):
    """Raised by ``final_answer()`` to short-circuit execution."""

    def __init__(self, value: Any) -> None:
        self.value = value
        super().__init__(str(value))


def final_answer(value: Any = None) -> None:  # noqa: D401
    """Signal the final result of the code execution.

    Parameters
    ----------
    value:
        The result to return to the calling agent.  Can be any type —
        strings, dicts, lists, numbers, etc.  The value is serialised
        automatically.

    Raises
    ------
    _FinalAnswerSignal
        Always raised.  Caught by the outer executor.
    """
    raise _FinalAnswerSignal(value)


# ---------------------------------------------------------------------------
# Shell / process helpers
# ---------------------------------------------------------------------------

_DEFAULT_TIMEOUT = 60
_MAX_OUTPUT = 50_000


def bash(
    command: str,
    timeout: int = _DEFAULT_TIMEOUT,
    cwd: str | None = None,
) -> str:
    """Run a shell command and return its combined stdout/stderr.

    Parameters
    ----------
    command:
        Shell command string (passed to ``/bin/sh -c``).
    timeout:
        Max seconds to wait (default 60).
    cwd:
        Working directory.  Defaults to the active workspace or CWD.

    Returns
    -------
    str
        Combined output.

    Examples
    --------
    >>> files = bash("ls -la src/")
    >>> git_log = bash("git log --oneline -10")
    >>> bash("pip install requests")
    """
    run_cwd = cwd or _WORKSPACE_PATH or os.getcwd()
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=run_cwd,
        )
        out = result.stdout or ""
        err = result.stderr or ""
        combined = out
        if err.strip():
            combined += ("\n" if combined else "") + err
        if len(combined) > _MAX_OUTPUT:
            combined = (
                combined[:_MAX_OUTPUT]
                + f"\n[output truncated at {_MAX_OUTPUT} chars]"
            )
        return combined.strip() or f"(exited with code {result.returncode})"
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s."
    except Exception as exc:
        return f"Error: {exc}"


def python(code: str, timeout: int = _DEFAULT_TIMEOUT) -> str:
    """Run a Python script in a **separate** subprocess.

    Use this when you need isolation from the current execution context
    (e.g. running an untrusted snippet, or avoiding import side-effects).

    Parameters
    ----------
    code:
        Python source code.
    timeout:
        Max seconds (default 60).

    Returns
    -------
    str
        Combined stdout/stderr.
    """
    run_cwd = _WORKSPACE_PATH or os.getcwd()
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=run_cwd,
        )
        out = result.stdout or ""
        err = result.stderr or ""
        combined = out
        if err.strip():
            combined += ("\n" if combined else "") + err
        if len(combined) > _MAX_OUTPUT:
            combined = (
                combined[:_MAX_OUTPUT]
                + f"\n[output truncated at {_MAX_OUTPUT} chars]"
            )
        return combined.strip() or f"(exited with code {result.returncode})"
    except subprocess.TimeoutExpired:
        return f"Python execution timed out after {timeout}s."
    except Exception as exc:
        return f"Python error: {exc}"


# ---------------------------------------------------------------------------
# File system helpers
# ---------------------------------------------------------------------------


def _resolve(path: str) -> Path:
    """Resolve a path relative to the workspace or CWD."""
    p = Path(path).expanduser()
    if p.is_absolute():
        return p
    base = Path(_WORKSPACE_PATH) if _WORKSPACE_PATH else Path(os.getcwd())
    return (base / p).resolve()


def read_file(
    path: str,
    start_line: int | None = None,
    end_line: int | None = None,
) -> str:
    """Read a file's contents, optionally slicing by line numbers.

    Parameters
    ----------
    path:
        File path (absolute or relative to workspace).
    start_line:
        1-indexed first line to include (default: beginning).
    end_line:
        1-indexed last line to include (default: end of file).

    Returns
    -------
    str
        File contents (with line numbers if a range is given).

    Examples
    --------
    >>> content = read_file("src/main.py")
    >>> header = read_file("README.md", 1, 30)
    """
    fpath = _resolve(path)
    if not fpath.exists():
        return f"Error: file not found — {path}"
    if fpath.is_dir():
        return f"Error: path is a directory — {path}"
    try:
        text = fpath.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"Error reading {path}: {exc}"

    if start_line is not None or end_line is not None:
        lines = text.split("\n")
        s = max(1, start_line or 1)
        e = min(len(lines), end_line or len(lines))
        numbered = [f"{i:>5} | {lines[i - 1]}" for i in range(s, e + 1)]
        return "\n".join(numbered)
    return text


def write_file(path: str, content: str) -> str:
    """Write content to a file, creating parent directories as needed.

    Parameters
    ----------
    path:
        File path.
    content:
        Full file content.

    Returns
    -------
    str
        Confirmation message.

    Examples
    --------
    >>> write_file("output/report.md", "# Report\\n\\nDone.")
    """
    fpath = _resolve(path)
    try:
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(content, encoding="utf-8")
        return f"Written {len(content)} bytes to {path}"
    except OSError as exc:
        return f"Error writing {path}: {exc}"


def append_file(path: str, content: str) -> str:
    """Append content to an existing file.

    Parameters
    ----------
    path:
        File path.
    content:
        Text to append.

    Returns
    -------
    str
        Confirmation message.
    """
    fpath = _resolve(path)
    try:
        with fpath.open("a", encoding="utf-8") as f:
            f.write(content)
        return f"Appended {len(content)} bytes to {path}"
    except OSError as exc:
        return f"Error appending to {path}: {exc}"


def edit_file(path: str, old: str, new: str, count: int = 1) -> str:
    """Replace an exact string in a file (like str_replace).

    Parameters
    ----------
    path:
        File path.
    old:
        Exact text to find.
    new:
        Replacement text.
    count:
        How many occurrences to replace (default 1, -1 for all).

    Returns
    -------
    str
        Confirmation or error.

    Examples
    --------
    >>> edit_file("config.py", 'DEBUG = True', 'DEBUG = False')
    """
    fpath = _resolve(path)
    if not fpath.exists():
        return f"Error: file not found — {path}"
    try:
        text = fpath.read_text(encoding="utf-8")
    except OSError as exc:
        return f"Error reading {path}: {exc}"
    if old not in text:
        return f"Error: target string not found in {path}"
    updated = text.replace(old, new, count)
    n = text.count(old) if count == -1 else min(count, text.count(old))
    try:
        fpath.write_text(updated, encoding="utf-8")
    except OSError as exc:
        return f"Error writing {path}: {exc}"
    return f"Replaced {n} occurrence(s) in {path}"


def find_files(
    pattern: str,
    base_dir: str | None = None,
    max_results: int = 500,
) -> list[str]:
    """Find files matching a glob pattern (recursive).

    Parameters
    ----------
    pattern:
        Glob pattern (e.g. ``"**/*.py"``).
    base_dir:
        Base directory (defaults to workspace root).
    max_results:
        Max files to return.

    Returns
    -------
    list[str]
        List of relative file paths.

    Examples
    --------
    >>> py_files = find_files("**/*.py")
    >>> tests = find_files("**/test_*.py", "src/")
    """
    root = _resolve(base_dir) if base_dir else Path(
        _WORKSPACE_PATH or os.getcwd()
    )
    try:
        matches = sorted(root.glob(pattern))[:max_results]
    except Exception as exc:
        return [f"Error: {exc}"]
    result = []
    for m in matches:
        try:
            result.append(str(m.relative_to(root)))
        except ValueError:
            result.append(str(m))
    return result


def search_files(
    pattern: str,
    path: str | None = None,
    file_pattern: str | None = None,
    case_insensitive: bool = False,
    max_results: int = 200,
) -> str:
    """Search file contents for a regex pattern (like grep/ripgrep).

    Uses ``rg`` when available, falls back to ``grep -rP``.

    Parameters
    ----------
    pattern:
        Regex pattern.
    path:
        Directory or file to search (defaults to workspace root).
    file_pattern:
        Glob filter (e.g. ``"*.py"``).
    case_insensitive:
        Case-insensitive matching.
    max_results:
        Max matching lines.

    Returns
    -------
    str
        Matching lines in ``file:line:content`` format.

    Examples
    --------
    >>> results = search_files("def create_agent", file_pattern="*.py")
    >>> results = search_files("TODO|FIXME", case_insensitive=True)
    """
    search_dir = path or _WORKSPACE_PATH or os.getcwd()
    has_rg = shutil.which("rg") is not None

    if has_rg:
        cmd = ["rg", "--line-number", "--no-heading", "--color=never"]
        if case_insensitive:
            cmd.append("--ignore-case")
        if file_pattern:
            cmd.extend(["--glob", file_pattern])
        cmd.extend(["-m", str(max_results), "--", pattern, search_dir])
    else:
        cmd = ["grep", "-rnP"]
        if case_insensitive:
            cmd.append("-i")
        if file_pattern:
            cmd.extend(["--include", file_pattern])
        cmd.extend([pattern, search_dir])

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        output = result.stdout.strip()
        if not output:
            return f"No matches for '{pattern}'"
        return output
    except subprocess.TimeoutExpired:
        return "Search timed out."
    except Exception as exc:
        return f"Search error: {exc}"


def list_dir(path: str = ".") -> list[str]:
    """List directory contents.

    Parameters
    ----------
    path:
        Directory path (defaults to workspace root).

    Returns
    -------
    list[str]
        Sorted list of entries.
    """
    dpath = _resolve(path)
    if not dpath.is_dir():
        return [f"Error: not a directory — {path}"]
    try:
        return sorted(e.name for e in dpath.iterdir())
    except OSError as exc:
        return [f"Error: {exc}"]


# ---------------------------------------------------------------------------
# Web / HTTP helpers
# ---------------------------------------------------------------------------

_USER_AGENT = (
    "Mozilla/5.0 (compatible; Erebus-CodeAgent/1.0; "
    "+https://github.com/nitzzzu/Erebus)"
)


def _agentic_post(path: str, params: dict) -> tuple[int, str]:
    """POST to the Agentic Fetch API."""
    if not _AGENTIC_FETCH_URL:
        return 0, "Agentic Fetch API not configured (EREBUS_AGENTIC_FETCH_URL)."
    url = f"{_AGENTIC_FETCH_URL}{path}"
    body = json.dumps(params).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "User-Agent": _USER_AGENT,
            "Content-Type": "application/json",
        },
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


def search_web(
    query: str,
    max_results: int = 5,
    engine: str = "google",
) -> str:
    """Search the web using the Agentic Fetch API.

    Parameters
    ----------
    query:
        Search query string.
    max_results:
        Max results (default 5).
    engine:
        Search engine: ``google``, ``hackernews``, ``reddit``, ``github``.

    Returns
    -------
    str
        Formatted search results.

    Examples
    --------
    >>> results = search_web("Python asyncio tutorial")
    >>> hn = search_web("LLM agents", engine="hackernews")
    """
    status, body = _agentic_post(
        "/search",
        {"query": query, "engine": engine, "max_results": max_results},
    )
    if status == 200:
        try:
            data = json.loads(body)
            items = data if isinstance(data, list) else data.get("results", [])
            parts = []
            for r in items[:max_results]:
                title = r.get("title", "")
                url = r.get("url", r.get("link", ""))
                snippet = r.get(
                    "snippet", r.get("description", r.get("content", ""))
                )
                parts.append(f"**{title}**\n{url}\n{snippet}")
            return "\n\n".join(parts) or "No results found."
        except (json.JSONDecodeError, KeyError):
            return body[:8000]
    return f"Search failed ({status}): {body[:500]}"


def fetch_url(url: str, max_length: int = 8000) -> str:
    """Fetch a URL and return its content as readable markdown.

    Parameters
    ----------
    url:
        The URL to fetch (http:// or https://).
    max_length:
        Max characters to return.

    Returns
    -------
    str
        Page content as markdown, or error message.

    Examples
    --------
    >>> page = fetch_url("https://docs.python.org/3/library/json.html")
    """
    if _AGENTIC_FETCH_URL:
        status, body = _agentic_post(
            "/fetch", {"url": url, "include_links": False}
        )
        if status == 200:
            try:
                data = json.loads(body)
                content = data.get(
                    "markdown", data.get("content", data.get("text", body))
                )
                if isinstance(content, str):
                    if len(content) > max_length:
                        content = (
                            content[:max_length]
                            + f"\n\n[Truncated at {max_length} chars]"
                        )
                    return content
            except (json.JSONDecodeError, KeyError):
                pass
            return body[:max_length]
        return f"Fetch failed ({status}): {body[:500]}"

    # Fallback: direct urllib request
    req = urllib.request.Request(
        url, headers={"User-Agent": _USER_AGENT}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            if len(text) > max_length:
                text = (
                    text[:max_length]
                    + f"\n\n[Truncated at {max_length} chars]"
                )
            return text
    except Exception as exc:
        return f"Fetch error: {exc}"


def http_get(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """Perform a raw HTTP GET request.

    Parameters
    ----------
    url:
        Target URL.
    headers:
        Optional request headers.
    timeout:
        Request timeout in seconds.

    Returns
    -------
    dict
        ``{"status": int, "headers": dict, "body": str}``

    Examples
    --------
    >>> resp = http_get("https://api.github.com/repos/python/cpython")
    >>> print(resp["status"], resp["body"][:200])
    """
    req = urllib.request.Request(url, method="GET")
    req.add_header("User-Agent", _USER_AGENT)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return {
                "status": resp.status,
                "headers": dict(resp.headers),
                "body": body,
            }
    except urllib.error.HTTPError as exc:
        return {
            "status": exc.code,
            "headers": dict(exc.headers) if exc.headers else {},
            "body": exc.read().decode("utf-8", errors="replace"),
        }
    except Exception as exc:
        return {"status": 0, "headers": {}, "body": str(exc)}


def http_post(
    url: str,
    data: Any = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """Perform a raw HTTP POST request.

    Parameters
    ----------
    url:
        Target URL.
    data:
        Request body.  Dicts are auto-serialised as JSON.
    headers:
        Optional request headers.
    timeout:
        Request timeout in seconds.

    Returns
    -------
    dict
        ``{"status": int, "headers": dict, "body": str}``

    Examples
    --------
    >>> resp = http_post("https://httpbin.org/post", {"key": "value"})
    """
    if isinstance(data, (dict, list)):
        body_bytes = json.dumps(data).encode("utf-8")
        content_type = "application/json"
    elif isinstance(data, str):
        body_bytes = data.encode("utf-8")
        content_type = "text/plain"
    elif isinstance(data, bytes):
        body_bytes = data
        content_type = "application/octet-stream"
    else:
        body_bytes = b""
        content_type = "text/plain"

    req = urllib.request.Request(url, data=body_bytes, method="POST")
    req.add_header("User-Agent", _USER_AGENT)
    req.add_header("Content-Type", content_type)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp_body = resp.read().decode("utf-8", errors="replace")
            return {
                "status": resp.status,
                "headers": dict(resp.headers),
                "body": resp_body,
            }
    except urllib.error.HTTPError as exc:
        return {
            "status": exc.code,
            "headers": dict(exc.headers) if exc.headers else {},
            "body": exc.read().decode("utf-8", errors="replace"),
        }
    except Exception as exc:
        return {"status": 0, "headers": {}, "body": str(exc)}


# ---------------------------------------------------------------------------
# Data / text helpers
# ---------------------------------------------------------------------------


def parse_json(text: str) -> Any:
    """Parse a JSON string, returning the parsed object or an error string.

    Examples
    --------
    >>> data = parse_json('{"a": 1}')
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        return f"JSON parse error: {exc}"


def to_json(obj: Any, indent: int = 2) -> str:
    """Serialise an object to a JSON string.

    Examples
    --------
    >>> print(to_json({"name": "Erebus", "version": 1}))
    """
    return json.dumps(obj, indent=indent, default=str)


# ---------------------------------------------------------------------------
# Catalogue of all built-in names exposed to CodeAgent snippets
# ---------------------------------------------------------------------------

BUILTINS_CATALOG: dict[str, Any] = {
    # Shell / process
    "bash": bash,
    "python": python,
    # File system
    "read_file": read_file,
    "write_file": write_file,
    "append_file": append_file,
    "edit_file": edit_file,
    "find_files": find_files,
    "search_files": search_files,
    "list_dir": list_dir,
    # Web / HTTP
    "search_web": search_web,
    "fetch_url": fetch_url,
    "http_get": http_get,
    "http_post": http_post,
    # Data helpers
    "parse_json": parse_json,
    "to_json": to_json,
    # Control flow
    "final_answer": final_answer,
    # Re-exports of useful stdlib bits
    "Path": Path,
    "re": re,
    "json": json,
    "os": os,
    "glob": _glob_mod,
    "textwrap": textwrap,
    "shlex": shlex,
}
