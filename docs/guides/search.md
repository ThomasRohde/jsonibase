# Search

JsonIBase supports three search modes:

| Mode | Behavior |
|---|---|
| `fts` | SQLite FTS5 lexical search over `fts_fields`. |
| `vector` | Cosine similarity over stored local embeddings. |
| `hybrid` | Reciprocal-rank fusion of FTS and vector candidates. |

The default mode is `hybrid`.

## FTS behavior

FTS uses SQLite FTS5 with the `unicode61` tokenizer and diacritic removal. Query input is
tokenized and simplified before it reaches SQLite, so malformed FTS syntax such as
quoted fragments does not crash search.

JsonIBase plans FTS queries in this order:

1. `all_terms` using every token with prefix matching.
2. `adjacent_terms` pairs for longer queries.
3. `any_term` fallback with `OR`.

When `title_field` is also in `fts_fields`, title matches receive higher BM25 weight.

## Vector behavior

Vector search encodes the query with the configured provider and compares it to stored
record embeddings with cosine similarity. Embedding text is built from
`embedding_fields`; if they are empty, indexing falls back to `fts_fields`.

## Hybrid behavior

Hybrid search retrieves a larger candidate set from both FTS and vector search, combines
rankings with reciprocal-rank fusion, and returns the top results. Explanations include
the source ranks that contributed to the final score.

## Filters

Filters use equality expressions:

```python
store.search(
    "standards",
    "managed services",
    filters={"status": {"eq": "active"}},
)
```

Only fields declared in `filter_fields` can be used. Unsupported filter fields or
operators raise structured `JsonIBaseError` values.

The CLI equivalent is:

```shell
jsonibase search --root . --collection standards --path data/standards.jsonl --fts title --filter status --query "managed services" --filter-eq status=active
```

## Redaction

Fields listed in `redacted_fields` are replaced with `[REDACTED]` in search result
records and snippets. Source files still contain the original values.
