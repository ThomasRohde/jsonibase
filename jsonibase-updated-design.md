
# Design Document: JsonIBase

**Status:** Updated greenfield design  
**Version:** 0.2  
**Date:** 2026-05-12  
**Working package name:** `jsonibase`  
**Project/brand name:** `JsonIBase`  
**Target runtime:** Python 3.13+  
**Primary pattern:** Canonical JSONL source files + derived local SQLite/WAL index + FTS5 + default vendored Model2Vec embeddings.

> JsonIBase is a local-first Python library for typed, searchable JSONL-backed records. It provides safe file-based persistence, validation, derived SQLite indexing, FTS5 keyword search, and default semantic search through a vendored small Model2Vec model. It deliberately contains **no Git or GitHub functionality**; version-control workflows are owned by applications that use the library.

---

## 1. Executive summary

JsonIBase should be a reusable Python 3.13 library for teams and agents that need a small, deterministic, local data substrate.

The core idea:

```text
Typed Python records
        ↓
Canonical JSONL source files
        ↓
Safe local mutation transaction
        ↓
Validation and integrity checks
        ↓
Derived SQLite index in WAL mode
        ↓
FTS5 keyword search + vendored Model2Vec semantic search
        ↓
Python API / optional agent-friendly CLI
```

The updated design has two deliberate changes:

1. **No Git functionality.**  
   JsonIBase should not inspect Git state, create commits, create branches, open pull requests, call GitHub APIs, or provide Git adapters. Users of the package can wrap JsonIBase with their own Git or GitHub workflow.

2. **Vendored Model2Vec is included by default.**  
   The standard install should include the small embedding model and its runtime dependencies. Hybrid search should work out of the box without optional embedding extras or model downloads.

The result is a cleaner, more reusable library: **a VCS-neutral JSONL record base with excellent local indexing and search**.

---

## 2. Naming

Use the exact brand spelling:

```text
Brand:          JsonIBase
Python package: jsonibase
CLI command:    jsonibase
Main class:     JsonIBase
```

Suggested tagline:

```text
Typed JSONL records with SQLite, FTS5, and built-in local embeddings.
```

Suggested README opening:

```markdown
# JsonIBase

Typed JSONL records with derived SQLite, FTS5, and built-in local embeddings.

JsonIBase turns local JSONL source files into a validated, searchable record base.
JSONL is the source of truth. SQLite is the derived local index.
```

Important naming note: `JsonIBase` uses the spelling supplied here. The lowercase import/package name should be `jsonibase`.

---

## 3. Problem statement

Many internal tools need persistent, searchable records without a server. They need:

- Durable local source files.
- Human-readable, diffable data.
- Strong typed validation.
- Safe local writes.
- Fast search.
- Optional structured CLI access.
- Deterministic behavior suitable for agents and CI.

They do not necessarily want the persistence library to own Git, GitHub, Confluence, cloud storage, or deployment workflows. JsonIBase should stay focused on the data substrate.

---

## 4. Goals

JsonIBase should provide:

1. A typed Python API for JSONL-backed record collections.
2. Canonical JSONL persistence.
3. Safe local write transactions.
4. Strong Pydantic v2 validation.
5. Multi-collection integrity validation.
6. Derived SQLite indexing with WAL mode.
7. FTS5 keyword search.
8. Default vendored Model2Vec embeddings.
9. Hybrid FTS/vector search.
10. Stable search explanations.
11. Source manifests and change manifests for external tooling.
12. Optional agent-friendly CLI.
13. Modern Python 3.13 typing, packaging, and testing.

---

## 5. Non-goals

JsonIBase should not provide:

- Git status checks.
- Git commits.
- Branch creation.
- Pull request creation.
- GitHub API calls.
- Cloud synchronization.
- Multi-machine replication.
- A hosted API server.
- A general-purpose database replacement.
- A vector database.
- LLM inference.
- Document ingestion or OCR.
- Domain-specific architecture-governance behavior.

The library can expose enough metadata for external Git workflows, but it must not implement them.

---

## 6. Design principles

### 6.1 JSONL is source of truth

JSONL files are the durable state. SQLite is derived state and can always be rebuilt.

### 6.2 VCS-neutral

JsonIBase should work in any directory. It should not care whether the directory is tracked by Git, Mercurial, Perforce, SharePoint sync, OneDrive, or no VCS at all.

### 6.3 Search works out of the box

The standard install includes the vendored small Model2Vec model. FTS and semantic search are available without extra install steps.

### 6.4 Deterministic by default

No hidden network calls. No implicit model downloads. No LLM calls. No nondeterministic serialization.

### 6.5 Safe mutation first

Writes should be planned, validated, applied through a safe transaction, and reported as structured before/after changes.

### 6.6 Excellent Python library first

The Python API is the primary interface. The CLI is useful but secondary.

### 6.7 Small, explicit extension points

Domain tools should extend through collection specs, validators, text extractors, ID providers, and custom embedding providers, not by modifying the core.

---

## 7. Recommended technology stack

### 7.1 Core runtime

| Concern | Recommendation | Notes |
|---|---|---|
| Runtime | Python 3.13+ | Clean modern baseline. |
| Project manager | `uv` | Fast lockfile and reproducible environments. |
| Build backend | `hatchling` | Stable and simple. |
| Layout | `src/` | Prevents accidental root imports. |
| Package typing | PEP 561 with `py.typed` | Required for downstream type checking. |

### 7.2 Required dependencies

Because the vendored model is now default, the standard install includes embedding runtime dependencies.

| Concern | Package | Required? |
|---|---|---:|
| Validation | `pydantic` v2 | Yes |
| JSON serialization | `orjson` | Yes |
| File locks | `portalocker` | Yes |
| Embedding runtime | `model2vec` | Yes |
| Numeric arrays | `numpy` | Yes |
| CLI | `typer`, `rich` | Optional extra unless the project decides the CLI should be standard |

### 7.3 Development dependencies

| Concern | Package |
|---|---|
| Testing | `pytest`, `pytest-cov` |
| Property-based testing | `hypothesis` |
| Benchmarks | `pytest-benchmark` |
| Lint/format | `ruff` |
| Static typing | `pyright` or `basedpyright` |
| Build/release | `build`, `twine`, `hatchling` |

