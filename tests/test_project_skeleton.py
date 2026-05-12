from __future__ import annotations

import importlib
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_declares_jsonibase_package() -> None:
    pyproject = ROOT / "pyproject.toml"
    assert pyproject.exists()

    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    project = data["project"]
    assert project["name"] == "jsonibase"
    assert project["requires-python"] == ">=3.13"
    assert "pydantic>=2" in project["dependencies"]
    assert "orjson>=3" in project["dependencies"]
    assert "portalocker>=2" in project["dependencies"]
    assert "numpy>=2" in project["dependencies"]
    assert "model2vec>=0.3" in project["dependencies"]
    assert project["scripts"]["jsonibase"] == "jsonibase.cli.main:main"

    assert data["build-system"]["build-backend"] == "hatchling.build"
    assert data["tool"]["ruff"]["target-version"] == "py313"
    assert data["tool"]["pyright"]["typeCheckingMode"] == "strict"


def test_package_exposes_public_api_and_typing_marker() -> None:
    module = importlib.import_module("jsonibase")

    assert module.__version__ == "0.1.0"
    assert module.JsonIBase.__name__ == "JsonIBase"
    assert module.CollectionSpec.__name__ == "CollectionSpec"
    assert module.SearchQuery.__name__ == "SearchQuery"
    assert module.SearchResult.__name__ == "SearchResult"
    assert module.ChangeSet.__name__ == "ChangeSet"
    assert module.ValidationReport.__name__ == "ValidationReport"
    assert module.SourceManifest.__name__ == "SourceManifest"
    assert (ROOT / "src" / "jsonibase" / "py.typed").exists()


def test_package_does_not_contain_vcs_or_git_modules() -> None:
    package_root = ROOT / "src" / "jsonibase"
    assert package_root.exists()

    forbidden_names = {"git", "github", "vcs"}
    discovered = {
        path.stem.lower()
        for path in package_root.rglob("*")
        if path.is_file() and path.suffix == ".py"
    } | {path.name.lower() for path in package_root.rglob("*") if path.is_dir()}

    assert forbidden_names.isdisjoint(discovered)
