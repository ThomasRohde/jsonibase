# Python API

The public API is exported from `jsonibase` and centered on `JsonIBase.open()`.

```python
from jsonibase import CollectionSpec, JsonIBase
```

## Workspace

```python
store = JsonIBase.open(
    root=".",
    collections=[standards],
    index_path=".jsonibase/jsonibase.db",
    rebuild_policy="lazy",
)
```

Arguments:

| Argument | Default | Meaning |
|---|---|---|
| `root` | Required | Workspace root for relative source and index paths. |
| `collections` | Required | `CollectionSpec` objects describing each JSONL file. |
| `index_path` | `.jsonibase/jsonibase.db` | SQLite index path, relative to `root` unless absolute. |
| `rebuild_policy` | `lazy` | `lazy`, `eager`, or `manual` freshness behavior. |
| `embedding_provider` | Bundled Model2Vec provider | Custom provider implementing `EmbeddingProvider`. |
| `embeddings_enabled` | `True` | Set to `False` to disable vector behavior. |

## CollectionSpec

`CollectionSpec[TRecord]` connects a Pydantic model to a JSONL file:

```python
standards = CollectionSpec[Standard](
    name="standards",
    path="data/standards.jsonl",
    model=Standard,
    id_field="id",
    title_field="title",
    fts_fields=["title", "body"],
    embedding_fields=["title", "body"],
    filter_fields=["status", "owner"],
    sort_fields=["title"],
    redacted_fields=["internal_notes"],
)
```

Important fields:

| Field | Meaning |
|---|---|
| `name` | Logical collection name. Must match `^[A-Za-z][A-Za-z0-9_]*$`. |
| `path` | JSONL source path. Relative paths are resolved from `root`. |
| `model` | Pydantic model used to validate every line. |
| `id_field` | Record identity field. Defaults to `id`. |
| `title_field` | Optional field used for indexed title storage and FTS weighting. |
| `fts_fields` | Text fields included in SQLite FTS5 search. |
| `embedding_fields` | Fields encoded for vector search. Defaults to `fts_fields` during indexing when empty. |
| `filter_fields` | Fields allowed in equality filters. |
| `sort_fields` | Fields allowed by `list(..., sort=...)`. |
| `relationships` | Cross-collection referential checks. |
| `redacted_fields` | Fields redacted from search results and snippets. |

## Operations

| Method | Behavior |
|---|---|
| `init()` | Creates metadata directories and empty source files if missing. |
| `validate()` | Returns a `ValidationReport` for JSONL, schema, identity, and relationships. |
| `add(collection, record)` | Adds a new record and rejects duplicate ids. |
| `update(collection, record_id, patch)` | Patches one record and validates the final source. |
| `upsert(collection, record)` | Inserts or replaces a record by id. |
| `plan()` | Starts a `ChangePlan` for staged multi-operation changes. |
| `apply(plan)` | Applies a plan transactionally after validating staged files. |
| `get(collection, record_id)` | Reads one typed record from source or returns `None`. |
| `list(collection, filters=None, sort=None, limit=None, offset=0)` | Reads typed records from source. |
| `status()` | Compares the current source manifest with the manifest stored in SQLite. |
| `rebuild()` | Rebuilds the derived SQLite index from source files. |
| `search(collection, query, filters=None, top=10, mode="hybrid")` | Runs hybrid, FTS, or vector search. |
| `recover(auto=False)` | Reports or clears incomplete transaction journals. |

## Change plans

Use plans when you want to preview or group writes:

```python
plan = store.plan()
plan.upsert("standards", record)
preview = plan.preview()
result = store.apply(plan)
```

`preview` is a `ChangeSet` with record ids and operations. `result` is a
`ChangeResult` with the transaction id, changed files, and before/after payloads.

## Result models

The package exports:

| Model | Purpose |
|---|---|
| `ChangeSet` | Preview of planned changes. |
| `ChangeResult` | Applied mutation result. |
| `RecoveryReport` | Incomplete transaction report and recovery outcome. |
| `SearchQuery` | Structured query shape for application wrappers. |
| `SearchResult` | Search hit with score, record, source, snippet, and explanation. |
| `SourceManifest` | Fingerprints for current sources, config, and embeddings. |
| `ValidationFinding` | One validation issue. |
| `ValidationReport` | Collection of findings with an `ok` property. |
