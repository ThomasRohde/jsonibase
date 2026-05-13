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
        ROOT / "zensical.toml",
        ROOT / "docs" / "index.md",
        ROOT / "docs" / "installation.md",
        ROOT / "docs" / "quickstart.md",
        ROOT / "docs" / "api.md",
        ROOT / "docs" / "cli.md",
        ROOT / "docs" / "development.md",
        ROOT / "docs" / "deployment.md",
        ROOT / "docs" / "embedding-model.md",
        ROOT / "docs" / "external-integration.md",
        ROOT / "docs" / "examples.md",
        ROOT / "docs" / "troubleshooting.md",
        ROOT / "docs" / "guides" / "jsonl-sources.md",
        ROOT / "docs" / "guides" / "search.md",
        ROOT / "docs" / "guides" / "sqlite-indexes.md",
        ROOT / "docs" / "guides" / "validation.md",
        ROOT / "CHANGELOG.md",
        ROOT / "RELEASE.md",
        ROOT / ".github" / "workflows" / "ci.yml",
        ROOT / ".github" / "workflows" / "docs.yml",
        ROOT / ".github" / "workflows" / "publish.yml",
        ROOT / "scripts" / "release.py",
        ROOT / "scripts" / "verify_model_manifest.py",
        ROOT / "examples" / "basic_usage.py",
    ]

    for path in expected:
        assert path.exists(), path
        assert path.read_text(encoding="utf-8").strip()


def test_zensical_config_documents_project_pages() -> None:
    config = (ROOT / "zensical.toml").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "docs.yml").read_text(encoding="utf-8")
    deployment = (ROOT / "docs" / "deployment.md").read_text(encoding="utf-8")

    assert 'site_url = "https://thomasrohde.github.io/jsonibase/"' in config
    assert 'docs_dir = "docs"' in config
    assert 'site_dir = "site"' in config
    assert "zensical build --clean --strict" in workflow
    assert "actions/deploy-pages" in workflow
    assert "GitHub Actions as the source" in deployment