Version floors in this document should be verified against current Python 3.13 compatibility before implementation.

---

## 8. Python 3.13 engineering standards

JsonIBase should use modern Python deliberately:

- Require Python 3.13+.
- Use strict static typing.
- Use `pathlib.Path` everywhere.
- Use `typing.Protocol` for provider abstractions.
- Use PEP 695-style generics where they improve clarity.
- Use `Self`, `Literal`, `TypeAlias`, `TypedDict`, and `@override` where appropriate.
- Use frozen dataclasses for small immutable internal value objects.
- Use Pydantic models for public data contracts.
- Use timezone-aware UTC timestamps.
- Use structured exceptions.
- Keep public return values serializable.
- Include `py.typed`.
- Run `ruff check`, `ruff format`, `pyright --strict`, and `pytest` in CI.

Example style:

```python
from pydantic import BaseModel
from typing import Protocol

class IdProvider(Protocol):
    def new_id(self) -> str:
        ...

class CollectionSpec[TRecord: BaseModel](BaseModel):
    name: str
    path: str
    model: type[TRecord]
    id_field: str
```

---

## 9. High-level architecture

```text
jsonibase
├── public API
│   ├── JsonIBase
│   ├── CollectionSpec
│   ├── SearchQuery
│   ├── SearchResult
│   ├── ChangeSet
│   ├── ValidationReport
│   └── SourceManifest
│
├── source layer
│   ├── canonical JSONL reader/writer
│   ├── atomic staged writes
│   ├── cross-platform locks
│   ├── transaction journal
│   └── recovery engine
│
├── validation layer
│   ├── Pydantic validation
│   ├── identity validation
│   ├── relationship validation
│   ├── custom validator plugins
│   └── security/redaction validators
│
├── index layer
│   ├── SQLite connection manager
│   ├── schema generator
│   ├── source manifest
│   ├── full rebuild engine
│   ├── FTS5 table builder
│   └── vector BLOB storage
│
├── embedding layer
│   ├── vendored Model2Vec provider
│   ├── custom provider protocol
│   ├── vector serialization
│   └── model fingerprinting
│
├── search layer
│   ├── FTS query planner
│   ├── vector search
│   ├── Reciprocal Rank Fusion
│   ├── filters
│   ├── snippets
│   └── explanations
│
├── integration surface
│   ├── changed file reports
│   ├── source manifests
│   ├── change manifests
│   └── no built-in Git behavior
│
└── optional CLI
    ├── guide
    ├── init
    ├── status
    ├── validate
    ├── build
    ├── search
    ├── get
    └── apply
```

---

## 10. Core abstractions

## 10.1 `CollectionSpec`

A collection is one typed JSONL file plus indexing configuration.

```python
from pydantic import BaseModel
from jsonibase import CollectionSpec

class Standard(BaseModel):
    id: str
    title: str
    body: str
    status: str
    owner: str
    tags: list[str]

standards = CollectionSpec[Standard](
    name="standards",
    path="data/standards.jsonl",
    model=Standard,
    id_field="id",
    title_field="title",
    fts_fields=["title", "body", "tags"],
    embedding_fields=["title", "body"],
    filter_fields=["status", "owner", "tags"],
)
```

The collection spec should support:

- Collection name.
- JSONL file path.
- Pydantic model.
- ID field.
- Optional title/display field.
- FTS fields.
- Embedding fields.
- Filter fields.
- Sort fields.
- Relationship declarations.
- Redacted fields.
- Field normalization.
- Collection-level validators.
- Optional deletion policy.

---

## 10.2 `JsonIBase`

`JsonIBase` is the main facade.

```python
from jsonibase import JsonIBase

store = JsonIBase.open(
    root=".",
    collections=[standards],
    index_path=".jsonibase/jsonibase.db",
    rebuild_policy="lazy",
)

store.add("standards", standard)
store.update("standards", standard.id, {"status": "active"})

results = store.search(
    collection="standards",
    query="managed services instead of self hosting",
    filters={"status": {"eq": "active"}},
    top=10,
)
```

Public operations:

| Operation | Purpose |
|---|---|
| `open` | Open an existing workspace. |
| `init` | Create configured source files and metadata directory. |
| `status` | Report source/index freshness and health. |
| `validate` | Validate JSONL and integrity rules. |
| `plan` | Create a mutation plan without writing. |
| `apply` | Apply a validated change set. |
| `add` | Add one record. |
| `update` | Patch one record. |
| `upsert` | Insert or replace by ID or key. |
| `get` | Retrieve one record. |
| `list` | List records with filters and stable sorting. |
| `search` | Search with FTS/vector/hybrid. |
| `rebuild` | Rebuild derived SQLite index. |
| `recover` | Recover or report incomplete local transactions. |
| `changed_files` | Return files changed by the latest mutation result. |

---

## 10.3 `ChangeSet`

A change set is the unit of safe mutation.

```python
with store.plan() as plan:
    plan.add("standards", standard)
    plan.update("standards", "std_001", {"status": "deprecated"})

preview = plan.preview()
result = store.apply(plan)
```

A change set contains:

- Change set ID.
- Base source manifest.
- Proposed record operations.
- Before/after records.
- Validation report.
- Expected source file hashes.
- Changed file list.
- Optional caller-supplied actor metadata.

A change set does not contain Git commit, branch, PR, or remote metadata.

---

## 10.4 `SourceManifest`

The source manifest is a deterministic fingerprint of source files, collection configuration, and embedding configuration.

```json
{
  "schema_version": "1.0",
  "collections": {
    "standards": {
      "path": "data/standards.jsonl",
      "sha256": "e3b0...",
      "size_bytes": 12345,
      "mtime_ns": 1770000000000000000,
      "record_count": 42
    }
  },
  "config_fingerprint": "sha256:...",
  "embedding_fingerprint": "sha256:..."
}
```

Used for:

- Stale index detection.
- Optimistic concurrency.
- Transaction validation.
- External integration.
- CI checks.
- Rebuild triggering.

---

## 11. Workspace layout

Recommended default:

