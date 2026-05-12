from __future__ import annotations

import pytest
from pydantic import BaseModel

from jsonibase import CollectionSpec, JsonIBase
from jsonibase.config import RelationshipSpec
from jsonibase.errors import JsonIBaseError


class Standard(BaseModel):
    id: str
    title: str


class Link(BaseModel):
    id: str
    target_id: str


def _store(tmp_path):
    standards = CollectionSpec[Standard](
        name="standards",
        path="data/standards.jsonl",
        model=Standard,
    )
    links = CollectionSpec[Link](
        name="links",
        path="data/links.jsonl",
        model=Link,
        relationships=[RelationshipSpec(field="target_id", target_collection="standards")],
    )
    store = JsonIBase.open(tmp_path, [standards, links], rebuild_policy="manual")
    store.init()
    return store


def test_plan_preview_does_not_write_until_apply(tmp_path) -> None:
    store = _store(tmp_path)

    with store.plan() as plan:
        plan.add("standards", Standard(id="std_001", title="One"))
        preview = plan.preview()

    assert preview.operations == [
        {
            "op": "add",
            "collection": "standards",
            "record_id": "std_001",
        }
    ]
    assert preview.base_manifest is not None
    assert "standards" in preview.base_manifest.collections
    assert store.get("standards", "std_001") is None

    result = store.apply(plan)

    assert result.changed_files == [tmp_path / "data" / "standards.jsonl"]
    assert store.get("standards", "std_001") == Standard(id="std_001", title="One")


def test_apply_validates_multi_collection_staged_final_state(tmp_path) -> None:
    store = _store(tmp_path)

    with store.plan() as plan:
        plan.add("links", Link(id="lnk_001", target_id="std_001"))
        plan.add("standards", Standard(id="std_001", title="One"))

    result = store.apply(plan)

    assert result.changed_files == [
        tmp_path / "data" / "links.jsonl",
        tmp_path / "data" / "standards.jsonl",
    ]
    assert store.get("links", "lnk_001") == Link(id="lnk_001", target_id="std_001")


def test_apply_rejects_invalid_staged_final_state_without_writing(tmp_path) -> None:
    store = _store(tmp_path)

    with store.plan() as plan:
        plan.add("links", Link(id="lnk_001", target_id="std_missing"))

    with pytest.raises(JsonIBaseError) as exc_info:
        store.apply(plan)

    assert exc_info.value.code == "VALIDATION_FAILED"
    assert store.get("links", "lnk_001") is None


def test_plan_supports_update_and_upsert_operations(tmp_path) -> None:
    store = _store(tmp_path)
    store.add("standards", Standard(id="std_001", title="One"))

    with store.plan() as plan:
        plan.update("standards", "std_001", {"title": "Updated"})
        plan.upsert("standards", Standard(id="std_002", title="Two"))

    store.apply(plan)

    assert store.get("standards", "std_001") == Standard(id="std_001", title="Updated")
    assert store.get("standards", "std_002") == Standard(id="std_002", title="Two")
