from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

from pydantic import BaseModel

from jsonibase.config import CollectionSpec
from jsonibase.source.jsonl import JsonlRecord, JsonlSourceError, read_jsonl
from jsonibase.validation.findings import ValidationFinding, ValidationReport


@dataclass(frozen=True)
class ValidationContext:
    root: Path
    collections: dict[str, CollectionSpec[BaseModel]]
    records: dict[str, list[JsonlRecord[BaseModel]]]


class Validator(Protocol):
    name: str

    def validate(self, context: ValidationContext) -> list[ValidationFinding]: ...


def validate_workspace(
    root: str | Path,
    collections: list[CollectionSpec[BaseModel]] | tuple[CollectionSpec[BaseModel], ...],
    validators: list[Validator] | tuple[Validator, ...] = (),
) -> ValidationReport:
    root_path = Path(root)
    specs_by_name = {spec.name: spec for spec in collections}
    records_by_collection: dict[str, list[JsonlRecord[BaseModel]]] = {}
    findings: list[ValidationFinding] = []

    for spec in collections:
        source_path = Path(spec.path)
        if not source_path.is_absolute():
            source_path = root_path / source_path
        try:
            records_by_collection[spec.name] = read_jsonl(source_path, spec)
        except JsonlSourceError as exc:
            findings.append(_source_error_to_finding(exc))
            records_by_collection[spec.name] = []

    context = ValidationContext(
        root=root_path,
        collections=specs_by_name,
        records=records_by_collection,
    )
    findings.extend(_validate_identity(context))
    findings.extend(_validate_relationships(context))

    for validator in validators:
        findings.extend(validator.validate(context))

    return ValidationReport(findings=findings)


def _source_error_to_finding(error: JsonlSourceError) -> ValidationFinding:
    return ValidationFinding(
        level="error",
        code=error.code,
        collection=error.collection,
        message=error.message,
        details={
            "path": str(error.path),
            "line_number": error.line_number,
        },
    )


def _validate_identity(context: ValidationContext) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    for collection_name, records in context.records.items():
        spec = context.collections[collection_name]
        seen: dict[str, JsonlRecord[BaseModel]] = {}
        for record in records:
            record_id = str(getattr(record.record, spec.id_field))
            first = seen.get(record_id)
            if first is not None:
                findings.append(
                    ValidationFinding(
                        level="error",
                        code="DUPLICATE_ID",
                        collection=collection_name,
                        record_id=record_id,
                        message=f"duplicate id '{record_id}' in collection '{collection_name}'",
                        details={
                            "first_line_number": first.line_number,
                            "duplicate_line_number": record.line_number,
                        },
                    )
                )
            else:
                seen[record_id] = record
    return findings


def _validate_relationships(context: ValidationContext) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    target_indexes = _build_target_indexes(context)

    for collection_name, records in context.records.items():
        spec = context.collections[collection_name]
        for relationship in spec.relationships:
            target_values = target_indexes.get(
                (relationship.target_collection, relationship.target_field),
                set(),
            )
            for record in records:
                source_id = str(getattr(record.record, spec.id_field))
                raw_value = getattr(record.record, relationship.field)
                for target_id in _relationship_values(raw_value):
                    if target_id not in target_values:
                        findings.append(
                            ValidationFinding(
                                level="error",
                                code="RELATION_TARGET_MISSING",
                                collection=collection_name,
                                record_id=source_id,
                                message="relationship target does not exist",
                                details={
                                    "field": relationship.field,
                                    "target_collection": relationship.target_collection,
                                    "target_field": relationship.target_field,
                                    "target_id": target_id,
                                    "line_number": record.line_number,
                                },
                            )
                        )

    return findings


def _build_target_indexes(context: ValidationContext) -> dict[tuple[str, str], set[str]]:
    indexes: dict[tuple[str, str], set[str]] = {}
    for collection_name, spec in context.collections.items():
        records = context.records.get(collection_name, [])
        fields = {spec.id_field}
        for source_spec in context.collections.values():
            for relationship in source_spec.relationships:
                if relationship.target_collection == collection_name:
                    fields.add(relationship.target_field)
        for field_name in fields:
            indexes[(collection_name, field_name)] = {
                str(getattr(record.record, field_name)) for record in records
            }
    return indexes


def _relationship_values(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list | tuple | set):
        return [str(item) for item in cast(list[object] | tuple[object, ...] | set[object], value)]
    return [str(value)]