```text
workspace/
├── data/
│   ├── standards.jsonl
│   ├── references.jsonl
│   └── links.jsonl
├── .jsonibase/
│   ├── config.toml
│   ├── jsonibase.db
│   ├── jsonibase.db-wal
│   ├── jsonibase.db-shm
│   ├── locks/
│   └── transactions/
└── ...
```

JsonIBase should not write `.gitignore` or assume `.jsonibase/` will be ignored. It can expose a recommended ignore pattern in documentation:

```text
.jsonibase/*.db
.jsonibase/*.db-wal
.jsonibase/*.db-shm
.jsonibase/locks/
.jsonibase/transactions/
```

The application or repository owner decides how to handle these files.

---

## 12. Canonical JSONL source design

Each line is one complete JSON object.

Rules:

- UTF-8.
- One JSON object per line.
- No blank lines in canonical output.
- Keys sorted deterministically.
- Datetimes in UTC ISO 8601.
- No NaN or Infinity.
- No comments.
- A final trailing newline.
- Stable ordering unless caller explicitly sorts differently.
- Arrays preserve semantic order unless configured as set-like fields.

Example:

```json
{"body":"Prefer managed services where possible.","id":"std_001","owner":"platform","status":"active","tags":["cloud","platform"],"title":"Prefer managed services"}
```

Canonical serialization should be owned by JsonIBase. Domain tools should not manually serialize records.

---

## 13. Local mutation and transaction design

## 13.1 Write process

Local writes use staging, validation, and atomic replacement:

```text
acquire lock
→ read source manifest
→ create staging area
→ copy affected source files to staging
→ apply proposed changes in staging
→ validate staged state
→ write transaction journal
→ fsync staged files
→ atomically replace changed files
→ fsync parent directories where supported
→ mark index stale or rebuild according to policy
→ clear transaction journal
→ release lock
```

### 13.2 Transaction journal

A transaction journal enables recovery from interrupted writes.

```json
{
  "transaction_id": "tx_20260512_101500_7f3a",
  "state": "prepared",
  "base_manifest": {},
  "target_manifest": {},
  "files": [
    {
      "path": "data/standards.jsonl",
      "old_sha256": "sha256:...",
      "new_sha256": "sha256:...",
      "staged_path": ".jsonibase/transactions/tx_.../standards.jsonl"
    }
  ]
}
```

On startup, JsonIBase should detect incomplete journals and return a structured recovery-required error unless explicitly configured to recover automatically.

### 13.3 Deletion policy

Default: deletion is forbidden unless configured.

```python
CollectionSpec(
    name="standards",
    path="data/standards.jsonl",
    model=Standard,
    id_field="id",
    deletion="forbid",  # "forbid" | "tombstone" | "hard"
)
```

Recommended default remains `forbid` because many use cases need auditability.

---

## 14. Validation design

## 14.1 Validation levels

| Level | Purpose |
|---|---|
| `syntax` | JSONL parses. |
| `schema` | Pydantic model validates. |
| `identity` | IDs are unique and valid. |
| `relationship` | Declared relationships point to existing records. |
| `semantic` | Caller-supplied domain validators. |
| `index` | Derived SQLite index matches source manifest. |
| `security` | Optional policy validators such as secrets or PII checks. |

### 14.2 Validator protocol

```python
from typing import Protocol

class Validator(Protocol):
    name: str

    def validate(self, context: ValidationContext) -> list[ValidationFinding]:
        ...
```

### 14.3 Validation finding

```json
{
  "level": "error",
  "code": "RELATION_TARGET_MISSING",
  "collection": "links",
  "record_id": "lnk_001",
  "message": "Link target does not exist",
  "details": {
    "target_collection": "standards",
    "target_id": "std_999"
  }
}
```

### 14.4 Mutation validation

Mutations must validate the staged final state, not only the incoming patch. This catches duplicate IDs, broken relationships, invalid derived state, and domain-level violations.

---

## 15. SQLite index design

## 15.1 SQLite responsibilities

SQLite stores:

- Mirrored record fields for filtering.
- Full JSON record bodies.
- FTS5 virtual tables.
- Embedding vectors as BLOBs.
- Source line metadata.
- Source manifest.
- Schema version.
- Build metadata.

SQLite does not own durable business state.

### 15.2 Connection setup

```python
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")
conn.execute("PRAGMA cache_size=-64000")
conn.execute("PRAGMA temp_store=MEMORY")
conn.execute("PRAGMA foreign_keys=ON")
conn.row_factory = sqlite3.Row
```

### 15.3 Generated table example

For collection `standards`:

```sql
CREATE TABLE ji_standards (
    id TEXT PRIMARY KEY,
    json TEXT NOT NULL,
    title TEXT,
    status TEXT,
    owner TEXT,
    tags TEXT,
    embedding BLOB,
    source_line INTEGER NOT NULL,
    source_sha256 TEXT NOT NULL
);

CREATE VIRTUAL TABLE ji_standards_fts USING fts5(
    title,
    body,
    tags,
    content='ji_standards',
    content_rowid='rowid',
    tokenize='unicode61 remove_diacritics 2'
);
```

### 15.4 Source manifest table

```sql
CREATE TABLE ji_source_manifest (
    collection TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    record_count INTEGER NOT NULL,
    config_fingerprint TEXT NOT NULL,
    embedding_fingerprint TEXT NOT NULL,
    built_at TEXT NOT NULL
);
```

### 15.5 Rebuild strategy

MVP should use full rebuild:

```text
load source files
→ validate
→ create temp SQLite file
→ create schema
→ insert records
→ populate FTS5
→ compute and store embeddings
→ write manifest
→ close temp DB
→ atomically replace old DB
```

Full rebuild is simpler and safer than incremental rebuild. Incremental rebuild can be a later optimization.

### 15.6 Rebuild policies

| Policy | Behavior |
|---|---|
| `eager` | Rebuild after each mutation. |
| `lazy` | Rebuild on next read if stale. |
| `manual` | Caller controls rebuild. |

Default: `lazy`.

---

## 16. Default vendored Model2Vec embedding design

## 16.1 Design change

Embedding support is no longer optional. The standard install includes:

- `model2vec`
- `numpy`
- The vendored model files
- A default provider

