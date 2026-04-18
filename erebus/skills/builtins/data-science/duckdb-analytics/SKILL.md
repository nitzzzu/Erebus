---
name: duckdb-analytics
description: DuckDB in-process analytics tools for the CodeAgent — SQL on CSV/Parquet/JSON without a server
---

# DuckDB Analytics — CodeAgent Tools

## Overview

This skill extends the CodeAgent with DuckDB-powered data analytics functions.
DuckDB runs in-process — no server required.  Analyse CSV, Parquet, and JSON files
with SQL, run aggregations, and export results.

## Setup

```bash
pip install duckdb
```

## CodeAgent Functions

- `duckdb_query(sql, params=None)` — run a SQL query, return results as list of dicts
- `duckdb_sql(sql)` — run a SQL query, return formatted table string
- `duckdb_load_csv(path, table_name=None)` — load a CSV file into a temp table
- `duckdb_load_parquet(path, table_name=None)` — load a Parquet file
- `duckdb_load_json(path, table_name=None)` — load a JSON/JSONL file
- `duckdb_tables()` — list all tables in the current session
- `duckdb_describe(table)` — describe a table's schema
- `duckdb_export_csv(sql, path)` — export query results to CSV

## Example

```python
# Load and analyse a CSV
duckdb_load_csv("sales.csv", "sales")
results = duckdb_sql("""
    SELECT region, SUM(amount) as total, COUNT(*) as orders
    FROM sales
    GROUP BY region
    ORDER BY total DESC
""")
print(results)

# Direct query on file — no load needed
result = duckdb_sql("SELECT * FROM 'data/*.parquet' LIMIT 10")
print(result)
```
