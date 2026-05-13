from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from pydantic import BaseModel, ConfigDict

from jsonibase import CollectionSpec, JsonIBase
from jsonibase.errors import JsonIBaseError

app = typer.Typer(add_completion=False, no_args_is_help=True)


class CliRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str


def main() -> None:
    app()


@app.command()
def guide() -> None:
    _emit("guide", _guide_payload())


@app.command()
def init(
    root: Path = typer.Option(Path("."), "--root"),
    collection: str = typer.Option(..., "--collection"),
    path: str = typer.Option(..., "--path"),
    fts: list[str] | None = typer.Option(None, "--fts"),
    embedding: list[str] | None = typer.Option(None, "--embedding"),
    filter_fields: list[str] | None = typer.Option(None, "--filter"),
) -> None:
    store = _store(root, collection, path, fts, embedding, filter_fields)
    store.init()
    _emit("init", {"root": str(root), "collection": collection, "path": path})


@app.command()
def validate(
    root: Path = typer.Option(Path("."), "--root"),
    collection: str = typer.Option(..., "--collection"),
    path: str = typer.Option(..., "--path"),
    fts: list[str] | None = typer.Option(None, "--fts"),
    embedding: list[str] | None = typer.Option(None, "--embedding"),
    filter_fields: list[str] | None = typer.Option(None, "--filter"),
) -> None:
    store = _store(root, collection, path, fts, embedding, filter_fields)
    report = store.validate()
    _emit(
        "validate",
        report.model_dump(mode="json"),
        ok=report.ok,
        exit_code=0 if report.ok else 1,
    )


@app.command()
def build(
    root: Path = typer.Option(Path("."), "--root"),
    collection: str = typer.Option(..., "--collection"),
    path: str = typer.Option(..., "--path"),
    fts: list[str] | None = typer.Option(None, "--fts"),
    embedding: list[str] | None = typer.Option(None, "--embedding"),
    filter_fields: list[str] | None = typer.Option(None, "--filter"),
) -> None:
    store = _store(root, collection, path, fts, embedding, filter_fields)
    _run_json("build", lambda: store.rebuild())


@app.command()
def status(
    root: Path = typer.Option(Path("."), "--root"),
    collection: str = typer.Option(..., "--collection"),
    path: str = typer.Option(..., "--path"),
    fts: list[str] | None = typer.Option(None, "--fts"),
    embedding: list[str] | None = typer.Option(None, "--embedding"),
    filter_fields: list[str] | None = typer.Option(None, "--filter"),
) -> None:
    store = _store(root, collection, path, fts, embedding, filter_fields)
    _emit("status", store.status().model_dump(mode="json"))


@app.command()
def get(
    root: Path = typer.Option(Path("."), "--root"),
    collection: str = typer.Option(..., "--collection"),
    path: str = typer.Option(..., "--path"),
    record_id: str = typer.Option(..., "--id"),
    fts: list[str] | None = typer.Option(None, "--fts"),
    embedding: list[str] | None = typer.Option(None, "--embedding"),
    filter_fields: list[str] | None = typer.Option(None, "--filter"),
) -> None:
    store = _store(root, collection, path, fts, embedding, filter_fields)
    record = store.get(collection, record_id)
    _emit("get", {"record": _record_payload(record)})


@app.command("list")
def list_command(
    root: Path = typer.Option(Path("."), "--root"),
    collection: str = typer.Option(..., "--collection"),
    path: str = typer.Option(..., "--path"),
    fts: list[str] | None = typer.Option(None, "--fts"),
    embedding: list[str] | None = typer.Option(None, "--embedding"),
    filter_fields: list[str] | None = typer.Option(None, "--filter"),
    filter_eq: list[str] | None = typer.Option(None, "--filter-eq"),
) -> None:
    store = _store(root, collection, path, fts, embedding, filter_fields)
    records = store.list(collection, filters=_parse_eq_filters(filter_eq))
    _emit("list", {"records": [_record_payload(record) for record in records]})