Search should use hybrid FTS/vector mode by default.

### 16.2 Model packaging

Recommended package layout:

```text
src/jsonibase/
├── __init__.py
├── py.typed
├── embeddings/
│   ├── __init__.py
│   ├── provider.py
│   └── model2vec.py
└── models/
    └── potion-base-8M/
        ├── config.json
        ├── model.safetensors
        ├── tokenizer.json
        └── MODEL-MANIFEST.json
```

`MODEL-MANIFEST.json` should include:

```json
{
  "name": "potion-base-8M",
  "provider": "model2vec",
  "dimension": 256,
  "files": {
    "config.json": "sha256:...",
    "model.safetensors": "sha256:...",
    "tokenizer.json": "sha256:..."
  },
  "license": "TO_BE_VERIFIED_BEFORE_RELEASE",
  "source": "TO_BE_VERIFIED_BEFORE_RELEASE"
}
```

Before release, model licensing and redistribution rights must be verified and documented.

### 16.3 Loading model resources

Use `importlib.resources` so the model works from wheels:

```python
from importlib.resources import files
from model2vec import StaticModel

def default_model_path() -> str:
    return str(files("jsonibase.models").joinpath("potion-base-8M"))

def load_default_model() -> StaticModel:
    return StaticModel.from_pretrained(default_model_path())
```

If `model2vec` cannot load from an importlib resource path in some packaging modes, copy the model resource to a managed cache directory on first use and fingerprint the copied files.

### 16.4 Embedding provider protocol

Even though the vendored model is default, custom providers should be supported.

```python
from typing import Protocol
import numpy as np
import numpy.typing as npt

class EmbeddingProvider(Protocol):
    name: str
    dimension: int
    fingerprint: str

    def embed_text(self, text: str) -> npt.NDArray[np.float32]:
        ...

    def embed_many(self, texts: list[str]) -> list[npt.NDArray[np.float32]]:
        ...
```

### 16.5 Default behavior

Default:

```python
store = JsonIBase.open(root=".", collections=[standards])
# Uses vendored Model2Vec provider automatically.
```

Opt-out:

```python
store = JsonIBase.open(
    root=".",
    collections=[standards],
    embedding_provider=None,
)
```

Custom provider:

```python
store = JsonIBase.open(
    root=".",
    collections=[standards],
    embedding_provider=my_enterprise_provider,
)
```

### 16.6 No network calls

JsonIBase must never download a model automatically. The vendored model is packaged with the wheel.

### 16.7 Embedding fingerprint

The index manifest should include:

- Provider name.
- Model name.
- Model file hashes.
- Embedding dimension.
- Embedding fields.
- Text normalization version.
- Provider code version if available.

Any change triggers rebuild.

---

## 17. Search design

## 17.1 Retrieval modes

| Mode | Description |
|---|---|
| `fts` | FTS5/BM25 keyword search. |
| `vector` | Cosine similarity over vendored model embeddings. |
| `hybrid` | Reciprocal Rank Fusion over FTS and vector rankings. |

Default: `hybrid`.

### 17.2 FTS query planning

The query planner should accept plain language and safely convert it to FTS5 syntax.

Requirements:

- Escape invalid syntax.
- Handle punctuation-heavy text.
- Support phrase queries.
- Support field boosts where configured.
- Return warnings if simplifying the query.
- Never crash because of malformed user input.

### 17.3 Vector search

Vectors are stored as `float32` BLOBs. At the expected scale, brute-force cosine similarity is acceptable.

Implementation:

```text
query text
→ default Model2Vec embedding
→ candidate row embeddings from SQLite
→ cosine similarity
→ top K vector ranking
```

### 17.4 Hybrid ranking

Use Reciprocal Rank Fusion:

```text
RRF_score(d) = Σ 1 / (k + rank_i(d))
```

Default `k = 60`.

### 17.5 Search result

```json
{
  "collection": "standards",
  "id": "std_001",
  "title": "Prefer managed services",
  "score": 0.033061,
  "relevance": "high",
  "match_sources": ["fts", "vector"],
  "snippet": "Prefer managed services where possible...",
  "explanation": {
    "fts_rank": 1,
    "vector_rank": 4,
    "rrf_k": 60,
    "embedding_provider": "model2vec:potion-base-8M"
  }
}
```

### 17.6 Filters

Support composable filters:

```python
results = store.search(
    collection="standards",
    query="event streaming",
    filters={
        "status": {"eq": "active"},
        "tags": {"any": ["platform", "messaging"]},
    },
)
```

Operators:

| Operator | Meaning |
|---|---|
| `eq` | Equal. |
| `neq` | Not equal. |
| `in` | Scalar is in list. |
| `any` | Any requested value exists in list field. |
| `all` | All requested values exist in list field. |
| `contains` | Text/list contains value. |
| `before` | Date/time before. |
| `after` | Date/time after. |
| `is_null` | Null check. |
| `not` | Negation wrapper. |

---

## 18. External integration surface

JsonIBase should make external Git/VCS workflows easy without implementing them.

### 18.1 What JsonIBase may expose

JsonIBase may return:

- Changed file paths.
- Before/after source manifests.
- Change set summaries.
- Validation reports.
- Stale index status.
- Suggested ignore patterns.
- Source file hashes.
- Canonical JSONL outputs.

### 18.2 What JsonIBase must not do

JsonIBase must not:

- Run `git`.
- Inspect `.git`.
- Check Git dirty state.
- Create commits.
- Create branches.
- Push.
- Pull.
- Merge.
- Rebase.
- Open PRs.
- Call GitHub, GitLab, Bitbucket, or Azure DevOps APIs.
- Include Git/GitHub optional extras.

### 18.3 External wrapper example

A consuming application can do:

```python
result = store.apply(change_set)

# External application code, not JsonIBase:
changed_files = result.changed_files
run_enterprise_git_workflow(changed_files)
```

JsonIBase’s role ends at the changed file list and source manifests.

---

## 19. Optional CLI design

The CLI is useful for CI, development, and agent workflows. It should not be required for library consumers unless the project decides to include it in the standard install.

Suggested command:

```bash
jsonibase
```

Commands:

