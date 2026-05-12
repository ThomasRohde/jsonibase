# API

The primary API is `JsonIBase.open(root, collections, index_path, rebuild_policy)`.

Core operations:

- `init()` creates source files and metadata directories.
- `validate()` returns a `ValidationReport`.
- `add()`, `update()`, and `upsert()` mutate canonical JSONL through a staged transaction.
- `plan()` and `apply()` stage multiple operations and validate the final state before writing.
- `get()` and `list()` read typed records from source.
- `rebuild()` rebuilds the derived SQLite/WAL index.
- `status()` compares the index manifest with the current source manifest.
- `search()` runs FTS, vector, or hybrid search.
- `recover()` reports or clears incomplete transaction journals.

`CollectionSpec` defines the JSONL path, Pydantic model, ID field, searchable
fields, filter fields, relationships, redacted fields, and deletion policy.