@app.command()
def search(
    root: Path = typer.Option(Path("."), "--root"),
    collection: str = typer.Option(..., "--collection"),
    path: str = typer.Option(..., "--path"),
    query: str = typer.Option(..., "--query"),
    fts: list[str] | None = typer.Option(None, "--fts"),
    embedding: list[str] | None = typer.Option(None, "--embedding"),
    filter_fields: list[str] | None = typer.Option(None, "--filter"),
    filter_eq: list[str] | None = typer.Option(None, "--filter-eq"),
    top: int = typer.Option(10, "--top"),
) -> None:
    store = _store(root, collection, path, fts, embedding, filter_fields)
    results = store.search(
        collection,
        query,
        filters=_parse_eq_filters(filter_eq),
        top=top,
    )
    _emit("search", {"results": [result.model_dump(mode="json") for result in results]})


@app.command()
def plan(
    root: Path = typer.Option(Path("."), "--root"),
    collection: str = typer.Option(..., "--collection"),
    path: str = typer.Option(..., "--path"),
    op: str = typer.Option(..., "--op"),
    record: str | None = typer.Option(None, "--record"),
    record_id: str | None = typer.Option(None, "--id"),
    patch: str | None = typer.Option(None, "--patch"),
    fts: list[str] | None = typer.Option(None, "--fts"),
    embedding: list[str] | None = typer.Option(None, "--embedding"),
    filter_fields: list[str] | None = typer.Option(None, "--filter"),
) -> None:
    store = _store(root, collection, path, fts, embedding, filter_fields)
    change_plan = _change_plan(store, collection, op, record, record_id, patch)
    _emit("plan", change_plan.preview().model_dump(mode="json"))


@app.command()
def apply(
    root: Path = typer.Option(Path("."), "--root"),
    collection: str = typer.Option(..., "--collection"),
    path: str = typer.Option(..., "--path"),
    op: str = typer.Option(..., "--op"),
    record: str | None = typer.Option(None, "--record"),
    record_id: str | None = typer.Option(None, "--id"),
    patch: str | None = typer.Option(None, "--patch"),
    fts: list[str] | None = typer.Option(None, "--fts"),
    embedding: list[str] | None = typer.Option(None, "--embedding"),
    filter_fields: list[str] | None = typer.Option(None, "--filter"),
) -> None:
    store = _store(root, collection, path, fts, embedding, filter_fields)
    change_plan = _change_plan(store, collection, op, record, record_id, patch)
    result = store.apply(change_plan)
    _emit("apply", result.model_dump(mode="json"))


def _store(
    root: Path,
    collection: str,
    path: str,
    fts: list[str] | None,
    embedding: list[str] | None,
    filter_fields: list[str] | None,
) -> JsonIBase:
    fts_fields = tuple(fts or ())
    embedding_fields = tuple(embedding or ())
    configured_filter_fields = tuple(filter_fields or ())
    record_model = _record_model([*fts_fields, *embedding_fields, *configured_filter_fields])
    spec = CollectionSpec(
        name=collection,
        path=path,
        model=record_model,
        id_field="id",
        fts_fields=fts_fields,
        embedding_fields=embedding_fields,
        filter_fields=configured_filter_fields,
    )
    return JsonIBase.open(root=root, collections=[spec], rebuild_policy="lazy")


def _record_model(fields: list[str]) -> type[BaseModel]:
    _ = fields
    return CliRecord


def _parse_eq_filters(filters: list[str] | None) -> dict[str, dict[str, str]]:
    parsed: dict[str, dict[str, str]] = {}
    for item in filters or []:
        if "=" not in item:
            raise JsonIBaseError(
                "CLI_FILTER_INVALID",
                "filters must use field=value syntax",
                details={"filter": item},
            )
        field_name, value = item.split("=", 1)
        parsed[field_name] = {"eq": value}
    return parsed


def _change_plan(
    store: JsonIBase,
    collection: str,
    op: str,
    record: str | None,
    record_id: str | None,
    patch: str | None,
):
    change_plan = store.plan()
    if op in {"add", "upsert"}:
        if record is None:
            raise JsonIBaseError("CLI_RECORD_REQUIRED", "--record is required")
        parsed_record = CliRecord.model_validate(json.loads(record))
        if op == "add":
            change_plan.add(collection, parsed_record)
        else:
            change_plan.upsert(collection, parsed_record)
        return change_plan

    if op == "update":
        if record_id is None or patch is None:
            raise JsonIBaseError("CLI_PATCH_REQUIRED", "--id and --patch are required")
        change_plan.update(collection, record_id, json.loads(patch))
        return change_plan

    raise JsonIBaseError(
        "CLI_OPERATION_UNSUPPORTED",
        "operation must be add, update, or upsert",
        details={"op": op},
    )


