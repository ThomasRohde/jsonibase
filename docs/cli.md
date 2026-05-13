# CLI

The `jsonibase` command is generic and JSON-only. In a source checkout, run it
through `uv`:

```shell
uv run jsonibase guide
```

The installed command is:

```shell
jsonibase guide
```

## Output envelope

Every command writes one pretty-printed JSON document to stdout:

```json
{
  "command": "guide",
  "data": {
    "schema_version": 1
  },
  "ok": true
}
```

Errors use the same envelope with `ok: false` and a structured error:

```json
{
  "command": "search",
  "error": {
    "code": "FILTER_FIELD_NOT_CONFIGURED",
    "details": {
      "collection": "standards",
      "field": "status"
    },
    "message": "field 'status' is not configured for filtering"
  },
  "ok": false
}
```

Parse all stdout as one JSON document. The CLI does not emit JSON Lines.

## Common options

Collection commands accept these options:

| Option | Meaning |
|---|---|
| `--root` | Workspace root. Defaults to the current directory. |
| `--collection` | Logical collection name. |
| `--path` | JSONL source path, relative to `--root` unless absolute. |
| `--fts` | Repeatable text field included in FTS5 search. |
| `--embedding` | Repeatable field included in local embedding text. |
| `--filter` | Repeatable field allowed in `--filter-eq` expressions. |

Keep collection options consistent across `init`, `build`, `status`, and `search`.
Changing indexed fields changes the configuration fingerprint and makes the index stale.

## Commands

| Command | Purpose |
|---|---|
| `jsonibase guide` | Return the machine-readable CLI contract. |
| `jsonibase init` | Create metadata directories and the configured JSONL file if missing. |
| `jsonibase validate` | Validate JSONL syntax, schema, ids, and relationships. |
| `jsonibase build` | Rebuild the derived SQLite index. |
| `jsonibase status` | Report index freshness and stale reason. |
| `jsonibase search` | Search with hybrid FTS plus local embeddings. |
| `jsonibase get` | Read one source record by id. |
| `jsonibase list` | Read source records, optionally with equality filters. |
| `jsonibase plan` | Preview a source mutation without writing. |
| `jsonibase apply` | Apply a source mutation transactionally after validation. |

## Inspect and search

```shell
jsonibase init --root . --collection standards --path data/standards.jsonl --fts title --fts body --embedding title --embedding body --filter status
jsonibase validate --root . --collection standards --path data/standards.jsonl --fts title --fts body --embedding title --embedding body --filter status
jsonibase build --root . --collection standards --path data/standards.jsonl --fts title --fts body --embedding title --embedding body --filter status
jsonibase status --root . --collection standards --path data/standards.jsonl --fts title --fts body --embedding title --embedding body --filter status
jsonibase search --root . --collection standards --path data/standards.jsonl --fts title --fts body --embedding title --embedding body --filter status --query "managed services" --filter-eq status=active --top 5
```

`--filter-eq` uses `field=value` syntax and the field must also be declared with
`--filter`.

## Mutate

Preview a change:

```shell
jsonibase plan --root . --collection standards --path data/standards.jsonl --fts title --op upsert --record '{"id":"std_001","title":"Managed services"}'
```

Apply the same change:

```shell
jsonibase apply --root . --collection standards --path data/standards.jsonl --fts title --op upsert --record '{"id":"std_001","title":"Managed services"}'
```

Update one record:

```shell
jsonibase apply --root . --collection standards --path data/standards.jsonl --fts title --op update --id std_001 --patch '{"title":"Managed services standard"}'
```

Mutation operations are `add`, `update`, and `upsert`. Records and patches must be JSON
object strings.