```bash
jsonibase guide
jsonibase init
jsonibase status
jsonibase validate
jsonibase build
jsonibase search <collection> "<query>"
jsonibase get <collection> <id>
jsonibase list <collection>
jsonibase plan < changeset.json
jsonibase apply < changeset.json
```

No CLI command should mention Git.

### 19.1 CLI envelope

Every command returns one JSON envelope:

```json
{
  "schema_version": "1.0",
  "request_id": "req_20260512_101500_7f3a",
  "ok": true,
  "command": "jsonibase.search",
  "result": {
    "results": [],
    "total": 0
  },
  "warnings": [],
  "errors": [],
  "metrics": {
    "duration_ms": 42
  }
}
```

stdout should contain only structured JSON. Human diagnostics go to stderr.

---

## 20. Public API sketch

## 20.1 Open a workspace

```python
from jsonibase import JsonIBase, CollectionSpec

store = JsonIBase.open(
    root=".",
    collections=[standards],
    index_path=".jsonibase/jsonibase.db",
    rebuild_policy="lazy",
)
```

## 20.2 Add/update/upsert

```python
created = store.add("standards", standard)

updated = store.update(
    "standards",
    "std_001",
    {"status": "active"},
)

upserted = store.upsert("standards", standard)
```

## 20.3 Plan/apply

```python
with store.plan() as plan:
    plan.add("standards", standard)
    plan.update("standards", "std_002", {"status": "deprecated"})

preview = plan.preview()
result = store.apply(plan)

print(result.changed_files)
print(result.after_manifest)
```

## 20.4 Search

```python
results = store.search(
    collection="standards",
    query="managed services over self-hosted infrastructure",
    mode="hybrid",
    filters={"status": {"eq": "active"}},
    top=10,
    explain=True,
)
```

## 20.5 Validate

```python
report = store.validate()

if not report.ok:
    for finding in report.findings:
        print(finding.code, finding.message)
```

---

## 21. Error handling

## 21.1 Exception hierarchy

```text
JsonIBaseError
├── ConfigError
├── JsonlParseError
├── SchemaValidationError
├── IntegrityError
├── RecordNotFoundError
├── RecordAlreadyExistsError
├── LockTimeoutError
├── TransactionError
├── TransactionRecoveryRequiredError
├── IndexStaleError
├── IndexBuildError
├── SearchError
├── EmbeddingModelError
├── IoError
└── InternalError
```

No Git or GitHub error classes should exist.

### 21.2 Error object

All exceptions should expose:

- Stable code.
- Human message.
- Structured details.
- Retryability.
- Suggested action.

Example:

```json
{
  "code": "ERR_RECORD_ALREADY_EXISTS",
  "message": "Record already exists in collection 'standards'",
  "retryable": false,
  "suggested_action": "fix_input",
  "details": {
    "collection": "standards",
    "id": "std_001"
  }
}
```

### 21.3 Error codes

| Code | Meaning |
|---|---|
| `ERR_CONFIG_INVALID` | Invalid collection/config declaration. |
| `ERR_JSONL_PARSE` | Invalid JSONL syntax. |
| `ERR_SCHEMA_VALIDATION` | Pydantic validation failed. |
| `ERR_INTEGRITY` | Cross-record integrity failed. |
| `ERR_RECORD_NOT_FOUND` | Missing record ID. |
| `ERR_RECORD_ALREADY_EXISTS` | Duplicate record. |
| `ERR_LOCK_TIMEOUT` | Could not acquire write lock. |
| `ERR_TRANSACTION_RECOVERY_REQUIRED` | Incomplete transaction journal found. |
| `ERR_INDEX_STALE` | Index stale and rebuild disabled. |
| `ERR_INDEX_BUILD` | SQLite build failed. |
| `ERR_SEARCH_QUERY` | Query planning failed. |
| `ERR_EMBEDDING_MODEL` | Vendored model missing or invalid. |
| `ERR_IO` | Filesystem error. |
| `ERR_INTERNAL` | Library bug. |

---

## 22. Security and enterprise controls

### 22.1 No network by default

Core operations are offline. Since Git and GitHub are excluded, the standard library has no network reason to call out.

### 22.2 Model artifact governance

Because the vendored model is part of the standard install, release governance matters:

- Verify model license.
- Verify redistribution rights.
- Include model source and version.
- Include file hash manifest.
- Include model card or summary if available.
- Document model limitations.
- Add supply-chain scanning for model files where possible.

### 22.3 Secrets and PII

Provide optional validators:

- Secret scanning hook.
- PII detection hook.
- Redaction policy.
- Snippet redaction.
- Export redaction.

Example:

```python
CollectionSpec(
    name="people",
    path="data/people.jsonl",
    model=Person,
    id_field="id",
    redacted_fields=["email", "phone"],
)
```

### 22.4 Audit metadata

Mutation results should include:

- Change set ID.
- Base manifest.
- Target manifest.
- Changed files.
- Before/after records.
- Caller-supplied actor metadata.
- Timestamp.

No Git commit or PR metadata should be part of the core mutation result.

---

## 23. Performance targets

Initial target scale:

| Metric | Target |
|---|---:|
| Records per collection | 100 to 50,000 |
| JSONL read/validate | < 2s for 50k small records |
| Full rebuild without embeddings | < 10s for 50k small records |
| Full rebuild with embeddings | Depends on text volume; benchmark and publish |
| FTS search latency | < 100ms for 50k records |
| Hybrid search latency | < 500ms for 50k records with brute-force vectors |
| Mutation | < 500ms plus rebuild time |
| Default model load | < 1s target after warm cache |

Future optimizations:

- Incremental rebuild.
- Chunked embedding computation.
- Embedding cache keyed by record content hash.
- Vector pre-filtering.
- ANN integration if scale requires it.

---

## 24. Testing strategy

### 24.1 Unit tests

- Collection spec validation.
- JSONL parsing.
- Canonical serialization.
- Atomic writes.
- Lock behavior.
- Transaction journal recovery.
- Pydantic validation.
- Relationship validation.
- SQLite schema generation.
- FTS query planning.
- Embedding model loading.
- Vector serialization.
- RRF scoring.
- Filter evaluation.
- Error serialization.

### 24.2 Property-based tests

