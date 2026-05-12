from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from jsonibase.config import CollectionSpec
from jsonibase.index.builder import DEFAULT_EMBEDDING_FINGERPRINT
from jsonibase.models import SourceFileManifest, SourceManifest
from jsonibase.source.manifest import build_source_manifest

IndexStatusReason = Literal[
    "fresh",
    "missing",
    "invalid",
    "source_changed",
    "config_changed",
    "embedding_changed",
]


class IndexStatus(BaseModel):
    index_exists: bool
    stale: bool
    reason: IndexStatusReason
    source_manifest: SourceManifest
    index_manifest: SourceManifest | None = None


def index_status(
    *,
    root: str | Path,
    collections: list[CollectionSpec[BaseModel]] | tuple[CollectionSpec[BaseModel], ...],
    index_path: str | Path,
    embedding_fingerprint: str = DEFAULT_EMBEDDING_FINGERPRINT,
) -> IndexStatus:
    root_path = Path(root)
    db_path = Path(index_path)
    current_manifest = build_source_manifest(
        root=root_path,
        collections=collections,
        embedding_fingerprint=embedding_fingerprint,
    )

    if not db_path.exists():
        return IndexStatus(
            index_exists=False,
            stale=True,
            reason="missing",
            source_manifest=current_manifest,
        )

    try:
        db_manifest = _read_index_manifest(db_path, current_manifest)
    except sqlite3.Error:
        return IndexStatus(
            index_exists=True,
            stale=True,
            reason="invalid",
            source_manifest=current_manifest,
        )

    reason = _stale_reason(current_manifest, db_manifest)
    return IndexStatus(
        index_exists=True,
        stale=reason != "fresh",
        reason=reason,
        source_manifest=current_manifest,
        index_manifest=db_manifest,
    )


def _read_index_manifest(db_path: Path, current_manifest: SourceManifest) -> SourceManifest:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT * FROM ji_source_manifest ORDER BY collection").fetchall()
    finally:
        conn.close()

    collections: dict[str, SourceFileManifest] = {}
    config_fingerprint = current_manifest.config_fingerprint
    embedding_fingerprint = current_manifest.embedding_fingerprint
    for row in rows:
        collections[row["collection"]] = SourceFileManifest(
            path=Path(row["path"]),
            sha256=row["sha256"],
            size_bytes=row["size_bytes"],
            mtime_ns=row["mtime_ns"],
            record_count=row["record_count"],
        )
        config_fingerprint = row["config_fingerprint"]
        embedding_fingerprint = row["embedding_fingerprint"]

    return SourceManifest(
        collections=collections,
        config_fingerprint=config_fingerprint,
        embedding_fingerprint=embedding_fingerprint,
    )


def _stale_reason(current: SourceManifest, indexed: SourceManifest) -> IndexStatusReason:
    if current.config_fingerprint != indexed.config_fingerprint:
        return "config_changed"
    if current.embedding_fingerprint != indexed.embedding_fingerprint:
        return "embedding_changed"
    if set(current.collections) != set(indexed.collections):
        return "source_changed"
    for name, current_entry in current.collections.items():
        indexed_entry = indexed.collections[name]
        if (
            current_entry.sha256 != indexed_entry.sha256
            or current_entry.record_count != indexed_entry.record_count
            or current_entry.size_bytes != indexed_entry.size_bytes
        ):
            return "source_changed"
    return "fresh"
