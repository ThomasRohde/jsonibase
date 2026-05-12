from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from jsonibase import CollectionSpec
from jsonibase.config import JsonIBaseConfig, RelationshipSpec, config_fingerprint


class Standard(BaseModel):
    id: str
    title: str
    body: str
    status: str
    owner: str
    tags: list[str]


class Link(BaseModel):
    id: str
    source_id: str
    target_id: str


def test_collection_spec_accepts_typed_pydantic_model() -> None:
    spec = CollectionSpec[Standard](
        name="standards",
        path="data/standards.jsonl",
        model=Standard,
        id_field="id",
        title_field="title",
        fts_fields=["title", "body", "tags"],
        embedding_fields=["title", "body"],
        filter_fields=["status", "owner", "tags"],
        sort_fields=["title"],
    )

    assert spec.model is Standard
    assert spec.fts_fields == ("title", "body", "tags")
    assert spec.embedding_fields == ("title", "body")
    assert spec.filter_fields == ("status", "owner", "tags")
    assert spec.deletion == "forbid"


def test_collection_spec_rejects_unknown_configured_fields() -> None:
    with pytest.raises(ValidationError) as exc_info:
        CollectionSpec[Standard](
            name="standards",
            path="data/standards.jsonl",
            model=Standard,
            id_field="missing",
        )

    assert "unknown field 'missing'" in str(exc_info.value)


def test_collection_spec_rejects_invalid_names() -> None:
    with pytest.raises(ValidationError) as exc_info:
        CollectionSpec[Standard](
            name="not valid",
            path="data/standards.jsonl",
            model=Standard,
        )

    assert "collection name must match" in str(exc_info.value)


def test_relationship_specs_validate_source_field() -> None:
    with pytest.raises(ValidationError) as exc_info:
        CollectionSpec[Link](
            name="links",
            path="data/links.jsonl",
            model=Link,
            relationships=[
                RelationshipSpec(field="missing", target_collection="standards"),
            ],
        )

    assert "unknown relationship field 'missing'" in str(exc_info.value)


def test_config_fingerprint_is_deterministic_and_order_independent() -> None:
    standards = CollectionSpec[Standard](
        name="standards",
        path="data/standards.jsonl",
        model=Standard,
        fts_fields=["title", "body"],
    )
    links = CollectionSpec[Link](
        name="links",
        path="data/links.jsonl",
        model=Link,
        relationships=[RelationshipSpec(field="target_id", target_collection="standards")],
    )

    first = config_fingerprint([standards, links])
    second = config_fingerprint([links, standards])

    assert first.startswith("sha256:")
    assert first == second


def test_config_fingerprint_changes_when_indexing_options_change() -> None:
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
        fts_fields=["title", "body"],
    )

    assert config_fingerprint([base]) != config_fingerprint([changed])


def test_jsonibase_config_exposes_fingerprint() -> None:
    spec = CollectionSpec[Standard](
        name="standards",
        path="data/standards.jsonl",
        model=Standard,
    )
    config = JsonIBaseConfig(collections=[spec])

    assert config.fingerprint == config_fingerprint([spec])
