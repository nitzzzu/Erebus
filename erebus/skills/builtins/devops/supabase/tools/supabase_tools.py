"""Supabase client tools for CodeAgent.

Requires environment variables:
    SUPABASE_URL  — project URL (e.g. https://xxx.supabase.co)
    SUPABASE_KEY  — anon or service_role key

Uses the Supabase REST API directly via urllib — no SDK dependency.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

_SUPA_URL = os.environ.get("SUPABASE_URL", "")
_SUPA_KEY = os.environ.get("SUPABASE_KEY", "")


def _supa_headers() -> dict[str, str]:
    return {
        "apikey": _SUPA_KEY,
        "Authorization": f"Bearer {_SUPA_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _supa_request(
    method: str,
    path: str,
    body: bytes | None = None,
    extra_headers: dict[str, str] | None = None,
) -> tuple[int, str]:
    """Make a request to the Supabase REST API."""
    if not _SUPA_URL or not _SUPA_KEY:
        return 0, "SUPABASE_URL and SUPABASE_KEY must be set."
    url = f"{_SUPA_URL}{path}"
    headers = _supa_headers()
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return 0, str(exc)


def supa_query(
    table: str,
    select: str = "*",
    filters: dict[str, str] | None = None,
    limit: int = 100,
) -> list[dict] | str:
    """Query a Supabase table via PostgREST.

    Parameters
    ----------
    table:
        Table name.
    select:
        Columns to select (PostgREST syntax).
    filters:
        Optional filters as ``{"column": "eq.value"}``.
    limit:
        Max rows to return.

    Returns
    -------
    list[dict] | str
        Query results or error.
    """
    params = [f"select={select}", f"limit={limit}"]
    if filters:
        for col, val in filters.items():
            params.append(f"{col}={val}")
    query_str = "&".join(params)
    status, body = _supa_request("GET", f"/rest/v1/{table}?{query_str}")
    if status == 200:
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return body[:2000]
    return f"Query failed ({status}): {body[:500]}"


def supa_insert(table: str, data: dict | list[dict]) -> str:
    """Insert row(s) into a Supabase table.

    Parameters
    ----------
    table:
        Table name.
    data:
        Row dict or list of row dicts.

    Returns
    -------
    str
        Inserted data or error.
    """
    body = json.dumps(data).encode("utf-8")
    status, resp = _supa_request("POST", f"/rest/v1/{table}", body=body)
    if status in (200, 201):
        return resp[:2000]
    return f"Insert failed ({status}): {resp[:500]}"


def supa_update(table: str, data: dict, match: dict[str, str]) -> str:
    """Update matching rows in a Supabase table.

    Parameters
    ----------
    table:
        Table name.
    data:
        Fields to update.
    match:
        Filter for which rows to update (e.g. ``{"id": "eq.123"}``).

    Returns
    -------
    str
        Updated data or error.
    """
    params = "&".join(f"{k}={v}" for k, v in match.items())
    body = json.dumps(data).encode("utf-8")
    status, resp = _supa_request(
        "PATCH", f"/rest/v1/{table}?{params}", body=body,
    )
    if status == 200:
        return resp[:2000]
    return f"Update failed ({status}): {resp[:500]}"


def supa_delete(table: str, match: dict[str, str]) -> str:
    """Delete matching rows from a Supabase table.

    Parameters
    ----------
    table:
        Table name.
    match:
        Filter (e.g. ``{"id": "eq.123"}``).

    Returns
    -------
    str
        Deleted data or error.
    """
    params = "&".join(f"{k}={v}" for k, v in match.items())
    status, resp = _supa_request("DELETE", f"/rest/v1/{table}?{params}")
    if status in (200, 204):
        return resp[:2000] or "Deleted."
    return f"Delete failed ({status}): {resp[:500]}"


def supa_rpc(function_name: str, params: dict | None = None) -> Any:
    """Call a Supabase/Postgres RPC function.

    Parameters
    ----------
    function_name:
        Function name.
    params:
        Function parameters.

    Returns
    -------
    Any
        Function result.
    """
    body = json.dumps(params or {}).encode("utf-8")
    status, resp = _supa_request(
        "POST", f"/rest/v1/rpc/{function_name}", body=body,
    )
    if status == 200:
        try:
            return json.loads(resp)
        except json.JSONDecodeError:
            return resp[:2000]
    return f"RPC failed ({status}): {resp[:500]}"


def supa_sql(query: str) -> str:
    """Run raw SQL via Supabase (requires service_role key).

    Parameters
    ----------
    query:
        SQL query string.

    Returns
    -------
    str
        Query results.
    """
    body = json.dumps({"query": query}).encode("utf-8")
    status, resp = _supa_request("POST", "/rest/v1/rpc/exec_sql", body=body)
    if status == 200:
        return resp[:5000]
    # Fallback: use pg_query if exec_sql not available
    return f"SQL failed ({status}): {resp[:500]}"


def supa_storage_list(bucket: str) -> list[dict] | str:
    """List files in a Supabase storage bucket.

    Parameters
    ----------
    bucket:
        Bucket name.

    Returns
    -------
    list[dict] | str
        File listing or error.
    """
    body = json.dumps({
        "prefix": "", "limit": 100, "offset": 0,
    }).encode("utf-8")
    status, resp = _supa_request(
        "POST", f"/storage/v1/object/list/{bucket}", body=body,
    )
    if status == 200:
        try:
            return json.loads(resp)
        except json.JSONDecodeError:
            return resp[:2000]
    return f"Storage list failed ({status}): {resp[:500]}"


def supa_storage_upload(
    bucket: str,
    path: str,
    file_path: str,
) -> str:
    """Upload a file to Supabase storage.

    Parameters
    ----------
    bucket:
        Bucket name.
    path:
        Object path in bucket.
    file_path:
        Local file path.

    Returns
    -------
    str
        Upload result.
    """
    try:
        with open(file_path, "rb") as f:
            data = f.read()
    except OSError as exc:
        return f"File read error: {exc}"

    encoded_path = urllib.request.quote(path, safe="/")
    status, resp = _supa_request(
        "POST", f"/storage/v1/object/{bucket}/{encoded_path}",
        body=data,
        extra_headers={"Content-Type": "application/octet-stream"},
    )
    if status in (200, 201):
        return f"Uploaded to {bucket}/{path}"
    return f"Upload failed ({status}): {resp[:500]}"


def supa_storage_download(bucket: str, path: str) -> bytes | str:
    """Download a file from Supabase storage.

    Parameters
    ----------
    bucket:
        Bucket name.
    path:
        Object path.

    Returns
    -------
    bytes | str
        File content or error string.
    """
    encoded_path = urllib.request.quote(path, safe="/")
    url = f"{_SUPA_URL}/storage/v1/object/{bucket}/{encoded_path}"
    req = urllib.request.Request(url, headers=_supa_headers())
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except Exception as exc:
        return f"Download error: {exc}"


# -- TOOLS dict: required export for CodeAgent skill tool loading --
TOOLS: dict[str, Any] = {
    "supa_query": supa_query,
    "supa_insert": supa_insert,
    "supa_update": supa_update,
    "supa_delete": supa_delete,
    "supa_rpc": supa_rpc,
    "supa_sql": supa_sql,
    "supa_storage_list": supa_storage_list,
    "supa_storage_upload": supa_storage_upload,
    "supa_storage_download": supa_storage_download,
}
