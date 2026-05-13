# JSONL Sources

JSONL files are the canonical data store in JsonIBase. SQLite indexes, manifests, and
locks are derived or operational artifacts.

## Canonical format

Each record is one JSON object on one line:

```json
{"body":"Prefer managed services.","id":"std_001","status":"active","title":"Managed services"}
{"body":"Use exceptions for products that cannot be managed services.","id":"std_002","status":"draft","title":"Self-hosted exceptions"}
```

Rules enforced by the reader and validator:

| Rule | Error code |
|---|---|
| Blank lines are not allowed. | `JSONL_BLANK_LINE` |
| Each line must parse as JSON. | `JSONL_PARSE_ERROR` |
| Each line must validate against the collection model. | `JSONL_SCHEMA_ERROR` |
| Record ids must be unique inside a collection. | `DUPLICATE_ID` |

## Writes

`add()`, `update()`, `upsert()`, and `apply()` write canonical JSONL through a staged
transaction:

1. JsonIBase creates a transaction directory under `.jsonibase/transactions/`.
2. It writes staged source files.
3. It validates the staged workspace.
4. It replaces the target source file.
5. It removes the transaction directory.

If an incomplete journal is left behind, `recover(auto=False)` reports it and
`recover(auto=True)` clears it.

## Deterministic output

JsonIBase writes records with sorted JSON keys and one trailing newline per record. This
keeps diffs readable and makes source file hashes stable.

## Source manifests

`source_manifest()` fingerprints the current source files, collection configuration, and
embedding provider. The SQLite index stores the same manifest at build time so
`status()` can identify stale indexes.
