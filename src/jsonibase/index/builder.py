from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import uuid4

import numpy as np
import orjson
from numpy.typing import NDArray
from pydantic import BaseModel

from jsonibase.config import CollectionSpec
from jsonibase.embeddings import EmbeddingProvider, Model2VecEmbeddingProvider, serialize_vector
from jsonibase.errors import JsonIBaseError
from jsonibase.index.sqlite import connect_index
from jsonibase.models import SourceManifest
from jsonibase.source.jsonl import JsonlRecord, read_jsonl
from jsonibase.source.manifest import build_source_manifest
from jsonibase.validation import validate_workspace

DEFAULT_EMBEDDING_PROVIDER = Model2VecEmbeddingProvider()
DEFAULT_EMBEDDING_FINGERPRINT = DEFAULT_EMBEDDING_PROVIDER.fingerprint
DISABLED_EMBEDDING_FINGERPRINT = "sha256:embeddings-disabled"


def rebuild_index(
    *,
    root: str | Path,
    collections: list[CollectionSpec[BaseModel]] | tuple[CollectionSpec[BaseModel], ...],
    index_path: str | Path,
    embedding_fingerprint: str = DEFAULT_EMBEDDING_FINGERPRINT,
    embedding_provider: EmbeddingProvider | None = None,
    embeddings_enabled: bool = True,
) -> SourceManifest:
    root_path = Path(root)
    target_path = Path(index_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    report = validate_workspace(root_path, collections)
    if not report.ok:
        raise JsonIBaseError(
            "VALIDATION_FAILED",
            "cannot rebuild index from invalid source files",
            details={"findings": [finding.model_dump() for finding in report.findings]},
        )

    provider: EmbeddingProvider | None
    provider = embedding_provider or DEFAULT_EMBEDDING_PROVIDER if embeddings_enabled else None
    manifest_embedding_fingerprint = (
        embedding_provider.fingerprint
        if embedding_provider and embeddings_enabled
        else embedding_fingerprint
    )
    manifest = build_source_manifest(
        root=root_path,
        collections=collections,
        embedding_fingerprint=manifest_embedding_fingerprint,
    )
    temp_path = target_path.with_name(f"{target_path.name}.tmp.{uuid4().hex}")

    conn = connect_index(temp_path)
    try:
        _create_manifest_table(conn)
        for spec in collections:
            _create_collection_schema(conn, spec)
            records = read_jsonl(_source_path(root_path, spec), spec)
            _insert_records(conn, spec, records, provider)
        _insert_manifest(conn, manifest)
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        conn.close()

    _remove_sqlite_sidecars(target_path)
    temp_path.replace(target_path)
    _remove_sqlite_sidecars(temp_path)

    final_conn = connect_index(target_path)
    final_conn.close()
    return manifest


def _create_manifest_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
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
        )
        """
    )


def _create_collection_schema(conn: sqlite3.Connection, spec: CollectionSpec[BaseModel]) -> None:
    table_name = _collection_table(spec)
    columns = [
        '"id" TEXT PRIMARY KEY',
        '"json" TEXT NOT NULL',
    ]
    for field_name in _indexed_columns(spec):
        columns.append(f"{_quote_identifier(field_name)} TEXT")
    columns.extend(
        [
            '"embedding" BLOB',
            '"source_line" INTEGER NOT NULL',
            '"source_sha256" TEXT NOT NULL',
        ]
    )
    conn.execute(f"CREATE TABLE {_quote_identifier(table_name)} ({', '.join(columns)})")

    if spec.fts_fields:
        fts_columns = ['"id" UNINDEXED']
        fts_columns.extend(_quote_identifier(field_name) for field_name in spec.fts_fields)
        conn.execute(
            f"CREATE VIRTUAL TABLE {_quote_identifier(_fts_table(spec))} "
            f"USING fts5({', '.join(fts_columns)}, tokenize='unicode61 remove_diacritics 2')"
        )


def _insert_records(
    conn: sqlite3.Connection,
    spec: CollectionSpec[BaseModel],
    records: list[JsonlRecord[BaseModel]],
    embedding_provider: EmbeddingProvider | None,
) -> None:
    table_name = _collection_table(spec)
    columns = ["id", "json", *_indexed_columns(spec), "embedding", "source_line", "source_sha256"]
    placeholders = ", ".join("?" for _ in columns)
    quoted_columns = ", ".join(_quote_identifier(column) for column in columns)
    insert_sql = (
        f"INSERT INTO {_quote_identifier(table_name)} ({quoted_columns}) VALUES ({placeholders})"
    )

    embedding_texts = [_embedding_text(spec, entry.record) for entry in records]
    embeddings: NDArray[np.float32] | None = (
        embedding_provider.encode(embedding_texts) if embedding_provider is not None else None
    )

    for index, entry in enumerate(records):
        payload = entry.record.model_dump(mode="json")
        values: list[object] = [
            str(getattr(entry.record, spec.id_field)),
            orjson.dumps(payload, option=orjson.OPT_SORT_KEYS).decode("utf-8"),
        ]
        values.extend(
            _stored_field_value(getattr(entry.record, field)) for field in _indexed_columns(spec)
        )
        embedding = serialize_vector(embeddings[index]) if embeddings is not None else None
        values.extend([embedding, entry.line_number, entry.source_sha256])
        conn.execute(insert_sql, values)

        if spec.fts_fields:
            fts_columns = ["id", *spec.fts_fields]
            fts_values = [str(getattr(entry.record, spec.id_field))]
            fts_values.extend(
                _fts_field_value(getattr(entry.record, field)) for field in spec.fts_fields
            )
            fts_insert = (
                f"INSERT INTO {_quote_identifier(_fts_table(spec))} "
                f"({', '.join(_quote_identifier(column) for column in fts_columns)}) "
                f"VALUES ({', '.join('?' for _ in fts_columns)})"
            )
            conn.execute(fts_insert, fts_values)


def _insert_manifest(conn: sqlite3.Connection, manifest: SourceManifest) -> None:
    built_at = datetime.now(tz=UTC).isoformat()
    for collection, entry in manifest.collections.items():
        conn.execute(
            """
            INSERT INTO ji_source_manifest (
                collection,
                path,
                sha256,
                size_bytes,
                mtime_ns,
                record_count,
                config_fingerprint,
                embedding_fingerprint,
                built_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                collection,
                entry.path.as_posix(),
                entry.sha256,
                entry.size_bytes,
                entry.mtime_ns,
                entry.record_count,
                manifest.config_fingerprint,
                manifest.embedding_fingerprint,
                built_at,
            ),
        )


