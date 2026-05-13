# Examples

The repository includes runnable examples under `examples/`.

## Basic usage

`examples/basic_usage.py` creates a temporary workspace, adds one standard, and searches
for it:

```shell
uv run python examples/basic_usage.py
```

Expected output:

```text
std_001
```

## Internet ingestion examples

These scripts fetch public structured datasets, normalize them into Pydantic models, and
write JsonIBase workspaces under `example-workspaces/` by default:

```shell
uv run python examples/ingest_peps.py --query "typing protocol"
uv run python examples/ingest_cisa_kev.py --query "ransomware remote code execution"
uv run python examples/ingest_rfc_index.py --query "transport congestion control"
```

Use `--root` to write elsewhere. The scripts are examples, not library requirements;
normal JsonIBase operation does not need network access.

## Testing examples

The test suite compiles the internet ingestion examples:

```shell
uv run pytest tests/test_examples.py
```
