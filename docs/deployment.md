# GitHub Pages

This repository is configured for GitHub Pages Project Pages with Zensical.

## Local build

```shell
uv sync --extra dev
uv run zensical build --clean --strict
```

The build output is `site/`, matching Zensical's default output directory and the Pages
workflow artifact path.

## Site URL

`zensical.toml` sets:

```toml
site_url = "https://thomasrohde.github.io/jsonibase/"
```

That is the expected Project Pages URL for `ThomasRohde/jsonibase`.

## Workflow

`.github/workflows/docs.yml` builds the docs on pushes to `main` or `master`, uploads
`site/` as a Pages artifact, and deploys with `actions/deploy-pages`.

The repository owner must configure GitHub Pages to use GitHub Actions as the source:

1. Open the repository on GitHub.
2. Go to Settings, then Pages.
3. Set Build and deployment source to GitHub Actions.
4. Push to `main` or `master`, or run the `Documentation` workflow manually.

The published site should appear at `https://thomasrohde.github.io/jsonibase/`.

## References

- [Zensical: Create your site](https://zensical.org/docs/create-your-site/)
- [Zensical: Publish your site](https://zensical.org/docs/publish-your-site/)
- [Zensical: Build](https://zensical.org/docs/usage/build/)
