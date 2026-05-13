# Troubleshooting

## Search says the index is stale

With the default `lazy` rebuild policy, `search()` rebuilds stale indexes automatically.
With `manual`, call `store.rebuild()` or `jsonibase build` before searching.

Common stale reasons:

| Reason | Meaning |
|---|---|
| `missing` | The SQLite index file does not exist. |
| `invalid` | The index exists but cannot be read as a JsonIBase index. |
| `source_changed` | JSONL file content, size, hash, or record count changed. |
| `config_changed` | Collection configuration changed. |
| `embedding_changed` | Embedding provider fingerprint changed or embeddings were disabled/enabled. |

## Validation fails with `JSONL_BLANK_LINE`

Canonical JSONL cannot contain blank lines. Remove the blank line and rerun validation.

## Filters fail in search or list

Only fields declared in `filter_fields` or with CLI `--filter` can be filtered. Declare
the field consistently across init, build, status, list, and search.

## CLI JSON is hard to quote

In PowerShell, wrap JSON object arguments in single quotes:

```shell
jsonibase apply --root . --collection standards --path data/standards.jsonl --op upsert --record '{"id":"std_001","title":"Managed services"}'
```

## Vector search returns no results

Vector mode returns no results when embeddings are disabled. It can also return no
results when there are no indexed records with embeddings. Rebuild the index after
changing `embedding_fields` or the provider.

## A transaction recovery error blocks writes

Call `recover(auto=False)` to inspect incomplete transaction journals. If the journals
are safe to clear, call `recover(auto=True)`.

## FAQ

### Should I commit `.jsonibase/jsonibase.db`?

Usually no. JSONL files are the source of truth, and the SQLite index is derived. Commit
source files and rebuild the index locally or in CI.

### Does the default embedding provider call the network?

No. The default provider loads packaged Model2Vec files from the installed package.

### Is JsonIBase a Git or GitHub automation library?

No. Git workflows, pull requests, branches, and hosted APIs are intentionally outside
the package boundary.
