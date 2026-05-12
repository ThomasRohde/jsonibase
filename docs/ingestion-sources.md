# Ingestion Sources

These sources are useful for JsonIBase examples because they are public, stable,
structured, and contain text plus metadata that benefits from FTS and semantic
search.

| Source | URL | Format | Why it is useful |
|---|---|---|---|
| Python PEPs API | `https://peps.python.org/api/peps.json` | JSON | Official Python metadata, moderate size, rich status/type/topic filters. |
| CISA Known Exploited Vulnerabilities | `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json` | JSON | Official vulnerability catalog with vendors, products, CVEs, remediation text, and ransomware flags. |
| RFC Editor index | `https://www.rfc-editor.org/rfc-index.xml` | XML | Official index of Internet standards and related documents with status, stream, author, and title metadata. |
| Python release-cycle API | `https://peps.python.org/api/release-cycle.json` | JSON | Small release lifecycle dataset, useful for demos that need compact records. |
| Python releases API | `https://peps.python.org/api/python-releases.json` | JSON | Larger release schedule dataset with nested metadata and release events. |

Example scripts:

```shell
uv run python examples/ingest_peps.py --query "typing protocol"
uv run python examples/ingest_cisa_kev.py --query "ransomware remote code execution"
uv run python examples/ingest_rfc_index.py --query "transport congestion control"
```

The scripts write example workspaces under `example-workspaces/` by default.
Use `--root` to write elsewhere.
