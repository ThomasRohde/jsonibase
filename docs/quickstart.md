# Quickstart

This quickstart creates a local workspace with one typed collection backed by
`data/standards.jsonl`.

## Python workflow

```python
from pydantic import BaseModel

from jsonibase import CollectionSpec, JsonIBase


class Standard(BaseModel):
    id: str
    title: str
    body: str
    status: str


standards = CollectionSpec[Standard](
    name="standards",
    path="data/standards.jsonl",
    model=Standard,
    fts_fields=["title", "body"],
    embedding_fields=["title", "body"],
    filter_fields=["status"],
)

store = JsonIBase.open(".", [standards])
store.init()
store.add(
    "standards",
    Standard(
        id="std_001",
        title="Managed services",
        body="Prefer managed services where possible.",
        status="active",
    ),
)

report = store.validate()
assert report.ok

store.rebuild()
results = store.search("standards", "managed services")
print(results[0].record_id)
```

The record is written to canonical JSONL:

```json
{"body":"Prefer managed services where possible.","id":"std_001","status":"active","title":"Managed services"}
```

`store.rebuild()` creates the derived SQLite index. With the default lazy rebuild
policy, `store.search()` can also rebuild automatically when the index is missing or
stale.

## CLI workflow

The CLI works with generic records that include an `id` field. Every command returns one
pretty-printed JSON document.

```shell
jsonibase init --root . --collection standards --path data/standards.jsonl --fts title --fts body --embedding title --embedding body --filter status
jsonibase apply --root . --collection standards --path data/standards.jsonl --fts title --fts body --embedding title --embedding body --filter status --op upsert --record '{"id":"std_001","title":"Managed services","body":"Prefer managed services where possible.","status":"active"}'
jsonibase validate --root . --collection standards --path data/standards.jsonl --fts title --fts body --embedding title --embedding body --filter status
jsonibase build --root . --collection standards --path data/standards.jsonl --fts title --fts body --embedding title --embedding body --filter status
jsonibase search --root . --collection standards --path data/standards.jsonl --fts title --fts body --embedding title --embedding body --filter status --query "managed services"
```

In PowerShell, single quotes around the JSON record avoid escaping the inner quotes.

## Result shape

Search returns `SearchResult` objects with the record id, score, source record, match
source, optional snippet, and ranking explanation:

```json
{
  "collection": "standards",
  "record_id": "std_001",
  "score": 0.03278688524590164,
  "record": {
    "id": "std_001",
    "title": "Managed services",
    "body": "Prefer managed services where possible.",
    "status": "active"
  },
  "match_source": "hybrid",
  "snippet": "Managed services",
  "explanation": {
    "fts_rank": 1,
    "vector_rank": 1,
    "hybrid_candidate_depth": 100
  }
}
```
