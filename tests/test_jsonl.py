from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import BaseModel

from jsonibase import CollectionSpec
from jsonibase.source.jsonl import JsonlSourceError, read_jsonl, write_jsonl


class Standard(BaseModel):
    id: str
    title: str
    body: str
    status: str
    owner: str
    tags: list[str]
    updated_at: datetime | None = None


def test_write_jsonl_uses_canonical_sorted_keys_and_trailing_newline(tmp_path) -> None:
    path = tmp_path / "standards.jsonl"
    records = [
        Standard(
            id="std_001",
            title="Managed services",
            body="Prefer managed services where possible.",
            status="active",
            owner="platform",
            tags=["cloud", "platform"],
            updated_at=datetime(2026, 5, 12, 10, 15, tzinfo=UTC),
        )
    ]

    write_jsonl(path, records)

    assert path.read_text(encoding="utf-8") == (
        '{"body":"Prefer managed services where possible.",'
        '"id":"std_001",'
        '"owner":"platform",'
        '"status":"active",'
        '"tags":["cloud","platform"],'
        '"title":"Managed services",'
        '"updated_at":"2026-05-12T10:15:00Z"}\n'
    )


def test_read_jsonl_returns_typed_records_with_line_numbers(tmp_path) -> None:
    path = tmp_path / "standards.jsonl"
    path.write_text(
        '{"body":"Body","id":"std_001","owner":"platform","status":"active",'
        '"tags":["cloud"],"title":"Title","updated_at":null}\n',
        encoding="utf-8",
    )
    spec = CollectionSpec[Standard](
        name="standards",
        path=path,
        model=Standard,
    )

    records = read_jsonl(path, spec)

    assert len(records) == 1
    assert records[0].line_number == 1
    assert records[0].record.id == "std_001"
    assert records[0].source_sha256.startswith("sha256:")


def test_read_jsonl_rejects_blank_lines_with_file_and_line(tmp_path) -> None:
    path = tmp_path / "standards.jsonl"
    path.write_text(
        '{"body":"Body","id":"std_001","owner":"platform","status":"active",'
        '"tags":["cloud"],"title":"Title","updated_at":null}\n\n',
        encoding="utf-8",
    )
    spec = CollectionSpec[Standard](
        name="standards",
        path=path,
        model=Standard,
    )

    with pytest.raises(JsonlSourceError) as exc_info:
        read_jsonl(path, spec)

    assert exc_info.value.path == path
    assert exc_info.value.line_number == 2
    assert exc_info.value.code == "JSONL_BLANK_LINE"


def test_read_jsonl_rejects_invalid_json_with_file_and_line(tmp_path) -> None:
    path = tmp_path / "standards.jsonl"
    path.write_text('{"id":\n', encoding="utf-8")
    spec = CollectionSpec[Standard](
        name="standards",
        path=path,
        model=Standard,
    )

    with pytest.raises(JsonlSourceError) as exc_info:
        read_jsonl(path, spec)

    assert exc_info.value.path == path
    assert exc_info.value.line_number == 1
    assert exc_info.value.code == "JSONL_PARSE_ERROR"


def test_read_jsonl_rejects_schema_errors_with_collection_and_line(tmp_path) -> None:
    path = tmp_path / "standards.jsonl"
    path.write_text('{"id":"std_001"}\n', encoding="utf-8")
    spec = CollectionSpec[Standard](
        name="standards",
        path=path,
        model=Standard,
    )

    with pytest.raises(JsonlSourceError) as exc_info:
        read_jsonl(path, spec)

    assert exc_info.value.collection == "standards"
    assert exc_info.value.line_number == 1
    assert exc_info.value.code == "JSONL_SCHEMA_ERROR"
