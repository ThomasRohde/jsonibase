from __future__ import annotations

import sqlite3

from pydantic import BaseModel

from jsonibase import CollectionSpec, JsonIBase


class Standard(BaseModel):
    id: str
    title: str
    body: str
    status: str
    owner: str
    tags: list[str] = []


def _store(tmp_path):
    spec = CollectionSpec[Standard](
        name="standards",
        path="data/standards.jsonl",
        model=Standard,
        id_field="id",
        title_field="title",
        fts_fields=["title", "body", "tags"],
        filter_fields=["status", "owner", "tags"],
    )
    store = JsonIBase.open(
        root=tmp_path,
        collections=[spec],
        index_path=".jsonibase/jsonibase.db",
        rebuild_policy="manual",
    )
    store.init()
    store.add(
        "standards",
        Standard(
            id="std_001",
            title="Managed services",
            body="Prefer managed services where possible.",
            status="active",
            owner="platform",
            tags=["cloud", "platform"],
        ),
    )
    return store


def test_status_reports_missing_and_fresh_index(tmp_path) -> None:
    store = _store(tmp_path)

    missing = store.status()
    assert missing.index_exists is False
    assert missing.stale is True
    assert missing.reason == "missing"

    store.rebuild()

    fresh = store.status()
    assert fresh.index_exists is True
    assert fresh.stale is False
    assert fresh.reason == "fresh"


def test_rebuild_creates_wal_sqlite_index_with_collection_and_fts_tables(tmp_path) -> None:
    store = _store(tmp_path)

    store.rebuild()

    conn = sqlite3.connect(tmp_path / ".jsonibase" / "jsonibase.db")
    conn.row_factory = sqlite3.Row
    try:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"

        row = conn.execute("SELECT * FROM ji_standards WHERE id = ?", ("std_001",)).fetchone()
        assert row["title"] == "Managed services"
        assert row["status"] == "active"
        assert row["owner"] == "platform"
        assert row["tags"] == '["cloud","platform"]'
        assert row["source_line"] == 1
        assert row["source_sha256"].startswith("sha256:")
        assert '"body":"Prefer managed services where possible."' in row["json"]

        fts = conn.execute(
            "SELECT title, body, tags FROM ji_standards_fts WHERE id = ?",
            ("std_001",),
        ).fetchone()
        assert fts["title"] == "Managed services"
        assert fts["body"] == "Prefer managed services where possible."
        assert fts["tags"] == "cloud platform"
    finally:
        conn.close()


def test_rebuild_persists_source_manifest(tmp_path) -> None:
    store = _store(tmp_path)

    store.rebuild()

    conn = sqlite3.connect(tmp_path / ".jsonibase" / "jsonibase.db")
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT collection, path, record_count, config_fingerprint, embedding_fingerprint "
            "FROM ji_source_manifest WHERE collection = ?",
            ("standards",),
        ).fetchone()
        assert row["collection"] == "standards"
        assert row["path"] == "data/standards.jsonl"
        assert row["record_count"] == 1
        assert row["config_fingerprint"].startswith("sha256:")
        assert row["embedding_fingerprint"].startswith("sha256:")
    finally:
        conn.close()


def test_status_reports_stale_when_source_changes_after_rebuild(tmp_path) -> None:
    store = _store(tmp_path)
    store.rebuild()

    store.add(
        "standards",
        Standard(
            id="std_002",
            title="New standard",
            body="Fresh source.",
            status="draft",
            owner="platform",
        ),
    )

    stale = store.status()
    assert stale.index_exists is True
    assert stale.stale is True
    assert stale.reason == "source_changed"
