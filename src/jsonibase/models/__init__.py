from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class SourceFileManifest(BaseModel):
    path: Path
    sha256: str
    size_bytes: int
    mtime_ns: int
    record_count: int


class SourceManifest(BaseModel):
    schema_version: str = "1.0"
    collections: dict[str, SourceFileManifest] = Field(
        default_factory=lambda: dict[str, SourceFileManifest]()
    )
    config_fingerprint: str
    embedding_fingerprint: str


class ChangeSet(BaseModel):
    change_set_id: str
    base_manifest: SourceManifest | None = None
    operations: list[dict[str, Any]] = Field(default_factory=lambda: list[dict[str, Any]]())


class ChangeResult(BaseModel):
    change_set_id: str
    changed_files: list[Path] = Field(default_factory=lambda: list[Path]())
    before: dict[str, Any] = Field(default_factory=lambda: dict[str, Any]())
    after: dict[str, Any] = Field(default_factory=lambda: dict[str, Any]())


class RecoveryReport(BaseModel):
    recovery_required: bool
    transactions: list[dict[str, Any]] = Field(default_factory=lambda: list[dict[str, Any]]())
    recovered: list[str] = Field(default_factory=lambda: list[str]())


class SearchQuery(BaseModel):
    query: str
    collection: str | None = None
    mode: Literal["hybrid", "fts", "vector"] = "hybrid"
    filters: dict[str, Any] = Field(default_factory=lambda: dict[str, Any]())
    top: int = 10


class SearchResult(BaseModel):
    collection: str
    record_id: str
    score: float
    record: dict[str, Any]
    match_source: Literal["fts", "vector", "hybrid"]
    snippet: str | None = None
    explanation: dict[str, Any] = Field(default_factory=lambda: dict[str, Any]())


__all__ = [
    "ChangeResult",
    "ChangeSet",
    "RecoveryReport",
    "SearchQuery",
    "SearchResult",
    "SourceFileManifest",
    "SourceManifest",
]
