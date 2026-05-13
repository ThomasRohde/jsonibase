"""Verify packaged model files against MODEL-MANIFEST.json."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "src" / "jsonibase" / "models" / "potion-base-8M"
MANIFEST = MODEL_DIR / "MODEL-MANIFEST.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as model_file:
        for chunk in iter(lambda: model_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise SystemExit("MODEL-MANIFEST.json must contain a files object")

    failures: list[str] = []
    for relative_name, expected in sorted(files.items()):
        if not isinstance(relative_name, str) or not isinstance(expected, str):
            failures.append(f"invalid manifest entry: {relative_name!r} -> {expected!r}")
            continue
        path = MODEL_DIR / relative_name
        if not path.is_file():
            failures.append(f"missing model file: {path.relative_to(ROOT)}")
            continue
        actual = _sha256(path)
        if actual != expected:
            failures.append(
                f"{path.relative_to(ROOT)} expected {expected}, got {actual}"
            )

    unexpected = sorted(
        path.name
        for path in MODEL_DIR.iterdir()
        if path.is_file()
        and path.name != MANIFEST.name
        and path.name not in set(_manifest_names(files))
    )
    for name in unexpected:
        failures.append(f"model file not listed in manifest: {name}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print(f"verified {len(files)} model files")
    return 0


def _manifest_names(files: dict[Any, Any]) -> list[str]:
    return [name for name in files if isinstance(name, str)]


if __name__ == "__main__":
    sys.exit(main())
