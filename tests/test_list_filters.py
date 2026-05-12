from __future__ import annotations

import pytest
from pydantic import BaseModel

from jsonibase import CollectionSpec, JsonIBase
from jsonibase.errors import JsonIBaseError


class Standard(BaseModel):
    id: str
    title: str
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
        filter_fields=["status", "owner", "tags"],
        sort_fields=["title", "status"],
    )
    store = JsonIBase.open(tmp_path, [spec], rebuild_policy="manual")
    store.init()
    store.add(
        "standards",
        Standard(
            id="std_001",
            title="Managed services",
            status="active",
            owner="platform",
            tags=["cloud"],
        ),
    )
    store.add(
        "standards",
        Standard(
            id="std_002",
            title="Architecture exceptions",
            status="draft",
            owner="architecture",
            tags=["exceptions"],
        ),
    )
    store.add(
        "standards",
        Standard(
            id="std_003",
            title="Cloud tagging",
            status="active",
            owner="platform",
            tags=["cloud", "metadata"],
        ),
    )
    return store


def test_list_filters_records_using_configured_fields(tmp_path) -> None:
    store = _store(tmp_path)

    records = store.list(
        "standards",
        filters={"status": {"eq": "active"}, "tags": {"contains": "cloud"}},
        sort=["title"],
    )

    assert [record.id for record in records] == ["std_003", "std_001"]


def test_list_supports_descending_sort_and_pagination(tmp_path) -> None:
    store = _store(tmp_path)

    records = store.list("standards", sort=["-title"], offset=1, limit=1)

    assert [record.id for record in records] == ["std_003"]


def test_list_rejects_unconfigured_filter_and_sort_fields(tmp_path) -> None:
    store = _store(tmp_path)

    with pytest.raises(JsonIBaseError) as filter_error:
        store.list("standards", filters={"title": {"eq": "Managed services"}})
    with pytest.raises(JsonIBaseError) as sort_error:
        store.list("standards", sort=["owner"])

    assert filter_error.value.code == "FILTER_FIELD_NOT_CONFIGURED"
    assert sort_error.value.code == "SORT_FIELD_NOT_CONFIGURED"
