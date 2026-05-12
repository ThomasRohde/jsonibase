# JsonIBase

Typed JSONL records with derived SQLite, FTS5, and built-in local embeddings.

JsonIBase turns local JSONL source files into a validated, searchable record base.
JSONL is the source of truth. SQLite is the derived local index.

## Quickstart

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
store.add("standards", Standard(id="std_001", title="Managed services", body="Prefer managed services.", status="active"))
results = store.search("standards", "managed services")
```

The CLI returns JSON envelopes by default:

```shell
jsonibase guide
```

## Boundaries

JsonIBase is VCS-neutral. Git workflows are external. The library does not
inspect Git state, create commits, create branches, open pull requests, call
GitHub APIs, or provide Git adapters.

## Embeddings

The standard package includes a bundled Model2Vec resource manifest and default
local embedding provider. The provider performs no network calls during normal
operation. Applications can pass a custom embedding provider to `JsonIBase.open`
when they need a domain-specific model or want to disable semantic behavior in
their own wrapper.

## Internet Ingestion Examples

Additional examples ingest public structured sources:

- `examples/ingest_peps.py` for Python PEP metadata.
- `examples/ingest_cisa_kev.py` for CISA Known Exploited Vulnerabilities.
- `examples/ingest_rfc_index.py` for the RFC Editor XML index.

See `docs/ingestion-sources.md` for the source catalog and run commands.
