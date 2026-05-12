from __future__ import annotations

import json

import pytest
from pydantic import BaseModel

from jsonibase import CollectionSpec, JsonIBase
from jsonibase.errors import JsonIBaseError


class Standard(BaseModel):
    id: str
    title: str


def _store(tmp_path):
    spec = CollectionSpec[Standard](
        name="standards",
        path="data/standards.jsonl",
        model=Standard,
    )
    store = JsonIBase.open(tmp_path, [spec], rebuild_policy="manual")
    store.init()
    return store


def _write_incomplete_journal(tmp_path) -> None:
    tx_dir = tmp_path / ".jsonibase" / "transactions" / "tx_interrupted"
    tx_dir.mkdir(parents=True)
    (tx_dir / "journal.json").write_text(
        json.dumps(
            {
                "transaction_id": "tx_interrupted",
                "state": "prepared",
                "files": [{"path": "data/standards.jsonl"}],
            }
        ),
        encoding="utf-8",
    )


def test_recover_reports_incomplete_transaction_journals(tmp_path) -> None:
    store = _store(tmp_path)
    _write_incomplete_journal(tmp_path)

    report = store.recover()

    assert report.recovery_required is True
    assert report.transactions[0]["transaction_id"] == "tx_interrupted"
    assert report.transactions[0]["state"] == "prepared"


def test_incomplete_transaction_blocks_new_writes(tmp_path) -> None:
    store = _store(tmp_path)
    _write_incomplete_journal(tmp_path)

    with pytest.raises(JsonIBaseError) as exc_info:
        store.add("standards", Standard(id="std_001", title="One"))

    assert exc_info.value.code == "TRANSACTION_RECOVERY_REQUIRED"


def test_recover_auto_clears_incomplete_journals(tmp_path) -> None:
    store = _store(tmp_path)
    _write_incomplete_journal(tmp_path)

    report = store.recover(auto=True)

    assert report.recovery_required is False
    assert report.recovered == ["tx_interrupted"]
    assert list((tmp_path / ".jsonibase" / "transactions").iterdir()) == []
