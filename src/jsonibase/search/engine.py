from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

import numpy as np
import orjson
from pydantic import BaseModel

from jsonibase.config import CollectionSpec
from jsonibase.embeddings import EmbeddingProvider, deserialize_vector
from jsonibase.errors import JsonIBaseError
from jsonibase.models import SearchResult

SearchMode = Literal["hybrid", "fts", "vector"]


@dataclass(frozen=True)
class _RankedResult:
    result: SearchResult
    rank: int


def search_index(
    *,
    index_path: str | Path,
    spec: CollectionSpec[BaseModel],
    query: str,
    mode: SearchMode,
    filters: dict[str, Any] | None,
    top: int,
    embedding_provider: EmbeddingProvider,
) -> list[SearchResult]:
    if top <= 0:
        return []

    db_path = Path(index_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if mode == "fts":
            return [ranked.result for ranked in _fts_search(conn, spec, query, filters or {}, top)]
        if mode == "vector":
            return [
                ranked.result
                for ranked in _vector_search(
                    conn,
                    spec,
                    query,
                    filters or {},
                    top,
                    embedding_provider,
                )
            ]
        return _hybrid_search(conn, spec, query, filters or {}, top, embedding_provider)
    finally:
        conn.close()


def _fts_search(
    conn: sqlite3.Connection,
    spec: CollectionSpec[BaseModel],
    query: str,
    filters: dict[str, Any],
    top: int,
) -> list[_RankedResult]:
    planned = _plan_fts_query(query)
    if not planned:
        return []

    where_sql, values = _filter_sql(spec, filters)
    fts_table = _fts_table(spec)
    table = _collection_table(spec)
    sql = (
        f"SELECT c.id, c.json, bm25({_quote_identifier(fts_table)}) AS score "
        f"FROM {_quote_identifier(fts_table)} "
        f"JOIN {_quote_identifier(table)} AS c ON c.id = {_quote_identifier(fts_table)}.id "
        f"WHERE {_quote_identifier(fts_table)} MATCH ?{where_sql} "
        "ORDER BY score ASC, c.id ASC LIMIT ?"
    )
    rows = conn.execute(sql, [planned, *values, top]).fetchall()
    results: list[_RankedResult] = []
    for rank, row in enumerate(rows, start=1):
        score = 1.0 / rank
        raw_record = _raw_record(row["json"])
        results.append(
            _RankedResult(
                result=SearchResult(
                    collection=spec.name,
                    record_id=row["id"],
                    score=score,
                    record=_redact_record(spec, raw_record),
                    match_source="fts",
                    snippet=_snippet(spec, raw_record, query),
                    explanation={"fts_rank": rank, "fts_query": planned},
                ),
                rank=rank,
            )
        )
    return results


def _vector_search(
    conn: sqlite3.Connection,
    spec: CollectionSpec[BaseModel],
    query: str,
    filters: dict[str, Any],
    top: int,
    embedding_provider: EmbeddingProvider,
) -> list[_RankedResult]:
    where_sql, values = _filter_sql(spec, filters)
    table = _collection_table(spec)
    sql = (
        f"SELECT c.id, c.json, c.embedding FROM {_quote_identifier(table)} AS c "
        f"WHERE c.embedding IS NOT NULL{where_sql} ORDER BY c.id ASC"
    )
    query_vector = embedding_provider.encode([query])[0]
    query_norm = float(np.linalg.norm(query_vector))
    if query_norm == 0:
        return []

    scored: list[tuple[str, float, dict[str, Any]]] = []
    for row in conn.execute(sql, values).fetchall():
        vector = deserialize_vector(row["embedding"])
        vector_norm = float(np.linalg.norm(vector))
        if vector_norm == 0:
            continue
        score = float(np.dot(query_vector, vector) / (query_norm * vector_norm))
        scored.append((row["id"], score, _raw_record(row["json"])))

    scored.sort(key=lambda item: (-item[1], item[0]))
    results: list[_RankedResult] = []
    for rank, (record_id, score, record) in enumerate(scored[:top], start=1):
        results.append(
            _RankedResult(
                result=SearchResult(
                    collection=spec.name,
                    record_id=record_id,
                    score=score,
                    record=_redact_record(spec, record),
                    match_source="vector",
                    snippet=_snippet(spec, record, query),
                    explanation={"vector_rank": rank},
                ),
                rank=rank,
            )
        )
    return results


def _hybrid_search(
    conn: sqlite3.Connection,
    spec: CollectionSpec[BaseModel],
    query: str,
    filters: dict[str, Any],
    top: int,
    embedding_provider: EmbeddingProvider,
) -> list[SearchResult]:
    candidate_count = max(top * 4, 10)
    fts_results = _fts_search(conn, spec, query, filters, candidate_count)
    vector_results = _vector_search(conn, spec, query, filters, candidate_count, embedding_provider)
    combined: dict[str, SearchResult] = {}
    scores: dict[str, float] = {}

    for source, ranked_results in (("fts", fts_results), ("vector", vector_results)):
        for ranked in ranked_results:
            record_id = ranked.result.record_id
            combined.setdefault(record_id, ranked.result)
            scores[record_id] = scores.get(record_id, 0.0) + _rrf_score(ranked.rank)
            combined[record_id].explanation[f"{source}_rank"] = ranked.rank

    final = list(combined.values())
    for result in final:
        result.score = scores[result.record_id]
        has_fts = "fts_rank" in result.explanation
        has_vector = "vector_rank" in result.explanation
        result.match_source = "hybrid" if has_fts and has_vector else result.match_source
    final.sort(key=lambda item: (-item.score, item.record_id))
    return final[:top]


def _filter_sql(spec: CollectionSpec[BaseModel], filters: dict[str, Any]) -> tuple[str, list[str]]:
    clauses: list[str] = []
    values: list[str] = []
    allowed = set(spec.filter_fields)
    for field_name, expression in filters.items():
        if field_name not in allowed:
            raise JsonIBaseError(
                "FILTER_FIELD_NOT_CONFIGURED",
                f"field '{field_name}' is not configured for filtering",
                details={"collection": spec.name, "field": field_name},
            )
        if not isinstance(expression, dict):
            raise JsonIBaseError(
                "FILTER_UNSUPPORTED",
                "only {'eq': value} filters are currently supported",
                details={"collection": spec.name, "field": field_name},
            )
        expression_dict = cast(dict[str, object], expression)
        if set(expression_dict) != {"eq"}:
            raise JsonIBaseError(
                "FILTER_UNSUPPORTED",
                "only {'eq': value} filters are currently supported",
                details={"collection": spec.name, "field": field_name},
            )
        clauses.append(f" AND c.{_quote_identifier(field_name)} = ?")
        values.append(_stored_filter_value(expression_dict["eq"]))
    return "".join(clauses), values


def _stored_filter_value(value: object) -> str:
    if isinstance(value, list | tuple):
        return orjson.dumps(value).decode("utf-8")
    return str(value)


def _raw_record(json_text: str) -> dict[str, Any]:
    return cast(dict[str, Any], orjson.loads(json_text))


def _redact_record(spec: CollectionSpec[BaseModel], record: dict[str, Any]) -> dict[str, Any]:
    if not spec.redacted_fields:
        return record
    redacted: dict[str, Any] = dict(record)
    for field_name in spec.redacted_fields:
        if field_name in redacted:
            redacted[field_name] = "[REDACTED]"
    return redacted


def _snippet(spec: CollectionSpec[BaseModel], record: dict[str, Any], query: str) -> str | None:
    tokens = re.findall(r"[\w]+", query.casefold())
    for field_name in spec.fts_fields:
        value = record.get(field_name)
        text = _snippet_text(value)
        if not text:
            continue
        if not tokens or any(token in text.casefold() for token in tokens):
            return "[REDACTED]" if field_name in spec.redacted_fields else text
    return None


def _snippet_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, list | tuple | set):
        return " ".join(str(item) for item in cast(Iterable[object], value))
    return str(value)


def _plan_fts_query(query: str) -> str:
    tokens = re.findall(r"[\w]+", query.casefold())
    return " OR ".join(f"{token}*" for token in tokens)


def _rrf_score(rank: int, k: int = 60) -> float:
    return 1.0 / (k + rank)


def _collection_table(spec: CollectionSpec[BaseModel]) -> str:
    return f"ji_{spec.name}"


def _fts_table(spec: CollectionSpec[BaseModel]) -> str:
    return f"{_collection_table(spec)}_fts"


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'
