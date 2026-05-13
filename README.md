# JsonIBase

Typed JSONL records with derived SQLite, FTS5, and built-in local embeddings.

[![PyPI](https://img.shields.io/pypi/v/jsonibase.svg)](https://pypi.org/project/jsonibase/)
[![Python](https://img.shields.io/pypi/pyversions/jsonibase.svg)](https://pypi.org/project/jsonibase/)
[![CI](https://github.com/ThomasRohde/jsonibase/actions/workflows/ci.yml/badge.svg)](https://github.com/ThomasRohde/jsonibase/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

JsonIBase turns local JSONL source files into a validated, searchable record
base. JSONL is the source of truth. SQLite is the derived local index.

## Features

- Pydantic-backed collection specs for typed JSONL records.
- Canonical JSONL reads and transactional source mutations.
- Derived SQLite index with FTS5 lexical search.
- Bundled Model2Vec embedding provider for local vector and hybrid search.
- Validation for duplicate ids, schema errors, and relationships.
- JSON-only CLI designed for agents and scripts.
- No hosted service, database server, or network call required for normal use.

## Install

```shell
pip install jsonibase
```

Requires Python 3.13 or newer.

For development from a source checkout:

```shell
uv sync --extra dev
uv run pytest
uv run jsonibase guide
```

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
store.add(
    "standards",
    Standard(
        id="std_001",
        title="Managed services",
        body="Prefer managed services.",
        status="active",
    ),
)
results = store.search("standards", "managed services")
print(results[0].record_id)
```

## CLI

The CLI returns one pretty-printed JSON envelope per command. The guide is
machine-readable and intended to bootstrap agents like Codex:

```shell
jsonibase guide
```

Common workflow:

```shell
jsonibase init --root . --collection standards --path data/standards.jsonl --fts title --fts body
jsonibase validate --root . --collection standards --path data/standards.jsonl --fts title --fts body
jsonibase build --root . --collection standards --path data/standards.jsonl --fts title --fts body
jsonibase search --root . --collection standards --path data/standards.jsonl --fts title --fts body --query "managed services"
```

In a source checkout, prefix commands with `uv run`.

## Boundaries

JsonIBase is VCS-neutral. Git workflows are external. The library does not
inspect Git state, create commits, create branches, open pull requests, call
GitHub APIs, or provide Git adapters.

## Embeddings

The standard package includes a bundled Model2Vec resource manifest and default
local embedding provider. The provider performs no network calls during normal
operation. Applications can pass a custom provider to `JsonIBase.open` when
they need a domain-specific model or want to disable semantic behavior in their
own wrapper.

## Internet Ingestion Examples

Additional examples ingest public structured sources:

- `examples/ingest_peps.py` for Python PEP metadata.
- `examples/ingest_cisa_kev.py` for CISA Known Exploited Vulnerabilities.
- `examples/ingest_rfc_index.py` for the RFC Editor XML index.

See `docs/ingestion-sources.md` for the source catalog and run commands.

## Development

```shell
uv sync --extra dev
uv run ruff check src tests scripts
uv run pyright
uv run python scripts/verify_model_manifest.py
uv run pytest
uv run python -m build
uv run twine check dist/*
```

## Releasing

JsonIBase uses PyPI trusted publishing through
`.github/workflows/publish.yml`. The PyPI publisher must be configured for:

- Repository: `ThomasRohde/jsonibase`
- Workflow: `publish.yml`
- Environment: `pypi`

Cut a release from a clean tree:

```shell
python scripts/release.py 0.1.0
git push origin main v0.1.0
```

The tag triggers GitHub Actions to build, check, upload to PyPI, and create a
GitHub Release. After the release, open the next development cycle:

```shell
python scripts/release.py --post-release 0.2.0.dev0
git push origin main
```

## License

[MIT](LICENSE). The bundled `potion-base-8M` model declares MIT licensing in
its model card and is hash-pinned in `MODEL-MANIFEST.json`.
