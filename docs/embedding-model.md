# Embeddings

JsonIBase includes a default local embedding provider so semantic search works without a
hosted service.

## Bundled model

Model resources are packaged under `jsonibase.models/potion-base-8M/` and loaded through
Python package resources. The default provider is `Model2VecEmbeddingProvider`, which
loads the bundled files with `StaticModel.from_pretrained()`.

The provider exposes the `EmbeddingProvider` protocol:

```python
class EmbeddingProvider(Protocol):
    @property
    def dimension(self) -> int: ...

    @property
    def fingerprint(self) -> str: ...

    def encode(self, texts: list[str] | tuple[str, ...]) -> NDArray[np.float32]: ...
```

The packaged manifest records SHA-256 hashes and the MIT license declared by the model
card. Run this check before publishing a package:

```shell
uv run python scripts/verify_model_manifest.py
```

## Offline behavior

The default provider performs no implicit model download or network call during normal
operation. It reads model files from the installed package.

Applications that require a different model can pass a provider:

```python
store = JsonIBase.open(
    root=".",
    collections=[standards],
    embedding_provider=my_provider,
)
```

The provider fingerprint is stored in the SQLite index manifest. Changing providers or
disabling embeddings marks the index stale with the `embedding_changed` reason.

## Disabling embeddings

Disable vector behavior when an application wants lexical-only search:

```python
store = JsonIBase.open(
    root=".",
    collections=[standards],
    embeddings_enabled=False,
)
```

When embeddings are disabled, `mode="hybrid"` falls back to FTS and `mode="vector"`
returns no results.
