# Installation

JsonIBase requires Python 3.13 or newer.

## Install from PyPI

```shell
pip install jsonibase
```

The package includes the CLI entry point, core runtime dependencies, and the bundled
local embedding model.

## Install from a source checkout

Clone the repository and install the development extra with `uv`:

```shell
uv sync --extra cli --extra dev
uv run pytest
uv run jsonibase guide
```

Use `uv run` when invoking commands from the checkout so Python resolves the local
package and the locked development tools.

## Documentation tools

The documentation site is built with Zensical. It is part of the `dev` extra:

```shell
uv sync --extra dev
uv run zensical serve
uv run zensical build --clean --strict
```

`zensical serve` previews the site locally. `zensical build` writes the static site to
`site/`, which is ignored because GitHub Pages builds it in CI.
