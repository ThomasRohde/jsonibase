from __future__ import annotations

import hashlib
from pathlib import Path

from pydantic import BaseModel

from jsonibase.config import CollectionSpec, config_fingerprint
from jsonibase.models import SourceFileManifest, SourceManifest

EMPTY_SHA256 = f"sha256:{hashlib.sha256(b'').hexdigest()}"


def build_source_manifest(
    *,
    root: str | Path,
    collections: list[CollectionSpec[BaseModel]] | tuple[CollectionSpec[BaseModel], ...],
    embedding_fingerprint: str,
) -> SourceManifest:
    root_path = Path(root)
    entries: dict[str, SourceFileManifest] = {}

    for spec in sorted(collections, key=lambda item: item.name):
        configured_path = Path(spec.path)
        source_path = (
            configured_path if configured_path.is_absolute() else root_path / configured_path
        )
        entries[spec.name] = _manifest_entry(configured_path, source_path)

    return SourceManifest(
        collections=entries,
        config_fingerprint=config_fingerprint(collections),
        embedding_fingerprint=embedding_fingerprint,
    )


def _manifest_entry(configured_path: Path, source_path: Path) -> SourceFileManifest:
    if not source_path.exists():
        return SourceFileManifest(
            path=configured_path,
            sha256=EMPTY_SHA256,
            size_bytes=0,
            mtime_ns=0,
            record_count=0,
        )

    data = source_path.read_bytes()
    stat = source_path.stat()
    return SourceFileManifest(
        path=configured_path,
        sha256=f"sha256:{hashlib.sha256(data).hexdigest()}",
        size_bytes=len(data),
        mtime_ns=stat.st_mtime_ns,
        record_count=_count_records(data),
    )


def _count_records(data: bytes) -> int:
    if not data:
        return 0
    if data.endswith(b"\n"):
        return data.count(b"\n")
    return data.count(b"\n") + 1
