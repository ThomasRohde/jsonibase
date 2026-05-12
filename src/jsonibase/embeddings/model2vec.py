from __future__ import annotations

import hashlib
import json
from functools import cached_property
from importlib import resources
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel


class ModelManifest(BaseModel):
    name: str
    provider: str
    dimension: int
    files: dict[str, str]
    license: str
    source: str


class Model2VecEmbeddingProvider:
    """Default local embedding provider backed by packaged Model2Vec resources."""

    def __init__(self, model_name: str = "potion-base-8M") -> None:
        self._model_name = model_name

    @property
    def model_path(self) -> Path:
        return Path(str(resources.files("jsonibase.models").joinpath(self._model_name)))

    @cached_property
    def manifest(self) -> ModelManifest:
        data = (self.model_path / "MODEL-MANIFEST.json").read_text(encoding="utf-8")
        return ModelManifest.model_validate(json.loads(data))

    @property
    def dimension(self) -> int:
        return self.manifest.dimension

    @cached_property
    def _model(self) -> Any:
        from model2vec import StaticModel

        return StaticModel.from_pretrained(self.model_path, force_download=False)

    @property
    def fingerprint(self) -> str:
        return self._fingerprint

    @cached_property
    def _fingerprint(self) -> str:
        digest = hashlib.sha256()
        manifest_json = json.dumps(
            self.manifest.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
        )
        digest.update(manifest_json.encode("utf-8"))
        for file_name in sorted(self.manifest.files):
            digest.update(file_name.encode("utf-8"))
            digest.update((self.model_path / file_name).read_bytes())
        return f"sha256:{digest.hexdigest()}"

    def encode(self, texts: list[str] | tuple[str, ...]) -> NDArray[np.float32]:
        if not texts:
            return np.zeros((0, self.dimension), dtype=np.float32)
        vectors = self._model.encode(list(texts))
        return np.asarray(vectors, dtype=np.float32)
