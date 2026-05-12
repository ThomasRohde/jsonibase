from __future__ import annotations

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
        embedding_fields=["title", "body"],
        filter_fields=["status", "owner", "tags"],
    )
    store = JsonIBase.open(
        root=tmp_path,
        collections=[spec],
        index_path=".jsonibase/jsonibase.db",
        rebuild_policy="lazy",
    )
    store.init()
    store.add(
        "standards",
        Standard(
            id="std_001",
            title="Managed services",
            body="Prefer managed services instead of self hosting.",
            status="active",
            owner="platform",
            tags=["cloud", "platform"],
        ),
    )
    store.add(
        "standards",
        Standard(
            id="std_002",
            title="Self-hosted exceptions",
            body="Use exceptions for products that cannot be managed services.",
            status="draft",
            owner="architecture",
            tags=["exceptions"],
        ),
    )
    return store


def test_fts_search_rebuilds_lazy_index_and_returns_explanations(tmp_path) -> None:
    store = _store(tmp_path)

    results = store.search("standards", "managed services", mode="fts", top=5)

    assert [result.record_id for result in results] == ["std_001", "std_002"]
    assert results[0].match_source == "fts"
    assert results[0].record["title"] == "Managed services"
    assert results[0].snippet == "Managed services"
    assert results[0].explanation["fts_rank"] == 1
    assert store.status().reason == "fresh"


def test_search_filters_are_applied_to_fts_and_vector_modes(tmp_path) -> None:
    store = _store(tmp_path)

    fts_results = store.search(
        "standards",
        "managed services",
        mode="fts",
        filters={"status": {"eq": "active"}},
    )
    vector_results = store.search(
        "standards",
        "self hosted",
        mode="vector",
        filters={"status": {"eq": "draft"}},
    )

    assert [result.record_id for result in fts_results] == ["std_001"]
    assert [result.record_id for result in vector_results] == ["std_002"]


def test_vector_search_uses_stored_embeddings(tmp_path) -> None:
    store = _store(tmp_path)

    results = store.search("standards", "self hosting exceptions", mode="vector", top=1)

    assert len(results) == 1
    assert results[0].record_id == "std_002"
    assert results[0].match_source == "vector"
    assert results[0].explanation["vector_rank"] == 1
    assert results[0].score > 0


def test_hybrid_search_combines_fts_and_vector_sources(tmp_path) -> None:
    store = _store(tmp_path)

    results = store.search("standards", "managed services", top=1)

    assert len(results) == 1
    assert results[0].record_id == "std_001"
    assert results[0].match_source == "hybrid"
    assert "fts_rank" in results[0].explanation
    assert "vector_rank" in results[0].explanation


def test_malformed_fts_input_is_simplified_instead_of_crashing(tmp_path) -> None:
    store = _store(tmp_path)

    results = store.search("standards", '"managed services":', mode="fts")

    assert results
    assert results[0].record_id == "std_001"


def test_fts_search_uses_strict_plans_and_title_weighting(tmp_path) -> None:
    store = _store(tmp_path)
    store.add(
        "standards",
        Standard(
            id="std_003",
            title="alpha beta verified standard",
            body="Short body.",
            status="active",
            owner="platform",
        ),
    )
    store.add(
        "standards",
        Standard(
            id="std_004",
            title="background note",
            body=" ".join(["alpha", "beta"] * 12),
            status="active",
            owner="platform",
        ),
    )
    store.add(
        "standards",
        Standard(
            id="std_005",
            title="noise alpha candidate",
            body=" ".join(["noise", "alpha"] * 12),
            status="active",
            owner="platform",
        ),
    )

    title_results = store.search("standards", "alpha beta", mode="fts", top=2)
    noisy_results = store.search("standards", "alpha beta noise", mode="fts", top=3)

    assert title_results[0].record_id == "std_003"
    assert title_results[0].explanation["fts_query_strategy"] == "all_terms"
    assert noisy_results[0].record_id == "std_003"
    assert noisy_results[0].explanation["fts_query_strategy"] == "adjacent_terms"
