from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def serialize_vector(vector: NDArray[np.float32]) -> bytes:
    return np.asarray(vector, dtype=np.float32).tobytes()


def deserialize_vector(data: bytes) -> NDArray[np.float32]:
    return np.frombuffer(data, dtype=np.float32).copy()
