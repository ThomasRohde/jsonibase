from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

DeletionPolicy = Literal["forbid", "tombstone", "hard"]
_COLLECTION_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


class RelationshipSpec(BaseModel):
    field: str
    target_collection: str
    target_field: str = "id"


class CollectionSpec[TRecord: BaseModel](BaseModel):
    """Configuration for one typed JSONL-backed collection."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    path: str | Path
    model: type[TRecord]
    id_field: str = "id"
    title_field: str | None = None
    fts_fields: tuple[str, ...] = Field(default_factory=tuple)
    embedding_fields: tuple[str, ...] = Field(default_factory=tuple)
    filter_fields: tuple[str, ...] = Field(default_factory=tuple)
    sort_fields: tuple[str, ...] = Field(default_factory=tuple)
    relationships: tuple[RelationshipSpec, ...] = Field(default_factory=tuple)
    redacted_fields: tuple[str, ...] = Field(default_factory=tuple)
    deletion: DeletionPolicy = "forbid"

    @model_validator(mode="after")
    def validate_spec(self) -> CollectionSpec[TRecord]:
        if not _COLLECTION_NAME_RE.fullmatch(self.name):
            raise ValueError("collection name must match ^[A-Za-z][A-Za-z0-9_]*$")

        model_fields = set(self.model.model_fields)
        allows_extra_fields = self.model.model_config.get("extra") == "allow"
        fields_to_check = [self.id_field]
        if self.title_field is not None:
            fields_to_check.append(self.title_field)
        fields_to_check.extend(self.fts_fields)
        fields_to_check.extend(self.embedding_fields)
        fields_to_check.extend(self.filter_fields)
        fields_to_check.extend(self.sort_fields)
        fields_to_check.extend(self.redacted_fields)

        for field_name in fields_to_check:
            if not allows_extra_fields and field_name not in model_fields:
                raise ValueError(f"unknown field '{field_name}' for collection '{self.name}'")

        for relationship in self.relationships:
            if not allows_extra_fields and relationship.field not in model_fields:
                raise ValueError(
                    f"unknown relationship field '{relationship.field}' "
                    f"for collection '{self.name}'"
                )

        return self


class JsonIBaseConfig(BaseModel):
    collections: tuple[CollectionSpec[BaseModel], ...]
    index_path: Path = Path(".jsonibase/jsonibase.db")
    rebuild_policy: Literal["eager", "lazy", "manual"] = "lazy"

    @property
    def fingerprint(self) -> str:
        return config_fingerprint(self.collections)


def config_fingerprint(
    collections: list[CollectionSpec[BaseModel]] | tuple[CollectionSpec[BaseModel], ...],
) -> str:
    payload = [_collection_fingerprint_payload(spec) for spec in collections]
    payload.sort(key=lambda item: str(item["name"]))
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _collection_fingerprint_payload(spec: CollectionSpec[BaseModel]) -> dict[str, object]:
    return {
        "name": spec.name,
        "path": str(spec.path).replace("\\", "/"),
        "model": f"{spec.model.__module__}.{spec.model.__qualname__}",
        "model_fields": sorted(spec.model.model_fields),
        "id_field": spec.id_field,
        "title_field": spec.title_field,
        "fts_fields": list(spec.fts_fields),
        "embedding_fields": list(spec.embedding_fields),
        "filter_fields": list(spec.filter_fields),
        "sort_fields": list(spec.sort_fields),
        "relationships": [
            relationship.model_dump(mode="json") for relationship in spec.relationships
        ],
        "redacted_fields": list(spec.redacted_fields),
        "deletion": spec.deletion,
    }
