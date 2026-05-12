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
    _emit(
        "guide",
        {
            "commands": [
                "guide",
                "init",
                "status",
                "validate",
                "build",
                "search",
                "get",
                "list",
                "plan",
                "apply",
            ]
        },
    )


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


def _run_json(command: str, callback: Any) -> None:
    try:
        callback()
    except JsonIBaseError as exc:
        _emit_error(command, exc)
    else:
        _emit(command, {})


def _emit(command: str, data: Any, *, ok: bool = True, exit_code: int = 0) -> None:
    typer.echo(json.dumps({"ok": ok, "command": command, "data": data}, sort_keys=True))
    raise typer.Exit(exit_code)


def _emit_error(command: str, error: JsonIBaseError) -> None:
    typer.echo(
        json.dumps(
            {
                "ok": False,
                "command": command,
                "error": {
                    "code": error.code,
                    "message": error.message,
                    "details": error.details,
                },
            },
            sort_keys=True,
        )
    )
    raise typer.Exit(1)
