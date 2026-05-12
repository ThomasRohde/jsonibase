from __future__ import annotations

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pydantic import BaseModel

from jsonibase import CollectionSpec
from jsonibase.source.jsonl import read_jsonl, write_jsonl
from jsonibase.source.manifest import build_source_manifest


class PropertyRecord(BaseModel):
    id: str
    title: str
    tags: list[str]


record_strategy = st.builds(
    PropertyRecord,
    id=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Nd")),
        min_size=1,
        max_size=12,
    ),
    title=st.text(min_size=0, max_size=30),
    tags=st.lists(st.text(min_size=0, max_size=12), max_size=4),
)


@given(st.lists(record_strategy, max_size=10))
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_jsonl_round_trip_property(tmp_path, records: list[PropertyRecord]) -> None:
    path = tmp_path / "records.jsonl"
    spec = CollectionSpec[PropertyRecord](
        name="records",
        path="records.jsonl",
        model=PropertyRecord,
    )

    write_jsonl(path, records)
    loaded = [entry.record for entry in read_jsonl(path, spec)]

    assert loaded == records


@given(st.lists(record_strategy, max_size=10))
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_source_manifest_is_deterministic_property(
    tmp_path,
    records: list[PropertyRecord],
) -> None:
    path = tmp_path / "records.jsonl"
    spec = CollectionSpec[PropertyRecord](
        name="records",
        path="records.jsonl",
        model=PropertyRecord,
    )
    write_jsonl(path, records)

    first = build_source_manifest(
        root=tmp_path,
        collections=[spec],
        embedding_fingerprint="sha256:embedding",
    )
    second = build_source_manifest(
        root=tmp_path,
        collections=[spec],
        embedding_fingerprint="sha256:embedding",
    )

    assert first == second
