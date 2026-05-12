from __future__ import annotations

from collections.abc import Iterable
from typing import Any, cast

from pydantic import BaseModel

from jsonibase.config import CollectionSpec
from jsonibase.errors import JsonIBaseError


def filter_records(
    spec: CollectionSpec[BaseModel],
    records: list[BaseModel],
    filters: dict[str, Any] | None,
) -> list[BaseModel]:
    if not filters:
        return records

    allowed = set(spec.filter_fields)
    result = records
    for field_name, expression in filters.items():
        if field_name not in allowed:
            raise JsonIBaseError(
                "FILTER_FIELD_NOT_CONFIGURED",
                f"field '{field_name}' is not configured for filtering",
                details={"collection": spec.name, "field": field_name},
            )
        result = [record for record in result if _matches(getattr(record, field_name), expression)]
    return result


def sort_records(
    spec: CollectionSpec[BaseModel],
    records: list[BaseModel],
    sort: list[str] | tuple[str, ...] | None,
) -> list[BaseModel]:
    if not sort:
        return sorted(records, key=lambda record: str(getattr(record, spec.id_field)))

    allowed = set(spec.sort_fields)
    result = list(records)
    for sort_key in reversed(sort):
        descending = sort_key.startswith("-")
        field_name = sort_key[1:] if descending else sort_key
        if field_name not in allowed:
            raise JsonIBaseError(
                "SORT_FIELD_NOT_CONFIGURED",
                f"field '{field_name}' is not configured for sorting",
                details={"collection": spec.name, "field": field_name},
            )
        result.sort(
            key=lambda record, field=field_name: _sort_value(getattr(record, field)),
            reverse=descending,
        )
    return result


def paginate_records(
    records: list[BaseModel],
    *,
    offset: int = 0,
    limit: int | None = None,
) -> list[BaseModel]:
    if offset < 0:
        raise JsonIBaseError("PAGINATION_INVALID", "offset must be greater than or equal to zero")
    if limit is not None and limit < 0:
        raise JsonIBaseError("PAGINATION_INVALID", "limit must be greater than or equal to zero")
    if limit is None:
        return records[offset:]
    return records[offset : offset + limit]


def _matches(value: object, expression: object) -> bool:
    if not isinstance(expression, dict):
        raise JsonIBaseError(
            "FILTER_UNSUPPORTED",
            "filters must contain exactly one operator",
        )

    expression_dict = cast(dict[str, object], expression)
    if len(expression_dict) != 1:
        raise JsonIBaseError(
            "FILTER_UNSUPPORTED",
            "filters must contain exactly one operator",
        )

    operator, expected = next(iter(expression_dict.items()))
    if operator == "eq":
        return value == expected
    if operator == "ne":
        return value != expected
    if operator == "in":
        if not isinstance(expected, list | tuple | set):
            raise JsonIBaseError("FILTER_UNSUPPORTED", "'in' filter expects a sequence")
        return value in cast(Iterable[object], expected)
    if operator == "contains":
        if isinstance(value, list | tuple | set):
            return expected in cast(Iterable[object], value)
        return str(expected) in str(value)
    raise JsonIBaseError("FILTER_UNSUPPORTED", f"unsupported filter operator '{operator}'")


def _sort_value(value: object) -> tuple[str, str]:
    if value is None:
        return ("", "")
    return (type(value).__name__, str(value))