def _indexed_columns(spec: CollectionSpec[BaseModel]) -> list[str]:
    fields = [field for field in [spec.title_field, *spec.filter_fields] if field is not None]
    return sorted(set(fields) - {spec.id_field})


def _stored_field_value(value: object) -> str:
    if isinstance(value, list | tuple):
        return orjson.dumps(value).decode("utf-8")
    return str(value)


def _fts_field_value(value: object) -> str:
    if isinstance(value, list | tuple | set):
        return " ".join(str(item) for item in cast(Iterable[object], value))
    return str(value)


def _embedding_text(spec: CollectionSpec[BaseModel], record: BaseModel) -> str:
    fields = spec.embedding_fields or spec.fts_fields
    return " ".join(_fts_field_value(getattr(record, field)) for field in fields)


def _collection_table(spec: CollectionSpec[BaseModel]) -> str:
    return f"ji_{spec.name}"


def _fts_table(spec: CollectionSpec[BaseModel]) -> str:
    return f"{_collection_table(spec)}_fts"


def _source_path(root: Path, spec: CollectionSpec[BaseModel]) -> Path:
    source_path = Path(spec.path)
    return source_path if source_path.is_absolute() else root / source_path


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _remove_sqlite_sidecars(path: Path) -> None:
    suffixes: tuple[str, ...] = ("", "-wal", "-shm")
    for suffix in suffixes:
        sidecar = Path(f"{path}{suffix}")
        if sidecar.exists():
            sidecar.unlink()
