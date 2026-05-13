# Release Checklist

JsonIBase publishes to PyPI through GitHub Actions trusted publishing.

## One-time GitHub/PyPI setup

- Create `ThomasRohde/jsonibase` on GitHub.
- Push the repository with `.github/workflows/ci.yml` and
  `.github/workflows/publish.yml`.
- In GitHub, create an environment named `pypi`. Add required reviewers if you
  want a manual approval gate before publishing.
- In PyPI, keep the trusted publisher configured as:
  - Repository: `ThomasRohde/jsonibase`
  - Workflow: `publish.yml`
  - Environment: `pypi`

## Pre-release checks

```shell
uv sync --extra dev
uv run ruff check src tests scripts
uv run pyright
uv run python scripts/verify_model_manifest.py
uv run pytest
uv run python -m build
uv run twine check dist/*
```

Also confirm:

- `dist/*.whl` includes `jsonibase/py.typed`.
- `dist/*.whl` includes `jsonibase/models/potion-base-8M/**`.
- `dist/*.tar.gz` does not include local caches, `uv.lock`, or design notes.
- The packaged model license/source metadata still matches
  `src/jsonibase/models/potion-base-8M/MODEL-MANIFEST.json`.
- Docs still state that Git workflows are external.

## Cutting a release

From a clean tree:

```shell
python scripts/release.py 0.1.0
git push origin main v0.1.0
```

The tag push triggers `.github/workflows/publish.yml`, which builds the sdist
and wheel, runs validation checks, publishes to PyPI using trusted publishing,
and creates a GitHub Release with the distribution artifacts.

Open the next development cycle after the release:

```shell
python scripts/release.py --post-release 0.2.0.dev0
git push origin main
```
