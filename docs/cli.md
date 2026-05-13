# CLI

The `jsonibase` command is generic and JSON-only by default. In a source
checkout, run it through uv:

```shell
uv run jsonibase guide
```

The `guide` command is intentionally machine-readable. It returns the CLI
contract an agent needs: workspace invariants, common options, command-specific
required options, examples, output shapes, and safe workflows for inspect,
search, and mutation tasks.

Implemented commands:

- `jsonibase guide`
- `jsonibase init`
- `jsonibase validate`
- `jsonibase build`
- `jsonibase status`
- `jsonibase search`
- `jsonibase get`
- `jsonibase list`
- `jsonibase plan`
- `jsonibase apply`

Commands accept `--root`, `--collection`, `--path`, `--fts`, `--embedding`, and
`--filter` options so simple JSONL workspaces can be inspected without writing
application-specific Python code.

Every command returns one pretty-printed JSON envelope:

```json
{
  "command": "guide",
  "data": {
    "schema_version": 1
  },
  "ok": true
}
```

Errors use the same pretty-printed shape with `ok: false` and a structured
`error` object. Parse all stdout as one JSON document; the CLI does not emit
JSON Lines.
