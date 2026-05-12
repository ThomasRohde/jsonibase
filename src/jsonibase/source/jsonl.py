from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import orjson
from pydantic import BaseModel, ValidationError

from jsonibase.config import CollectionSpec

JsonlErrorCode = Literal[
    "JSONL_BLANK_LINE",
    "JSONL_PARSE_ERROR",
    "JSONL_SCHEMA_ERROR",
]


class JsonlSourceError(Exception):
    def __init__(
        self,
        *,
        code: JsonlErrorCode,
        path: Path,
        line_number: int,
        message: str,
        collection: str | None = None,
    ) -> None:
        super().__init__(f"{path}:{line_number}: {code}: {message}")
        self.code = code
        self.path = path
        self.line_number = line_number
        self.message = message
        self.collection = collection


@dataclass(frozen=True)
class JsonlRecord[TRecord: BaseModel]:
    record: TRecord
    line_number: int
    source_sha256: str


def read_jsonl[TRecord: BaseModel](
    path: str | Path,
    spec: CollectionSpec[TRecord],
) -> list[JsonlRecord[TRecord]]:
    source_path = Path(path)
    records: list[JsonlRecord[TRecord]] = []
    if not source_path.exists():
        return records

    with source_path.open("rb") as source_file:
        for line_number, raw_line in enumerate(source_file, start=1):
            line = raw_line.rstrip(b"\n")
            if line.endswith(b"\r"):
                line = line[:-1]
            if not line.strip():
                raise JsonlSourceError(
                    code="JSONL_BLANK_LINE",
                    path=source_path,
                    line_number=line_number,
                    message="blank lines are not valid canonical JSONL",
                    collection=spec.name,
                )

            try:
                data = orjson.loads(line)
            except orjson.JSONDecodeError as exc:
                raise JsonlSourceError(
                    code="JSONL_PARSE_ERROR",
                    path=source_path,
                    line_number=line_number,
                    message=str(exc),
                    collection=spec.name,
                ) from exc

            try:
                record = spec.model.model_validate(data)
            except ValidationError as exc:
                raise JsonlSourceError(
                    code="JSONL_SCHEMA_ERROR",
                    path=source_path,
                    line_number=line_number,
                    message=str(exc),
                    collection=spec.name,
                ) from exc

            records.append(
                JsonlRecord(
                    record=record,
                    line_number=line_number,
                    source_sha256=_sha256(line),
                )
            )

    return records


def write_jsonl(path: str | Path, records: list[BaseModel] | tuple[BaseModel, ...]) -> None:
    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("wb") as target_file:
        for record in records:
            payload = record.model_dump(mode="json")
            target_file.write(orjson.dumps(payload, option=orjson.OPT_SORT_KEYS))
            target_file.write(b"\n")


def _sha256(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"
