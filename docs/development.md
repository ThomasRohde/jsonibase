# Development

JsonIBase uses a `src` layout and targets Python 3.13 or newer.

## Setup

```shell
uv sync --extra cli --extra dev
```

## Checks

Run the full development gate before opening a pull request:

```shell
uv run ruff check src tests scripts
uv run pyright
uv run python scripts/verify_model_manifest.py
uv run pytest
uv run python -m build
uv run twine check dist/*
```

Focused commands:

```shell
uv run pytest tests/test_search.py
uv run pytest --cov=jsonibase
uv run jsonibase guide
uv run zensical build --clean --strict
```

## Project layout

| Path | Purpose |
|---|---|
| `src/jsonibase/` | Package source. |
| `src/jsonibase/api.py` | Main facade. |
| `src/jsonibase/cli/main.py` | Typer CLI. |
| `src/jsonibase/models/potion-base-8M/` | Bundled embedding model assets. |
| `tests/` | Pytest suite. |
| `examples/` | Runnable examples. |
| `docs/` | Zensical documentation sources. |
| `zensical.toml` | Documentation site configuration. |

## Documentation workflow

Preview while editing:

```shell
uv run zensical serve
```

Build the static site:

```shell
uv run zensical build --clean --strict
```

The generated `site/` directory is ignored. GitHub Pages builds and publishes it from
`.github/workflows/docs.yml`.
