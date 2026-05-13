# SQLite Indexes

JsonIBase stores derived search state in SQLite. The default index path is
`.jsonibase/jsonibase.db`.

## What is stored

The index contains:

- One table per collection with the record id, canonical JSON payload, filter columns,
  optional embedding, source line number, and source line hash.
- An FTS5 table per collection when `fts_fields` are configured.
- A source manifest table recording source hashes, config fingerprint, embedding
  fingerprint, record counts, and build time.

The index can be deleted and rebuilt from JSONL sources:

```python
store.rebuild()
```

or:

```shell
jsonibase build --root . --collection standards --path data/standards.jsonl --fts title --fts body
```

## Freshness

`status()` returns an `IndexStatus`:

| Field | Meaning |
|---|---|
| `index_exists` | Whether the SQLite file exists. |
| `stale` | Whether the index should be rebuilt. |
| `reason` | `fresh`, `missing`, `invalid`, `source_changed`, `config_changed`, or `embedding_changed`. |
| `source_manifest` | Current source and configuration fingerprint. |
| `index_manifest` | Manifest stored in SQLite, when readable. |

## Rebuild policies

`JsonIBase.open(..., rebuild_policy="lazy")` is the default. Search rebuilds missing or
stale indexes before querying.

| Policy | Behavior |
|---|---|
| `lazy` | Rebuilds when search needs a fresh index. |
| `eager` | Accepted by the API and currently follows the same search-time rebuild path. |
| `manual` | Search raises `INDEX_STALE` when the index is stale. Call `rebuild()` yourself. |

## Tracking artifacts

JSONL files are source. SQLite files are derived. A common ignore policy is:

```text
.jsonibase/*.db
.jsonibase/*.db-wal
.jsonibase/*.db-shm
.jsonibase/locks/
.jsonibase/transactions/
```
