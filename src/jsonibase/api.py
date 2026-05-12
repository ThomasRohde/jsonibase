from __future__ import annotations

import json
import shutil
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Self, cast
from uuid import uuid4

import portalocker
from pydantic import BaseModel

from jsonibase.config import CollectionSpec
from jsonibase.embeddings import EmbeddingProvider
from jsonibase.errors import JsonIBaseError
from jsonibase.index import (
    DEFAULT_EMBEDDING_FINGERPRINT,
    DEFAULT_EMBEDDING_PROVIDER,
    DISABLED_EMBEDDING_FINGERPRINT,
    IndexStatus,
    index_status,
    rebuild_index,
)
from jsonibase.models import ChangeResult, ChangeSet, RecoveryReport, SearchResult, SourceManifest
from jsonibase.search import search_index
from jsonibase.search.filters import filter_records, paginate_records, sort_records
from jsonibase.source.jsonl import read_jsonl, write_jsonl
from jsonibase.source.manifest import build_source_manifest
from jsonibase.validation import ValidationReport, validate_workspace


@dataclass
class ChangePlan:
    store: JsonIBase
    operations: list[dict[str, Any]] = field(default_factory=lambda: list[dict[str, Any]]())

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def add(self, collection: str, record: BaseModel) -> None:
        self.operations.append({"op": "add", "collection": collection, "record": record})

    def update(self, collection: str, record_id: str, patch: dict[str, Any]) -> None:
        self.operations.append(
            {"op": "update", "collection": collection, "record_id": record_id, "patch": patch}
        )

    def upsert(self, collection: str, record: BaseModel) -> None:
        self.operations.append({"op": "upsert", "collection": collection, "record": record})

    def preview(self) -> ChangeSet:
        return ChangeSet(
            change_set_id=f"plan_{uuid4().hex}",
            base_manifest=self.store.source_manifest(),
            operations=[self._preview_operation(operation) for operation in self.operations],
        )

    def _preview_operation(self, operation: dict[str, Any]) -> dict[str, Any]:
        preview = {
            "op": operation["op"],
            "collection": operation["collection"],
        }
        if "record_id" in operation:
            preview["record_id"] = operation["record_id"]
        elif "record" in operation:
            spec = self.store.collection_spec(operation["collection"])
            preview["record_id"] = self.store.record_id_for(spec, operation["record"])
        return preview


