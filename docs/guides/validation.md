# Validation

Validation checks whether the JSONL source files are safe to use as the canonical record
base.

```python
report = store.validate()
if not report.ok:
    for finding in report.findings:
        print(finding.code, finding.message)
```

The CLI command exits with status code `1` when validation has errors:

```shell
jsonibase validate --root . --collection standards --path data/standards.jsonl --fts title
```

## Built-in checks

| Check | Finding code |
|---|---|
| Blank JSONL line | `JSONL_BLANK_LINE` |
| Invalid JSON | `JSONL_PARSE_ERROR` |
| Pydantic schema error | `JSONL_SCHEMA_ERROR` |
| Duplicate ids in a collection | `DUPLICATE_ID` |
| Missing relationship target | `RELATION_TARGET_MISSING` |

`ValidationReport.ok` is true when no finding has level `error`.

## Relationships

Use `RelationshipSpec` to require values in one collection to exist in another:

```python
from jsonibase.config import RelationshipSpec

tasks = CollectionSpec[Task](
    name="tasks",
    path="data/tasks.jsonl",
    model=Task,
    relationships=[
        RelationshipSpec(
            field="owner_id",
            target_collection="owners",
            target_field="id",
        )
    ],
)
```

Relationship fields can be scalar values or lists, tuples, and sets.

## Custom validators

The validation engine accepts custom validators at the lower-level
`validate_workspace()` function. The public facade currently runs the built-in JSONL,
identity, and relationship checks.
