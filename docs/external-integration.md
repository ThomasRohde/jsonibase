# External Integration

JsonIBase deliberately does not implement Git, GitHub, pull requests, branches,
commits, cloud sync, or hosted APIs.

External tools can integrate by using:

- Canonical JSONL source files.
- `ChangeResult.changed_files`.
- `SourceManifest` fingerprints.
- `JsonIBase.status()` for freshness.
- `JsonIBase.validate()` for CI checks.

The examples under `examples/` show one integration pattern: fetch public
internet data, normalize it into Pydantic models, and let JsonIBase own the
canonical JSONL and derived search index.

Repository owners decide how to ignore or track `.jsonibase/` artifacts. A common
ignore policy is:

```text
.jsonibase/*.db
.jsonibase/*.db-wal
.jsonibase/*.db-shm
.jsonibase/locks/
.jsonibase/transactions/
```
