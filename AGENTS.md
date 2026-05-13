# Repository Guidelines

## Project Structure & Module Organization

JsonIBase is a Python 3.13 package using the `src` layout. Core library code lives in
`src/jsonibase/`, with subpackages for `cli`, `embeddings`, `index`, `search`, `source`,
and `validation`. Public API entry points are `src/jsonibase/api.py` and
`src/jsonibase/__init__.py`. Tests are in `tests/`, such as
`test_search.py`, `test_cli.py`, and `test_validation.py`. Docs live in `docs/`, runnable
samples in `examples/`, and bundled model assets in `src/jsonibase/models/potion-base-8M/`.

## Build, Test, and Development Commands

- `uv sync --extra cli --extra dev`: install CLI and development dependencies.
- `uv run pytest`: run the full suite with strict pytest settings.
- `uv run pytest tests/test_search.py`: run one focused test module.
- `uv run ruff check src tests`: lint source and tests using the repository Ruff rules.
- `uv run pyright`: run strict type checking for `src/`.
- `uv run python -m build`: build source and wheel distributions into `dist/`.
- `uv run jsonibase guide`: smoke-test the installed CLI entry point.

## Coding Style & Naming Conventions

Use 4-space indentation and keep lines at or below 100 characters. Prefer typed,
explicit functions and Pydantic models for structured records. Use
`snake_case` for modules, functions, variables, and test names; use `PascalCase` for
classes and Pydantic models. Ruff enforces import ordering and lint rules including
`E`, `F`, `W`, `I`, `UP`, `B`, `SIM`, `RUF`, `C4`, and `PIE`. Keep package code typed;
the project ships `py.typed`.

## Testing Guidelines

Pytest is the main framework, with Hypothesis for property-based tests and
`pytest-benchmark` for performance-sensitive paths. Add tests under `tests/` with
names matching `test_*.py`. Prefer behavior-focused tests that exercise public APIs,
CLI output envelopes, JSONL source behavior, indexing, validation, and search ranking.
Run `uv run pytest` before opening a pull request; add `--cov=jsonibase` for shared
internals or public API changes.

## Commit & Pull Request Guidelines

History uses short, imperative commit subjects such as `Improve lexical search ranking`.
Keep commits focused and describe the observable change. Pull requests should include a
concise summary, relevant issue links, test commands run, and examples or CLI output when
behavior changes. Update `docs/`, `examples/`, or `README.md` when public APIs, commands,
or ingestion workflows change.

## Security & Configuration Tips

JSONL files are the source of truth and SQLite indexes are derived artifacts. Do not
commit local caches such as `.pytest_cache/`, `.ruff_cache/`, `.hypothesis/`, or
`.benchmarks/`. The default embedding provider should not require network calls during
normal operation; document any provider that changes that assumption.