Use Hypothesis for:

- JSONL round trips.
- Add/update/upsert invariants.
- Manifest determinism.
- Rebuild equivalence.
- Filter equivalence between Python and SQLite.
- Transaction recovery edge cases.
- Canonical serialization stability.

### 24.3 Integration tests

- Full local workspace lifecycle.
- Multiple collections.
- Multi-file change set.
- Stale index rebuild.
- Search with default embeddings.
- Search with custom provider.
- Search with embeddings disabled.
- CLI envelope correctness.
- Interrupted transaction simulation.

### 24.4 Golden tests

Golden files for:

- Canonical JSONL.
- CLI envelopes.
- Validation findings.
- Search results.
- Search explanations.
- SQLite schema.
- Error payloads.

### 24.5 Performance tests

Benchmark:

- Full rebuild.
- Model load.
- Embedding computation.
- FTS search.
- Vector search.
- Hybrid search.
- Bulk import.
- Large JSONL validation.

---

## 25. Proposed project structure

```text
jsonibase/
├── pyproject.toml
├── README.md
├── LICENSE
├── uv.lock
├── src/
│   └── jsonibase/
│       ├── __init__.py
│       ├── py.typed
│       ├── api.py
│       ├── config.py
│       ├── errors.py
│       ├── models.py
│       ├── source/
│       │   ├── __init__.py
│       │   ├── jsonl.py
│       │   ├── atomic.py
│       │   ├── locks.py
│       │   ├── manifest.py
│       │   └── transaction.py
│       ├── validation/
│       │   ├── __init__.py
│       │   ├── engine.py
│       │   ├── findings.py
│       │   └── validators.py
│       ├── index/
│       │   ├── __init__.py
│       │   ├── sqlite.py
│       │   ├── schema.py
│       │   ├── builder.py
│       │   └── status.py
│       ├── embeddings/
│       │   ├── __init__.py
│       │   ├── provider.py
│       │   ├── model2vec.py
│       │   └── vectors.py
│       ├── search/
│       │   ├── __init__.py
│       │   ├── fts.py
│       │   ├── vector.py
│       │   ├── hybrid.py
│       │   ├── filters.py
│       │   └── snippets.py
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   ├── envelope.py
│       │   └── commands.py
│       └── models/
│           └── potion-base-8M/
│               ├── config.json
│               ├── model.safetensors
│               ├── tokenizer.json
│               └── MODEL-MANIFEST.json
└── tests/
    ├── conftest.py
    ├── test_jsonl.py
    ├── test_atomic.py
    ├── test_validation.py
    ├── test_index.py
    ├── test_embeddings.py
    ├── test_search.py
    ├── test_api.py
    └── test_cli.py
```

No `git/`, `github/`, or `vcs/` modules should exist in the package.

---

## 26. Proposed `pyproject.toml`

This is illustrative; version floors must be verified for Python 3.13 before implementation.

```toml
[project]
name = "jsonibase"
dynamic = ["version"]
description = "Typed JSONL records with SQLite, FTS5, and built-in local embeddings."
readme = "README.md"
requires-python = ">=3.13"
license = "MIT"
authors = [
  { name = "Thomas Klok Rohde" }
]
keywords = [
  "jsonl",
  "sqlite",
  "fts5",
  "search",
  "local-first",
  "embeddings",
  "agents",
]
classifiers = [
  "Development Status :: 3 - Alpha",
  "Intended Audience :: Developers",
  "License :: OSI Approved :: MIT License",
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3.13",
  "Typing :: Typed",
]

dependencies = [
  "pydantic>=2",
  "orjson>=3",
  "portalocker>=2",
  "numpy>=2",
  "model2vec>=0.3",
]

[project.optional-dependencies]
cli = [
  "typer>=0.12",
  "rich>=13",
]
dev = [
  "pytest>=8",
  "pytest-cov>=5",
  "hypothesis>=6",
  "pytest-benchmark>=4",
  "ruff>=0.6",
  "pyright>=1.1",
]

[project.scripts]
jsonibase = "jsonibase.cli.main:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.version]
path = "src/jsonibase/__init__.py"

[tool.hatch.build.targets.wheel]
packages = ["src/jsonibase"]
include = [
  "src/jsonibase/py.typed",
  "src/jsonibase/models/potion-base-8M/**",
]

[tool.ruff]
target-version = "py313"
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = [
  "E",
  "F",
  "W",
  "I",
  "UP",
  "B",
  "SIM",
  "RUF",
  "C4",
  "PIE",
]
ignore = []

[tool.pyright]
pythonVersion = "3.13"
typeCheckingMode = "strict"
include = ["src", "tests"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers --strict-config"
```

---

## 27. Work packages

## WP0 — Product boundary and naming

**Purpose:** Lock the clean scope: JsonIBase is VCS-neutral and includes default embeddings.

**Activities:**

- Confirm exact spelling: `JsonIBase`.
- Confirm package name: `jsonibase`.
- Remove Git/GitHub/VCS modules from the design.
- Define what integration metadata is allowed.
- Confirm default vendored Model2Vec strategy.
- Write architecture decision records.

**Deliverables:**

- Naming decision.
- Scope decision.
- Embedding packaging decision.
- Non-goal decision for Git/GitHub.

**Definition of done:**

- No built-in Git/GitHub behavior remains in the architecture.
- The standard install includes model2vec and the vendored model.
- The scope is domain-neutral.

**Dependencies:** None.

---

## WP1 — Python 3.13 project skeleton

**Purpose:** Create a high-quality modern Python package foundation.

**Activities:**

- Create `src/` layout.
- Add `pyproject.toml`.
- Configure `uv`.
- Add `py.typed`.
- Configure `ruff`.
- Configure strict `pyright`.
- Configure `pytest`.
- Add CI.
- Add package-data inclusion for model files.

**Deliverables:**

- Installable package.
- Working wheel build.
- CI pipeline.
- Basic README.
- Developer setup guide.

**Definition of done:**

- `uv sync` works.
- Wheel includes `py.typed`.
- Wheel includes the vendored model files.
- `ruff`, `pyright`, and `pytest` pass.

**Dependencies:** WP0.

---

## WP2 — Collection specification and configuration

