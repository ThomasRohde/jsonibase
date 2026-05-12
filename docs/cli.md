# CLI

The `jsonibase` command is generic and JSON-only by default.

Implemented commands:

- `jsonibase guide`
- `jsonibase init`
- `jsonibase validate`
- `jsonibase build`
- `jsonibase status`
- `jsonibase search`
- `jsonibase get`
- `jsonibase list`

Commands accept `--root`, `--collection`, `--path`, `--fts`, `--embedding`, and
`--filter` options so simple JSONL workspaces can be inspected without writing
application-specific Python code.

Every command returns one envelope:

```json
{"ok": true, "command": "guide", "data": {}}
```

Errors use the same shape with `ok: false` and a structured `error` object.
