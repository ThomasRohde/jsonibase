from __future__ import annotations

import hashlib

from pydantic import BaseModel

from jsonibase import CollectionSpec
from jsonibase.config import config_fingerprint
from jsonibase.source.manifest import EMPTY_SHA256, build_source_manifest


class Standard(BaseModel):
    id: str
    title: str


class Reference(BaseModel):
    id: str
    title: str


def test_build_source_manifest_hashes_files_and_counts_records(tmp_path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    source = data_dir / "standards.jsonl"
    content = b'{"id":"std_001","title":"One"}\n{"id":"std_002","title":"Two"}\n'
    source.write_bytes(content)
    spec = CollectionSpec[Standard](
        name="standards",
        path="data/standards.jsonl",
        model=Standard,
    )

    manifest = build_source_manifest(
        root=tmp_path,
        collections=[spec],
        embedding_fingerprint="sha256:embedding",
    )

    entry = manifest.collections["standards"]
    assert entry.path.as_posix() == "data/standards.jsonl"
    assert entry.sha256 == f"sha256:{hashlib.sha256(content).hexdigest()}"
    assert entry.size_bytes == len(content)
    assert entry.mtime_ns > 0
    assert entry.record_count == 2
    assert manifest.config_fingerprint == config_fingerprint([spec])
    assert manifest.embedding_fingerprint == "sha256:embedding"


def test_build_source_manifest_handles_missing_source_files(tmp_path) -> None:
    spec = CollectionSpec[Standard](
        name="standards",
        path="data/standards.jsonl",
        model=Standard,
    )

    manifest = build_source_manifest(
        root=tmp_path,
        collections=[spec],
        embedding_fingerprint="sha256:embedding",
    )

    entry = manifest.collections["standards"]
    assert entry.sha256 == EMPTY_SHA256
    assert entry.size_bytes == 0
    assert entry.mtime_ns == 0
    assert entry.record_count == 0


def test_source_manifest_changes_when_config_changes(tmp_path) -> None:
    base = CollectionSpec[Standard](
        name="standards",
        path="data/standards.jsonl",
        model=Standard,
        fts_fields=["title"],
    )
    changed = CollectionSpec[Standard](
        name="standards",
        path="data/standards.jsonl",
        model=Standard,
        embedding_fields=["title"],
    )

    base_manifest = build_source_manifest(
        root=tmp_path,
        collections=[base],
        embedding_fingerprint="sha256:embedding",
    )
    changed_manifest = build_source_manifest(
        root=tmp_path,
        collections=[changed],
        embedding_fingerprint="sha256:embedding",
    )

    assert base_manifest.config_fingerprint != changed_manifest.config_fingerprint


def test_source_manifest_collections_are_order_independent(tmp_path) -> None:
    standards = CollectionSpec[Standard](
        name="standards",
        path="data/standards.jsonl",
        model=Standard,
    )
    references = CollectionSpec[Reference](
        name="references",
        path="data/references.jsonl",
        model=Reference,
    )

    first = build_source_manifest(
        root=tmp_path,
        collections=[standards, references],
        embedding_fingerprint="sha256:embedding",
    )
    second = build_source_manifest(
        root=tmp_path,
        collections=[references, standards],
        embedding_fingerprint="sha256:embedding",
    )

    assert first == second