**Purpose:** Implement typed collection declarations.

**Activities:**

- Implement `CollectionSpec`.
- Implement `JsonIBaseConfig`.
- Implement field options.
- Implement config fingerprinting.
- Support Python-defined specs.
- Optionally support TOML loading.
- Validate invalid specs.

**Deliverables:**

- `jsonibase.config`
- Collection schema documentation.
- Config fingerprint function.
- Tests for valid and invalid specs.

**Definition of done:**

- Multiple Pydantic-backed collections can be declared.
- Config fingerprint changes when relevant options change.
- Invalid specs fail with structured errors.

**Dependencies:** WP1.

---

## WP3 — Canonical JSONL engine

**Purpose:** Implement source-of-truth persistence.

**Activities:**

- Implement JSONL reader.
- Implement canonical writer.
- Implement parse diagnostics.
- Implement line number tracking.
- Implement deterministic serialization.
- Implement property-based round-trip tests.

**Deliverables:**

- `jsonibase.source.jsonl`
- JSONL parse error model.
- Canonical serialization rules.
- Golden test files.

**Definition of done:**

- JSONL output is deterministic.
- Invalid lines report file and line.
- Valid records round-trip without semantic changes.

**Dependencies:** WP2.

---

## WP4 — Atomic local mutation and transaction journal

**Purpose:** Make writes safe and recoverable.

**Activities:**

- Implement cross-platform lock.
- Implement staging area.
- Implement transaction journal.
- Implement atomic replacement.
- Implement recovery detection.
- Implement before/after change records.
- Implement changed-file reporting.

**Deliverables:**

- `jsonibase.source.atomic`
- `jsonibase.source.locks`
- `jsonibase.source.transaction`
- `ChangeSet`
- `ChangeResult`

**Definition of done:**

- Concurrent writes are serialized or fail clearly.
- Interrupted transactions are detected.
- Multi-file mutations are staged and validated.
- Mutation results include changed files and manifests.

**Dependencies:** WP3.

---

## WP5 — Validation engine

**Purpose:** Validate source and staged states.

**Activities:**

- Implement validation context.
- Implement syntax/schema/identity checks.
- Implement relationship checks.
- Implement validator protocol.
- Implement structured validation reports.
- Add severity levels.

**Deliverables:**

- `jsonibase.validation`
- `ValidationReport`
- `ValidationFinding`
- Validator protocol.

**Definition of done:**

- `store.validate()` returns structured findings.
- Mutations validate staged final state.
- Domain validators can be plugged in.

**Dependencies:** WP4.

---

## WP6 — SQLite index foundation

**Purpose:** Build reliable derived SQLite indexes.

**Activities:**

- Implement SQLite connection setup.
- Implement generated table schema.
- Implement manifest table.
- Implement stale detection.
- Implement full rebuild to temp DB.
- Implement atomic DB replacement.
- Implement index status API.

**Deliverables:**

- `jsonibase.index.sqlite`
- `jsonibase.index.schema`
- `jsonibase.index.builder`
- `JsonIBase.rebuild()`
- `JsonIBase.status()`

**Definition of done:**

- Index rebuilds from JSONL.
- Stale/missing index is detected.
- Config changes trigger rebuild.
- Rebuild cannot corrupt source files.

**Dependencies:** WP5.

---

## WP7 — Vendored Model2Vec default provider

**Purpose:** Make semantic embeddings work in the standard install.

**Activities:**

- Add vendored model files.
- Add model manifest and hashes.
- Implement default provider.
- Implement model loading through package resources.
- Implement fingerprinting.
- Implement vector serialization.
- Add model packaging tests.

**Deliverables:**

- `jsonibase.embeddings.model2vec`
- `MODEL-MANIFEST.json`
- Embedding provider protocol.
- Default provider tests.

**Definition of done:**

- `JsonIBase.open()` can load the default model.
- Embeddings work without extra install steps.
- No network calls occur.
- Model fingerprint appears in the index manifest.

**Dependencies:** WP1, WP6.

---

## WP8 — FTS5 keyword search

**Purpose:** Provide robust lexical search.

**Activities:**

- Create FTS5 virtual tables.
- Populate configured FTS fields.
- Implement query planner.
- Implement FTS escaping/simplification.
- Implement snippets.
- Test malformed queries.

**Deliverables:**

- `jsonibase.search.fts`
- FTS query planner.
- FTS result model.
- Query warning model.

**Definition of done:**

- Plain-language FTS works.
- Malformed text does not crash search.
- Results are deterministic.
- Snippets are useful and redaction-aware.

**Dependencies:** WP6.

---

## WP9 — Vector and hybrid search

**Purpose:** Combine default semantic search with FTS.

**Activities:**

- Implement vector search.
- Implement cosine similarity.
- Implement Reciprocal Rank Fusion.
- Implement search explanations.
- Implement relevance labels.
- Add benchmarks.

**Deliverables:**

- `jsonibase.search.vector`
- `jsonibase.search.hybrid`
- `SearchQuery`
- `SearchResult`

**Definition of done:**

- Hybrid search is the default.
- Results identify FTS/vector match sources.
- Embeddings can be disabled explicitly.
- Custom providers can replace the default provider.

**Dependencies:** WP7, WP8.

---

## WP10 — Filter and listing engine

**Purpose:** Provide reliable structured retrieval.

**Activities:**

- Implement filter expression model.
- Implement scalar/list/date operators.
- Implement stable sorting.
- Implement pagination or cursor model.
- Ensure filter behavior is consistent across list/search.

**Deliverables:**

- `jsonibase.search.filters`
- `ListQuery`
- Filter expression tests.
- Pagination model.

**Definition of done:**

- Filters work across configured fields.
- Result ordering is stable.
- Filtering behavior is documented and tested.

**Dependencies:** WP6, WP9.

---

## WP11 — Main `JsonIBase` facade

**Purpose:** Provide the clean high-level API.

**Activities:**

- Implement `JsonIBase.open`.
- Implement `init`, `status`, `validate`, `rebuild`, `recover`.
- Implement `get`, `list`, `add`, `update`, `upsert`.
- Implement `plan` and `apply`.
- Implement rebuild policies.
- Wire structured exceptions.

