# Release Checklist

- Re-check the packaged model license and source metadata before publishing.
- Recompute model file SHA-256 values if any packaged model file changes.
- Run `ruff format`.
- Run `ruff check`.
- Run `pyright`.
- Run `pytest`.
- Build the wheel.
- Verify the wheel includes `jsonibase/py.typed`.
- Verify the wheel includes `jsonibase/models/potion-base-8M/**`.
- Confirm docs state that Git workflows are external.