def _record_payload(record: BaseModel | None) -> dict[str, Any] | None:
    if record is None:
        return None
    return record.model_dump(mode="json")


def _guide_payload() -> dict[str, Any]:
    common_options = {
        "--root": "Workspace root. Defaults to the current directory.",
        "--collection": "Logical collection name. Required for workspace commands.",
        "--path": "JSONL source path for the collection, relative to --root unless absolute.",
        "--fts": "Repeatable field name to include in full-text search.",
        "--embedding": "Repeatable field name to include in local embedding text.",
        "--filter": "Repeatable field name allowed in --filter-eq expressions.",
    }
    collection_example = [
        "--root",
        ".",
        "--collection",
        "standards",
        "--path",
        "data/standards.jsonl",
        "--fts",
        "title",
        "--fts",
        "body",
        "--embedding",
        "title",
        "--embedding",
        "body",
        "--filter",
        "status",
    ]
    filter_eq_help = (
        "Repeatable field=value filter. Field must also be declared with --filter."
    )
    record_json = (
        '{"id":"std_001","title":"Managed services","body":"Prefer managed services.",'
        '"status":"active"}'
    )
    return {
        "schema_version": 1,
        "purpose": (
            "Manage a local JsonIBase workspace: typed JSONL source files plus a derived "
            "SQLite FTS/vector search index."
        ),
        "run": {
            "installed": "jsonibase guide",
            "from_repo": "uv run jsonibase guide",
            "python_module": "uv run python -m jsonibase.cli.main guide",
        },
        "invariants": [
            "JSONL files are the source of truth.",
            "SQLite index files under .jsonibase/ are derived artifacts.",
            "Every source record must include an id field.",
            "CLI output is a pretty-printed JSON envelope.",
            "The CLI does not perform Git or GitHub actions.",
        ],
        "output_envelope": {
            "success": {"ok": True, "command": "<command>", "data": "<command result>"},
            "error": {
                "ok": False,
                "command": "<command>",
                "error": {
                    "code": "<stable error code>",
                    "message": "<human message>",
                    "details": "<structured details>",
                },
            },
            "parsing": "Parse all stdout as one JSON document. Do not expect JSON Lines.",
        },
        "common_options": common_options,
        "commands": {
            "guide": {
                "purpose": "Return this machine-readable usage guide.",
                "example": ["jsonibase", "guide"],
            },
            "init": {
                "purpose": "Create metadata directories and the configured JSONL file if missing.",
                "required_options": ["--root", "--collection", "--path"],
                "common_options_supported": True,
                "example": ["jsonibase", "init", *collection_example],
                "data_shape": {"root": "string", "collection": "string", "path": "string"},
            },
            "validate": {
                "purpose": "Validate source JSONL syntax, record schema, ids, and relationships.",
                "required_options": ["--root", "--collection", "--path"],
                "common_options_supported": True,
                "example": ["jsonibase", "validate", *collection_example],
                "data_shape": {"ok": "boolean", "findings": "list"},
            },
            "build": {
                "purpose": "Rebuild the derived SQLite index from JSONL source files.",
                "required_options": ["--root", "--collection", "--path"],
                "common_options_supported": True,
                "example": ["jsonibase", "build", *collection_example],
                "data_shape": {},
            },
            "status": {
                "purpose": "Report whether the derived index is fresh, missing, stale, or invalid.",
                "required_options": ["--root", "--collection", "--path"],
                "common_options_supported": True,
                "example": ["jsonibase", "status", *collection_example],
                "data_shape": {
                    "index_exists": "boolean",
                    "stale": "boolean",
                    "reason": [
                        "fresh",
                        "missing",
                        "invalid",
                        "source_changed",
                        "config_changed",
                        "embedding_changed",
                    ],
                },
            },
            "search": {
                "purpose": "Search a collection using hybrid FTS plus local embeddings by default.",
                "required_options": ["--root", "--collection", "--path", "--query"],
                "common_options_supported": True,
                "extra_options": {
                    "--query": "Search text.",
                    "--filter-eq": filter_eq_help,
                    "--top": "Maximum number of results. Defaults to 10.",
                },
                "example": [
                    "jsonibase",
                    "search",
                    *collection_example,
                    "--query",
                    "managed services",
                    "--filter-eq",
                    "status=active",
                    "--top",
                    "5",
                ],
                "data_shape": {"results": "list of SearchResult objects"},
            },
            "get": {
                "purpose": "Read one source record by id. Does not require a fresh index.",
                "required_options": ["--root", "--collection", "--path", "--id"],
                "common_options_supported": True,
                "extra_options": {"--id": "Record id."},
                "example": ["jsonibase", "get", *collection_example, "--id", "std_001"],
                "data_shape": {"record": "object|null"},
            },
            "list": {
                "purpose": "Read source records, optionally filtered with equality filters.",
                "required_options": ["--root", "--collection", "--path"],
                "common_options_supported": True,
                "extra_options": {"--filter-eq": filter_eq_help},
                "example": [
                    "jsonibase",
                    "list",
                    *collection_example,
                    "--filter-eq",
                    "status=active",
                ],
                "data_shape": {"records": "list of record objects"},
            },
            "plan": {
                "purpose": "Preview a source mutation without writing it.",
                "required_options": ["--root", "--collection", "--path", "--op"],
                "common_options_supported": True,
                "extra_options": {
                    "--op": "add, update, or upsert.",
                    "--record": "JSON object string for add or upsert. Must include id.",
                    "--id": "Record id for update.",
                    "--patch": "JSON object string for update.",
                },
                "examples": [
                    [
                        "jsonibase",
                        "plan",
                        *collection_example,
                        "--op",
                        "upsert",
                        "--record",
                        record_json,
                    ],
                    [
                        "jsonibase",
                        "plan",
                        *collection_example,
                        "--op",
                        "update",
                        "--id",
                        "std_001",
                        "--patch",
                        '{"status":"retired"}',
                    ],
                ],
                "data_shape": {"change_set_id": "string", "operations": "list"},
            },
            "apply": {
                "purpose": "Apply a source mutation transactionally after validation.",
                "required_options": ["--root", "--collection", "--path", "--op"],
                "common_options_supported": True,
                "extra_options": {
                    "--op": "add, update, or upsert.",
                    "--record": "JSON object string for add or upsert. Must include id.",
                    "--id": "Record id for update.",
                    "--patch": "JSON object string for update.",
                },
                "example": [
                    "jsonibase",
                    "apply",
                    *collection_example,
                    "--op",
                    "upsert",
                    "--record",
                    record_json,
                ],
                "data_shape": {"change_set_id": "string", "changed_files": "list"},
            },
        },
        "agent_workflows": [
            {
                "name": "Inspect an existing workspace",
                "steps": [
                    "Run guide to learn the contract.",
                    "Run status with the same collection options the user expects.",
                    "Run validate if status is invalid or source correctness matters.",
                    "Run get, list, or search depending on the task.",
                ],
            },
            {
                "name": "Create and search a simple workspace",
                "steps": [
                    "Run init with --root, --collection, --path, and field options.",
                    "Use apply --op upsert --record JSON to add records.",
                    "Run build, or let search lazily rebuild a stale index.",
                    "Run search with --query and optional --filter-eq.",
                ],
            },
            {
                "name": "Mutate safely",
                "steps": [
                    "Run plan first for add, update, or upsert.",
                    "Inspect data.operations and record ids.",
                    "Run apply only when the planned operation matches the user request.",
                    "Run validate or status afterward if the caller needs verification.",
                ],
            },
        ],
        "notes_for_agents": [
            "Use uv run jsonibase ... inside an uninstalled source checkout.",
            "Repeat --fts, --embedding, and --filter for multiple fields.",
            "Pass --record and --patch as valid JSON object strings.",
            "For PowerShell, escape inner JSON quotes or use single quotes around the JSON.",
            (
                "Keep collection configuration options consistent across init, build, "
                "status, and search."
            ),
            "Use --filter to declare fields before using --filter-eq field=value.",
        ],
    }


def _run_json(command: str, callback: Any) -> None:
    try:
        callback()
    except JsonIBaseError as exc:
        _emit_error(command, exc)
    else:
        _emit(command, {})


def _emit(command: str, data: Any, *, ok: bool = True, exit_code: int = 0) -> None:
    typer.echo(_json_dump({"ok": ok, "command": command, "data": data}))
    raise typer.Exit(exit_code)


def _emit_error(command: str, error: JsonIBaseError) -> None:
    typer.echo(
        _json_dump(
            {
                "ok": False,
                "command": command,
                "error": {
                    "code": error.code,
                    "message": error.message,
                    "details": error.details,
                },
            }
        )
    )
    raise typer.Exit(1)


def _json_dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)
