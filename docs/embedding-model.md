# Embedding Model

JsonIBase packages model resources under `jsonibase.models/potion-base-8M/` and
loads them through package resources. The default provider is named
`Model2VecEmbeddingProvider` and exposes:

- `dimension`
- `fingerprint`
- `encode(texts)`

The provider is local and deterministic. It loads the packaged Model2Vec files
with `StaticModel.from_pretrained()` from the package resource path and performs
no implicit model download or network call. The model manifest records the MIT
license declared by the model card and SHA-256 hashes for packaged files.

Applications can pass a custom provider to `JsonIBase.open(..., embedding_provider=...)`.
The provider must implement the `EmbeddingProvider` protocol.