**Deliverables:**

- `jsonibase.api`
- Public API documentation.
- End-to-end integration tests.
- Example domain adapter.

**Definition of done:**

- Consumers can use JsonIBase without importing low-level modules.
- Mutation, validation, rebuild, and search work end to end.
- Bulk operations can avoid repeated rebuilds.

**Dependencies:** WP4, WP5, WP9, WP10.

---

## WP12 — Optional CLI

**Purpose:** Provide a generic agent-friendly CLI without Git behavior.

**Activities:**

- Implement Typer CLI.
- Implement JSON envelope.
- Implement `guide`.
- Implement `init`, `status`, `validate`, `build`.
- Implement `search`, `get`, `list`.
- Implement `plan`, `apply`.
- Implement exit-code mapping.
- Add CLI tests.

**Deliverables:**

- `jsonibase` console script.
- CLI guide schema.
- Stable response envelope.
- CLI examples.

**Definition of done:**

- Every command returns one structured envelope.
- stdout is JSON-only by default.
- Errors are structured and stable.
- No command has Git/GitHub behavior.

**Dependencies:** WP11.

---

## WP13 — Security, redaction, and policy hooks

**Purpose:** Add enterprise-grade policy controls without hard-coding enterprise policy.

**Activities:**

- Implement redacted fields.
- Implement snippet redaction.
- Add validator examples for secrets/PII.
- Add protected collection policies.
- Add audit metadata support.
- Document safe configuration.

**Deliverables:**

- Redaction policy model.
- Security validator examples.
- Audit metadata model.
- Tests for redacted search/list output.

**Definition of done:**

- Sensitive fields do not leak in snippets.
- Validators can block writes.
- Mutation results include caller-supplied audit metadata.

**Dependencies:** WP11.

---

## WP14 — Documentation, examples, and release readiness

**Purpose:** Make JsonIBase usable by other projects.

**Activities:**

- Write README.
- Write quickstart.
- Write API reference.
- Write CLI reference.
- Write embedding model guide.
- Write external integration guide.
- Add example project.
- Add release checklist.
- Document model license and hashes.

**Deliverables:**

- Markdown documentation.
- Example package.
- Release checklist.
- First alpha release.

**Definition of done:**

- A new developer can create a searchable JSONL-backed collection in under 15 minutes.
- Docs explicitly state that Git is external.
- Docs explain bundled model behavior and opt-out.

**Dependencies:** WP12, WP13.

---

## 28. Milestone plan

### Milestone 1 — Local source and validation

Includes WP0 to WP5.

Outcome: typed JSONL source files, canonical persistence, safe mutation, validation, and change manifests.

### Milestone 2 — SQLite and default embeddings

Includes WP6 and WP7.

Outcome: derived SQLite index plus standard-install Model2Vec embeddings.

### Milestone 3 — Search

Includes WP8 to WP10.

Outcome: FTS, vector, hybrid search, filters, snippets, and explanations.

### Milestone 4 — Public API and CLI

Includes WP11 and WP12.

Outcome: clean Python facade plus optional agent-friendly CLI.

### Milestone 5 — Enterprise controls and release

Includes WP13 and WP14.

Outcome: redaction, policy hooks, docs, example project, and alpha release.

---

## 29. Recommended implementation sequence

1. Lock naming, non-goals, and model packaging decision.
2. Create Python 3.13 skeleton.
3. Add vendored model files and packaging tests early.
4. Implement collection specs.
5. Implement canonical JSONL.
6. Implement atomic transactions.
7. Implement validation.
8. Implement SQLite rebuild and manifest.
9. Implement default embedding provider.
10. Implement FTS search.
11. Implement vector search.
12. Implement hybrid search and filters.
13. Implement the `JsonIBase` facade.
14. Implement optional CLI.
15. Implement security/redaction hooks.
16. Write docs and release checklist.

Putting model packaging early is important because vendored model inclusion affects wheel size, licensing, CI, distribution, and import-resource behavior.

---

## 30. Acceptance criteria for first alpha

The first alpha should satisfy:

- Package name is `jsonibase`.
- Python 3.13+ package builds with `uv`.
- Wheel includes `py.typed`.
- Wheel includes the vendored Model2Vec model.
- Standard install includes embedding runtime dependencies.
- No Git, GitHub, or VCS module exists.
- `JsonIBase.open()` supports at least one typed collection.
- JSONL files are canonical and deterministic.
- Add/update/upsert work through safe local transactions.
- Validation catches parse, schema, duplicate ID, and relationship errors.
- SQLite index rebuilds from JSONL.
- FTS search works.
- Default semantic search works without extra install.
- Hybrid search works by default.
- Search results include match source and explanation.
- Embeddings can be disabled explicitly.
- Custom embedding providers can be supplied.
- Optional CLI supports `guide`, `validate`, `build`, `status`, `search`, and `get`.
- Documentation clearly states that Git workflows are external.

---

## 31. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Vendored model license blocks distribution | Verify license before release; replace model if needed. |
| Standard install becomes too large | Keep model small; document wheel size; avoid additional heavy deps. |
| Model resource loading fails from wheel | Test wheel install; use importlib resources; fallback to managed cache copy. |
| Users expect Git behavior because JSONL is diffable | Explicit non-goal in docs; provide changed-file manifests for external wrappers. |
| SQLite FTS query syntax is brittle | Robust query planner and simplification warnings. |
| Hybrid search quality varies by domain | Allow custom field extractors, weights, and provider replacement. |
| Transaction journal complexity | Keep MVP small and heavily tested. |
| Python 3.13 dependency compatibility | Verify dependency support before implementation and pin via `uv.lock`. |

---

## 32. Bottom line

JsonIBase should be a clean, VCS-neutral local record base:

```text
Canonical JSONL source
+ safe local transactions
+ Pydantic validation
+ derived SQLite/WAL index
+ FTS5
+ default vendored Model2Vec embeddings
+ hybrid search
+ structured manifests for external tools
```

Do not include Git. Do include the model.

That boundary gives the library a strong identity and keeps it reusable across architecture catalogs, standards repositories, decision records, policy stores, exception registers, agent memory stores, and other typed local knowledge bases.
