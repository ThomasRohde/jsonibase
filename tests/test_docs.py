from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_readme_documents_quickstart_boundary_and_embeddings() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "JsonIBase.open" in readme
    assert "Git workflows are external" in readme
    assert "bundled Model2Vec" in readme
    assert "jsonibase guide" in readme


def test_release_readiness_docs_exist() -> None:
    expected = [
        ROOT / "docs" / "api.md",
        ROOT / "docs" / "cli.md",
        ROOT / "docs" / "embedding-model.md",
        ROOT / "docs" / "external-integration.md",
        ROOT / "RELEASE.md",
        ROOT / "examples" / "basic_usage.py",
    ]

    for path in expected:
        assert path.exists(), path
        assert path.read_text(encoding="utf-8").strip()
