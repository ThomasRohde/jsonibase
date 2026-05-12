from __future__ import annotations

from pydantic import BaseModel

from jsonibase import CollectionSpec, JsonIBase


class SecretRecord(BaseModel):
    id: str
    title: str
    body: str
    secret: str


def test_search_results_redact_configured_fields(tmp_path) -> None:
    spec = CollectionSpec[SecretRecord](
        name="records",
        path="data/records.jsonl",
        model=SecretRecord,
        fts_fields=["title", "body", "secret"],
        embedding_fields=["title", "body", "secret"],
        redacted_fields=["secret"],
    )
    store = JsonIBase.open(tmp_path, [spec], rebuild_policy="lazy")
    store.init()
    store.add(
        "records",
        SecretRecord(
            id="rec_001",
            title="Credential rotation",
            body="Rotate credentials.",
            secret="token-123",
        ),
    )

    results = store.search("records", "token", mode="fts")

    assert results[0].record["secret"] == "[REDACTED]"
    assert results[0].snippet == "[REDACTED]"
    assert "token-123" not in str(results[0].record)