@dataclass(frozen=True)
class JsonIBase:
    """Main facade for a JsonIBase workspace."""

    root: Path
    collections: tuple[CollectionSpec[BaseModel], ...]
    index_path: Path
    rebuild_policy: str = "lazy"
    embedding_provider: Any | None = None
    embeddings_enabled: bool = True

    @classmethod
    def open(
        cls,
        root: str | Path,
        collections: list[CollectionSpec[BaseModel]] | tuple[CollectionSpec[BaseModel], ...],
        index_path: str | Path = ".jsonibase/jsonibase.db",
        rebuild_policy: str = "lazy",
        embedding_provider: EmbeddingProvider | None = None,
        embeddings_enabled: bool = True,
    ) -> Self:
        root_path = Path(root)
        return cls(
            root=root_path,
            collections=tuple(collections),
            index_path=root_path / index_path,
            rebuild_policy=rebuild_policy,
            embedding_provider=embedding_provider,
            embeddings_enabled=embeddings_enabled,
        )

    def init(self) -> None:
        self._metadata_dir.mkdir(parents=True, exist_ok=True)
        self._locks_dir.mkdir(parents=True, exist_ok=True)
        self._transactions_dir.mkdir(parents=True, exist_ok=True)
        for spec in self.collections:
            source_path = self._source_path(spec)
            source_path.parent.mkdir(parents=True, exist_ok=True)
            if not source_path.exists():
                source_path.write_bytes(b"")

    def validate(self) -> ValidationReport:
        return validate_workspace(self.root, self.collections)

    def source_manifest(self) -> SourceManifest:
        return build_source_manifest(
            root=self.root,
            collections=self.collections,
            embedding_fingerprint=self._embedding_fingerprint,
        )

    def recover(self, *, auto: bool = False) -> RecoveryReport:
        self.init()
        transactions = self._incomplete_transactions()
        if not auto:
            return RecoveryReport(
                recovery_required=bool(transactions),
                transactions=[transaction for _, transaction in transactions],
            )

        recovered: list[str] = []
        for transaction_dir, transaction in transactions:
            recovered.append(str(transaction.get("transaction_id", transaction_dir.name)))
            self._remove_transaction_dir(transaction_dir)
        return RecoveryReport(recovery_required=False, recovered=recovered)

    def plan(self) -> ChangePlan:
        return ChangePlan(self)

    def apply(self, plan: ChangePlan) -> ChangeResult:
        return self._apply_operations(plan.operations)

    def status(self) -> IndexStatus:
        return index_status(
            root=self.root,
            collections=self.collections,
            index_path=self.index_path,
            embedding_fingerprint=self._embedding_fingerprint,
        )

    def rebuild(self) -> None:
        rebuild_index(
            root=self.root,
            collections=self.collections,
            index_path=self.index_path,
            embedding_fingerprint=self._embedding_fingerprint,
            embedding_provider=self._embedding_provider if self.embeddings_enabled else None,
            embeddings_enabled=self.embeddings_enabled,
        )

    def search(
        self,
        collection: str,
        query: str,
        *,
        filters: dict[str, Any] | None = None,
        top: int = 10,
        mode: Literal["hybrid", "fts", "vector"] = "hybrid",
    ) -> list[SearchResult]:
        if mode not in {"hybrid", "fts", "vector"}:
            raise JsonIBaseError(
                "SEARCH_MODE_UNSUPPORTED",
                f"unsupported search mode '{mode}'",
                details={"mode": mode},
            )
        if not self.embeddings_enabled and mode == "vector":
            return []
        effective_mode = "fts" if not self.embeddings_enabled and mode == "hybrid" else mode
        self._ensure_index_ready()
        return search_index(
            index_path=self.index_path,
            spec=self._collection(collection),
            query=query,
            mode=effective_mode,
            filters=filters,
            top=top,
            embedding_provider=self._embedding_provider,
        )

    def add(self, collection: str, record: BaseModel) -> ChangeResult:
        spec = self._collection(collection)
        records = self._load_collection(spec)
        record_id = self._record_id(spec, record)
        if any(self._record_id(spec, existing) == record_id for existing in records):
            raise JsonIBaseError(
                "DUPLICATE_ID",
                f"record '{record_id}' already exists in collection '{collection}'",
                details={"collection": collection, "record_id": record_id},
            )

        next_records = [*records, spec.model.model_validate(record)]
        return self._commit_collection(
            spec=spec,
            records=next_records,
            before={},
            after=record.model_dump(mode="json"),
        )

    def update(self, collection: str, record_id: str, patch: dict[str, Any]) -> ChangeResult:
        spec = self._collection(collection)
        records = self._load_collection(spec)
        next_records: list[BaseModel] = []
        before: dict[str, Any] | None = None
        after: dict[str, Any] | None = None

        unknown_fields = set(patch) - set(spec.model.model_fields)
        if unknown_fields:
            raise JsonIBaseError(
                "UNKNOWN_FIELD",
                f"unknown patch field '{sorted(unknown_fields)[0]}'",
                details={"fields": sorted(unknown_fields)},
            )

        for record in records:
            if self._record_id(spec, record) == record_id:
                before = record.model_dump(mode="json")
                payload = {**before, **patch}
                updated = spec.model.model_validate(payload)
                after = updated.model_dump(mode="json")
                next_records.append(updated)
            else:
                next_records.append(record)

        if before is None or after is None:
            raise JsonIBaseError(
                "RECORD_NOT_FOUND",
                f"record '{record_id}' does not exist in collection '{collection}'",
                details={"collection": collection, "record_id": record_id},
            )

        return self._commit_collection(spec=spec, records=next_records, before=before, after=after)

    def upsert(self, collection: str, record: BaseModel) -> ChangeResult:
        spec = self._collection(collection)
        records = self._load_collection(spec)
        record = spec.model.model_validate(record)
        record_id = self._record_id(spec, record)
        next_records: list[BaseModel] = []
        before: dict[str, Any] = {}
        replaced = False

        for existing in records:
            if self._record_id(spec, existing) == record_id:
                before = existing.model_dump(mode="json")
                next_records.append(record)
                replaced = True
            else:
                next_records.append(existing)

        if not replaced:
            next_records.append(record)

        return self._commit_collection(
            spec=spec,
            records=next_records,
            before=before,
            after=record.model_dump(mode="json"),
        )

    def get(self, collection: str, record_id: str) -> BaseModel | None:
        spec = self._collection(collection)
        for record in self._load_collection(spec):
            if self._record_id(spec, record) == record_id:
                return record
        return None

    def list(
        self,
        collection: str,
        *,
        filters: dict[str, Any] | None = None,
        sort: list[str] | tuple[str, ...] | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[BaseModel]:
        spec = self._collection(collection)
        records = self._load_collection(spec)
        records = filter_records(spec, records, filters)
        records = sort_records(spec, records, sort)
        return paginate_records(records, offset=offset, limit=limit)

    @property
    def _metadata_dir(self) -> Path:
        return self.index_path.parent

    @property
    def _locks_dir(self) -> Path:
        return self._metadata_dir / "locks"

    @property
    def _transactions_dir(self) -> Path:
        return self._metadata_dir / "transactions"

    @property
    def _embedding_provider(self) -> EmbeddingProvider:
        if self.embedding_provider is not None:
            return cast(EmbeddingProvider, self.embedding_provider)
        return DEFAULT_EMBEDDING_PROVIDER

    @property
    def _embedding_fingerprint(self) -> str:
        if not self.embeddings_enabled:
            return DISABLED_EMBEDDING_FINGERPRINT
        if self.embedding_provider is not None:
            return self.embedding_provider.fingerprint
        return DEFAULT_EMBEDDING_FINGERPRINT

    def _ensure_index_ready(self) -> None:
        status = self.status()
        if not status.stale:
            return
        if self.rebuild_policy in {"lazy", "eager"}:
            self.rebuild()
            return
        raise JsonIBaseError(
            "INDEX_STALE",
            "index is stale and rebuild_policy is manual",
            details={"reason": status.reason},
        )

    def _collection(self, name: str) -> CollectionSpec[BaseModel]:
        return self.collection_spec(name)

    def collection_spec(self, name: str) -> CollectionSpec[BaseModel]:
        for spec in self.collections:
            if spec.name == name:
                return spec
        raise JsonIBaseError(
            "COLLECTION_NOT_FOUND",
            f"collection '{name}' is not configured",
            details={"collection": name},
        )

    def _source_path(self, spec: CollectionSpec[BaseModel]) -> Path:
        path = Path(spec.path)
        return path if path.is_absolute() else self.root / path

    def _load_collection(self, spec: CollectionSpec[BaseModel]) -> list[BaseModel]:
        return [entry.record for entry in read_jsonl(self._source_path(spec), spec)]

    def _commit_collection(
        self,
        *,
        spec: CollectionSpec[BaseModel],
        records: list[BaseModel],
        before: dict[str, Any],
        after: dict[str, Any],
    ) -> ChangeResult:
        return self._commit_collections(
            changed_records={spec.name: records},
            before=before,
            after=after,
        )

    def _commit_collections(
        self,
        *,
        changed_records: dict[str, list[BaseModel]],
        before: dict[str, Any],
        after: dict[str, Any],
    ) -> ChangeResult:
        self.init()
        transactions = self._incomplete_transactions()
        if transactions:
            raise JsonIBaseError(
                "TRANSACTION_RECOVERY_REQUIRED",
                "incomplete transaction journals must be recovered before writing",
                details={
                    "transactions": [transaction for _, transaction in transactions],
                },
            )
        transaction_id = f"tx_{uuid4().hex}"
        lock_path = self._locks_dir / "source.lock"

        with portalocker.Lock(lock_path, timeout=10):
            transaction_dir = self._transactions_dir / transaction_id
            staging_root = transaction_dir / "source"
            transaction_dir.mkdir(parents=True, exist_ok=False)
            try:
                self._stage_sources(staging_root, changed_records)
                report = validate_workspace(staging_root, self.collections)
                if not report.ok:
                    raise JsonIBaseError(
                        "VALIDATION_FAILED",
                        "staged mutation failed validation",
                        details={"findings": [finding.model_dump() for finding in report.findings]},
                    )

                changed_specs = [self._collection(name) for name in changed_records]
                journal_path = transaction_dir / "journal.json"
                journal_path.write_text(
                    json.dumps(
                        {
                            "transaction_id": transaction_id,
                            "state": "prepared",
                            "files": [
                                {
                                    "path": str(Path(changed_spec.path).as_posix()),
                                    "staged_path": str(staging_root / Path(changed_spec.path)),
                                }
                                for changed_spec in changed_specs
                            ],
                        },
                        sort_keys=True,
                    ),
                    encoding="utf-8",
                )
                changed_files: list[Path] = []
                for changed_spec in changed_specs:
                    target_path = self._source_path(changed_spec)
                    staged_path = staging_root / Path(changed_spec.path)
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    staged_path.replace(target_path)
                    changed_files.append(target_path)
                return ChangeResult(
                    change_set_id=transaction_id,
                    changed_files=changed_files,
                    before=before,
                    after=after,
                )
            finally:
                self._remove_transaction_dir(transaction_dir)

    def _stage_sources(
        self,
        staging_root: Path,
        changed_records: Mapping[str, Iterable[BaseModel]],
    ) -> None:
        for spec in self.collections:
            staged_path = staging_root / Path(spec.path)
            staged_path.parent.mkdir(parents=True, exist_ok=True)
            if spec.name in changed_records:
                write_jsonl(staged_path, tuple(changed_records[spec.name]))
                continue

            source_path = self._source_path(spec)
            if source_path.exists():
                shutil.copyfile(source_path, staged_path)
            else:
                staged_path.write_bytes(b"")

    def _remove_transaction_dir(self, transaction_dir: Path) -> None:
        resolved_transaction = transaction_dir.resolve()
        resolved_parent = self._transactions_dir.resolve()
        if resolved_parent not in resolved_transaction.parents:
            raise JsonIBaseError(
                "TRANSACTION_CLEANUP_REFUSED",
                "refusing to remove a transaction directory outside the transaction root",
                details={"transaction_dir": str(transaction_dir)},
            )
        shutil.rmtree(resolved_transaction, ignore_errors=True)

    def _incomplete_transactions(self) -> list[tuple[Path, dict[str, Any]]]:
        if not self._transactions_dir.exists():
            return []

        transactions: list[tuple[Path, dict[str, Any]]] = []
        for transaction_dir in sorted(self._transactions_dir.iterdir()):
            journal_path = transaction_dir / "journal.json"
            if not transaction_dir.is_dir() or not journal_path.exists():
                continue
            try:
                transaction = json.loads(journal_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                transaction = {
                    "transaction_id": transaction_dir.name,
                    "state": "unknown",
                    "error": "journal could not be decoded",
                }
            transactions.append((transaction_dir, transaction))
        return transactions

    def _apply_operations(self, operations: list[dict[str, Any]]) -> ChangeResult:
        records_by_collection = {
            spec.name: self._load_collection(spec) for spec in self.collections
        }
        changed: dict[str, list[BaseModel]] = {}
        before: dict[str, Any] = {}
        after: dict[str, Any] = {}

        for operation in operations:
            collection = operation["collection"]
            spec = self._collection(collection)
            records = records_by_collection[collection]
            op = operation["op"]

            if op == "add":
                record = spec.model.model_validate(operation["record"])
                record_id = self._record_id(spec, record)
                if any(self._record_id(spec, existing) == record_id for existing in records):
                    raise JsonIBaseError(
                        "DUPLICATE_ID",
                        f"record '{record_id}' already exists in collection '{collection}'",
                    )
                records.append(record)
                after[f"{collection}:{record_id}"] = record.model_dump(mode="json")
            elif op == "update":
                record_id = operation["record_id"]
                patch = operation["patch"]
                records_by_collection[collection] = self._apply_update_operation(
                    spec,
                    records,
                    record_id,
                    patch,
                    before,
                    after,
                )
            elif op == "upsert":
                record = spec.model.model_validate(operation["record"])
                records_by_collection[collection] = self._apply_upsert_operation(
                    spec,
                    records,
                    record,
                    before,
                    after,
                )
            else:
                raise JsonIBaseError("OPERATION_UNSUPPORTED", f"unsupported operation '{op}'")

            changed[collection] = records_by_collection[collection]

        return self._commit_collections(changed_records=changed, before=before, after=after)

    def _apply_update_operation(
        self,
        spec: CollectionSpec[BaseModel],
        records: list[BaseModel],
        record_id: str,
        patch: dict[str, Any],
        before: dict[str, Any],
        after: dict[str, Any],
    ) -> list[BaseModel]:
        unknown_fields = set(patch) - set(spec.model.model_fields)
        if unknown_fields:
            raise JsonIBaseError(
                "UNKNOWN_FIELD",
                f"unknown patch field '{sorted(unknown_fields)[0]}'",
                details={"fields": sorted(unknown_fields)},
            )

        next_records: list[BaseModel] = []
        found = False
        for record in records:
            if self._record_id(spec, record) == record_id:
                found = True
                before[f"{spec.name}:{record_id}"] = record.model_dump(mode="json")
                updated = spec.model.model_validate({**record.model_dump(mode="json"), **patch})
                after[f"{spec.name}:{record_id}"] = updated.model_dump(mode="json")
                next_records.append(updated)
            else:
                next_records.append(record)
        if not found:
            raise JsonIBaseError(
                "RECORD_NOT_FOUND",
                f"record '{record_id}' does not exist in collection '{spec.name}'",
            )
        return next_records

    def _apply_upsert_operation(
        self,
        spec: CollectionSpec[BaseModel],
        records: list[BaseModel],
        record: BaseModel,
        before: dict[str, Any],
        after: dict[str, Any],
    ) -> list[BaseModel]:
        record_id = self._record_id(spec, record)
        next_records: list[BaseModel] = []
        replaced = False
        for existing in records:
            if self._record_id(spec, existing) == record_id:
                before[f"{spec.name}:{record_id}"] = existing.model_dump(mode="json")
                next_records.append(record)
                replaced = True
            else:
                next_records.append(existing)
        if not replaced:
            next_records.append(record)
        after[f"{spec.name}:{record_id}"] = record.model_dump(mode="json")
        return next_records

    @staticmethod
    def _record_id(spec: CollectionSpec[BaseModel], record: BaseModel) -> str:
        return JsonIBase.record_id_for(spec, record)

    @staticmethod
    def record_id_for(spec: CollectionSpec[BaseModel], record: BaseModel) -> str:
        return str(getattr(record, spec.id_field))
