"""DuckDB analytics tools for CodeAgent.

Requires: pip install duckdb

Provides in-process SQL analytics on CSV, Parquet, and JSON files
without a server — perfect for data exploration and ETL.
"""

from __future__ import annotations

from typing import Any

# Lazy import — duckdb may not be installed
_db = None


def _get_db():
    """Get or create a session-scoped DuckDB connection."""
    global _db
    if _db is None:
        try:
            import duckdb
            _db = duckdb.connect(":memory:")
        except ImportError:
            raise RuntimeError(
                "duckdb is not installed. Run: pip install duckdb"
            )
    return _db


def duckdb_query(sql: str, params: list | None = None) -> list[dict]:
    """Run a SQL query and return results as a list of dicts.

    Parameters
    ----------
    sql:
        SQL query string.
    params:
        Optional query parameters.

    Returns
    -------
    list[dict]
        Query results.

    Examples
    --------
    >>> rows = duckdb_query("SELECT 1 as n, 'hello' as msg")
    >>> print(rows)
    [{'n': 1, 'msg': 'hello'}]
    """
    db = _get_db()
    try:
        if params:
            result = db.execute(sql, params)
        else:
            result = db.execute(sql)
        cols = [desc[0] for desc in result.description]
        return [dict(zip(cols, row)) for row in result.fetchall()]
    except Exception as exc:
        return [{"error": str(exc)}]


def duckdb_sql(sql: str) -> str:
    """Run a SQL query and return a formatted table string.

    Parameters
    ----------
    sql:
        SQL query.

    Returns
    -------
    str
        Formatted text table or error message.
    """
    rows = duckdb_query(sql)
    if not rows:
        return "(no results)"
    if "error" in rows[0] and len(rows[0]) == 1:
        return f"Error: {rows[0]['error']}"

    cols = list(rows[0].keys())
    # Calculate column widths
    widths = {c: len(c) for c in cols}
    for row in rows[:100]:
        for c in cols:
            widths[c] = max(widths[c], len(str(row.get(c, ""))))

    # Build table
    header = " | ".join(c.ljust(widths[c]) for c in cols)
    sep = "-+-".join("-" * widths[c] for c in cols)
    lines = [header, sep]
    for row in rows[:100]:
        lines.append(
            " | ".join(str(row.get(c, "")).ljust(widths[c]) for c in cols)
        )
    if len(rows) > 100:
        lines.append(f"... ({len(rows)} total rows, showing first 100)")
    return "\n".join(lines)


def duckdb_load_csv(path: str, table_name: str | None = None) -> str:
    """Load a CSV file into a DuckDB table.

    Parameters
    ----------
    path:
        Path to CSV file (supports glob patterns).
    table_name:
        Table name (auto-derived from filename if omitted).

    Returns
    -------
    str
        Confirmation with row count.
    """
    db = _get_db()
    if not table_name:
        from pathlib import Path as P
        table_name = P(path).stem.replace("-", "_").replace(" ", "_")
    try:
        db.execute(
            f"CREATE OR REPLACE TABLE {table_name} AS "
            f"SELECT * FROM read_csv_auto('{path}')"
        )
        count = db.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]
        return f"Loaded {count} rows into table '{table_name}'"
    except Exception as exc:
        return f"Error loading CSV: {exc}"


def duckdb_load_parquet(path: str, table_name: str | None = None) -> str:
    """Load a Parquet file into a DuckDB table.

    Parameters
    ----------
    path:
        Path to Parquet file (supports glob patterns).
    table_name:
        Table name.
    """
    db = _get_db()
    if not table_name:
        from pathlib import Path as P
        table_name = P(path).stem.replace("-", "_").replace(" ", "_")
    try:
        db.execute(
            f"CREATE OR REPLACE TABLE {table_name} AS "
            f"SELECT * FROM read_parquet('{path}')"
        )
        count = db.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]
        return f"Loaded {count} rows into table '{table_name}'"
    except Exception as exc:
        return f"Error loading Parquet: {exc}"


def duckdb_load_json(path: str, table_name: str | None = None) -> str:
    """Load a JSON/JSONL file into a DuckDB table.

    Parameters
    ----------
    path:
        Path to JSON file.
    table_name:
        Table name.
    """
    db = _get_db()
    if not table_name:
        from pathlib import Path as P
        table_name = P(path).stem.replace("-", "_").replace(" ", "_")
    try:
        db.execute(
            f"CREATE OR REPLACE TABLE {table_name} AS "
            f"SELECT * FROM read_json_auto('{path}')"
        )
        count = db.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]
        return f"Loaded {count} rows into table '{table_name}'"
    except Exception as exc:
        return f"Error loading JSON: {exc}"


def duckdb_tables() -> list[str]:
    """List all tables in the current DuckDB session.

    Returns
    -------
    list[str]
        Table names.
    """
    db = _get_db()
    rows = db.execute("SHOW TABLES").fetchall()
    return [r[0] for r in rows]


def duckdb_describe(table: str) -> str:
    """Describe a DuckDB table's schema.

    Parameters
    ----------
    table:
        Table name.

    Returns
    -------
    str
        Schema description.
    """
    return duckdb_sql(f"DESCRIBE {table}")


def duckdb_export_csv(sql: str, path: str) -> str:
    """Export query results to a CSV file.

    Parameters
    ----------
    sql:
        SQL query.
    path:
        Output file path.

    Returns
    -------
    str
        Confirmation.
    """
    db = _get_db()
    try:
        db.execute(f"COPY ({sql}) TO '{path}' (HEADER, DELIMITER ',')")
        return f"Exported to {path}"
    except Exception as exc:
        return f"Export error: {exc}"


# -- TOOLS dict: required export for CodeAgent skill tool loading --
TOOLS: dict[str, Any] = {
    "duckdb_query": duckdb_query,
    "duckdb_sql": duckdb_sql,
    "duckdb_load_csv": duckdb_load_csv,
    "duckdb_load_parquet": duckdb_load_parquet,
    "duckdb_load_json": duckdb_load_json,
    "duckdb_tables": duckdb_tables,
    "duckdb_describe": duckdb_describe,
    "duckdb_export_csv": duckdb_export_csv,
}
