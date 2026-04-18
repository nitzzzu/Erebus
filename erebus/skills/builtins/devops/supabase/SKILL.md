---
name: supabase
description: Supabase client tools for the CodeAgent — database CRUD, auth, storage, and edge functions
---

# Supabase — CodeAgent Tools

## Overview

This skill extends the CodeAgent with Supabase client functions.
Interact with Supabase projects directly — query Postgres, manage auth
users, upload files to storage, and invoke edge functions.

## Setup

Set environment variables:
- `SUPABASE_URL` — project URL (e.g. `https://xxx.supabase.co`)
- `SUPABASE_KEY` — anon or service_role key

## CodeAgent Functions

- `supa_query(table, select="*", filters=None, limit=100)` — query a table
- `supa_insert(table, data)` — insert row(s)
- `supa_update(table, data, match)` — update matching rows
- `supa_delete(table, match)` — delete matching rows
- `supa_rpc(function_name, params=None)` — call a Postgres function
- `supa_sql(query)` — run raw SQL (requires service_role key)
- `supa_storage_list(bucket)` — list files in a storage bucket
- `supa_storage_upload(bucket, path, file_path)` — upload a file
- `supa_storage_download(bucket, path)` — download a file

## Example

```python
# Query users table
users = supa_query("users", select="id,email,created_at", limit=10)
print(to_json(users))

# Insert a record
result = supa_insert("logs", {"action": "deploy", "status": "ok"})
print(result)

# Call an RPC function
result = supa_rpc("get_active_users", {"since": "2024-01-01"})
print(to_json(result))
```
