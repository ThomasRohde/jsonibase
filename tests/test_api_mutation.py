from __future__ import annotations

import pytest
from pydantic import BaseModel

from jsonibase import CollectionSpec, JsonIBase
from jsonibase.errors import JsonIBaseError


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
    return JsonIBase.open(
        root=tmp_path,
        collections=[spec],
        index_path=".jsonibase/jsonibase.db",
        rebuild_policy="manual",
    )


def test_init_creates_source_files_and_metadata_directories(tmp_path) -> None:
    store = _store(tmp_path)

    store.init()

    assert (tmp_path / "data" / "standards.jsonl").read_text(encoding="utf-8") == ""
    assert (tmp_path / ".jsonibase" / "locks").is_dir()
    assert (tmp_path / ".jsonibase" / "transactions").is_dir()


def test_add_get_and_list_records_through_canonical_source(tmp_path) -> None:
    store = _store(tmp_path)
    store.init()
    record = Standard(
        id="std_001",
        title="Managed services",
        body="Prefer managed services.",
        status="active",
        owner="platform",
        tags=["cloud"],
    )

    result = store.add("standards", record)

    assert result.changed_files == [tmp_path / "data" / "standards.jsonl"]
    assert store.get("standards", "std_001") == record
    assert store.list("standards") == [record]
    assert list((tmp_path / ".jsonibase" / "transactions").iterdir()) == []
    assert (tmp_path / "data" / "standards.jsonl").read_text(encoding="utf-8") == (
        '{"body":"Prefer managed services.",'
        '"id":"std_001",'
        '"owner":"platform",'
        '"status":"active",'
        '"tags":["cloud"],'
        '"title":"Managed services"}\n'
    )


def test_add_rejects_duplicate_ids_without_changing_source(tmp_path) -> None:
    store = _store(tmp_path)
    store.init()
    store.add(
        "standards",
        Standard(id="std_001", title="One", body="Body", status="active", owner="platform"),
    )
    before = (tmp_path / "data" / "standards.jsonl").read_text(encoding="utf-8")

    with pytest.raises(JsonIBaseError) as exc_info:
        store.add(
            "standards",
            Standard(id="std_001", title="Two", body="Body", status="active", owner="platform"),
        )

    assert exc_info.value.code == "DUPLICATE_ID"
    assert (tmp_path / "data" / "standards.jsonl").read_text(encoding="utf-8") == before


def test_update_patches_record_and_validates_final_state(tmp_path) -> None:
    store = _store(tmp_path)
    store.init()
    store.add(
        "standards",
        Standard(id="std_001", title="One", body="Body", status="draft", owner="platform"),
    )

    result = store.update("standards", "std_001", {"status": "active"})

    assert result.before["status"] == "draft"
    assert result.after["status"] == "active"
    assert store.get("standards", "std_001").status == "active"


def test_upsert_inserts_and_replaces_by_id(tmp_path) -> None:
    store = _store(tmp_path)
    store.init()

    store.upsert(
        "standards",
        Standard(id="std_001", title="One", body="Body", status="draft", owner="platform"),
    )
    store.upsert(
        "standards",
        Standard(id="std_001", title="One updated", body="Body", status="active", owner="platform"),
    )

    records = store.list("standards")
    assert len(records) == 1
    assert records[0].title == "One updated"
    assert records[0].status == "active"


def test_update_missing_record_fails_clearly(tmp_path) -> None:
    store = _store(tmp_path)
    store.init()

    with pytest.raises(JsonIBaseError) as exc_info:
        store.update("standards", "std_999", {"status": "active"})

    assert exc_info.value.code == "RECORD_NOT_FOUND"
