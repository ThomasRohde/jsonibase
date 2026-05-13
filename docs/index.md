# JsonIBase

JsonIBase turns typed JSONL files into a validated, searchable local record base. The
JSONL files remain the source of truth, while SQLite, FTS5, and bundled local
embeddings provide derived search indexes that can be rebuilt at any time.

Use JsonIBase when you want a small local data layer for tools, agents, examples, or
applications that need typed records, repeatable validation, and searchable text without
operating a service.

## What it provides

- Pydantic-backed collection specifications for typed JSONL records.
- Canonical JSONL reads and staged transactional mutations.
- A derived SQLite index with FTS5 lexical search.
- Local vector and hybrid search through the bundled Model2Vec provider.
- Validation for malformed JSONL, schema errors, duplicate ids, and relationships.
- A JSON-only CLI that is friendly to scripts and agents.
- No network call during normal use with the default embedding provider.

## Start here

- [Install JsonIBase](installation.md) in an application or source checkout.
- Follow the [quickstart](quickstart.md) to create a workspace, add records, and search.
- Use the [CLI reference](cli.md) for agent-friendly JSON command envelopes.
- Use the [Python API reference](api.md) for library integration.

## Core model

JsonIBase separates durable source data from derived indexes:

| Layer | Role | Typical location |
|---|---|---|
| JSONL source | Canonical records owned by your project | `data/*.jsonl` |
| Metadata | Locks and transaction journals | `.jsonibase/` |
| SQLite index | Derived search tables and source manifest | `.jsonibase/jsonibase.db` |

Because the SQLite database is derived, it can be ignored, deleted, and rebuilt from
the JSONL files and collection configuration.
