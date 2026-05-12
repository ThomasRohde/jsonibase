from __future__ import annotations

import numpy as np
from pydantic import BaseModel

from jsonibase import CollectionSpec, JsonIBase
from jsonibase.embeddings import (
    Model2VecEmbeddingProvider,
    deserialize_vector,
    serialize_vector,
)


def test_default_model_resources_are_packaged_and_fingerprinted() -> None:
    provider = Model2VecEmbeddingProvider()

    manifest = provider.manifest
    assert manifest.name == "potion-base-8M"
    assert manifest.provider == "model2vec"
    assert manifest.dimension == provider.dimension
    assert provider.fingerprint.startswith("sha256:")
    for file_name, sha256 in manifest.files.items():
        assert "TO_BE_VERIFIED" not in sha256
        assert sha256.startswith("sha256:")
        assert (provider.model_path / file_name).exists()
    assert manifest.license == "MIT"


def test_default_provider_returns_deterministic_float32_vectors() -> None:
    provider = Model2VecEmbeddingProvider()

    vectors = provider.encode(["managed services", "managed services"])

    assert vectors.shape == (2, provider.dimension)
    assert vectors.dtype == np.float32
    np.testing.assert_allclose(vectors[0], vectors[1])
    assert np.isfinite(vectors).all()


def test_vector_serialization_round_trips_float32_vectors() -> None:
    vector = np.array([0.25, -0.5, 1.0], dtype=np.float32)

    encoded = serialize_vector(vector)
    decoded = deserialize_vector(encoded)

    assert decoded.dtype == np.float32
    np.testing.assert_array_equal(decoded, vector)


class EmbeddingRecord(BaseModel):
    id: str
    title: str
    body: str


class ConstantEmbeddingProvider:
    dimension = 3
    fingerprint = "sha256:constant-provider"

    def encode(self, texts: list[str] | tuple[str, ...]) -> np.ndarray:
        _ = texts
        return np.ones((len(texts), self.dimension), dtype=np.float32)


def test_custom_embedding_provider_controls_manifest_fingerprint(tmp_path) -> None:
    spec = CollectionSpec[EmbeddingRecord](
        name="records",
        path="records.jsonl",
        model=EmbeddingRecord,
        fts_fields=["title", "body"],
        embedding_fields=["title", "body"],
    )
    store = JsonIBase.open(
        tmp_path,
        [spec],
        embedding_provider=ConstantEmbeddingProvider(),
    )
    store.init()
    store.add("records", EmbeddingRecord(id="rec_001", title="One", body="Body"))
    store.rebuild()

    assert store.status().source_manifest.embedding_fingerprint == "sha256:constant-provider"


def test_embeddings_can_be_disabled_explicitly(tmp_path) -> None:
    spec = CollectionSpec[EmbeddingRecord](
        name="records",
        path="records.jsonl",
        model=EmbeddingRecord,
        fts_fields=["title", "body"],
        embedding_fields=["title", "body"],
    )
    store = JsonIBase.open(tmp_path, [spec], embeddings_enabled=False)
    store.init()
    store.add("records", EmbeddingRecord(id="rec_001", title="One", body="Body"))
    store.rebuild()

    assert store.status().source_manifest.embedding_fingerprint == "sha256:embeddings-disabled"
    assert store.search("records", "one", mode="vector") == []
