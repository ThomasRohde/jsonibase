from __future__ import annotations

from typing import Protocol

import numpy as np
from numpy.typing import NDArray


class EmbeddingProvider(Protocol):
    @property
    def dimension(self) -> int: ...

    @property
    def fingerprint(self) -> str: ...

    def encode(self, texts: list[str] | tuple[str, ...]) -> NDArray[np.float32]: ...
