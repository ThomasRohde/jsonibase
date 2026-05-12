from __future__ import annotations

import argparse
from pathlib import Path
from xml.etree import ElementTree as ET

from _internet_common import fetch_bytes, print_results
from pydantic import BaseModel

from jsonibase import CollectionSpec, JsonIBase

RFC_INDEX_URL = "https://www.rfc-editor.org/rfc-index.xml"
NAMESPACE = {"rfc": "https://www.rfc-editor.org/rfc-index"}


class RfcRecord(BaseModel):
    id: str
    doc_id: str
    number: int
    title: str
    authors: list[str]
    month: str | None
    year: str | None
    current_status: str
    publication_status: str
    stream: str
    doi: str | None
    body: str


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest the RFC Editor XML index into JsonIBase.")
    parser.add_argument("--root", type=Path, default=Path("example-workspaces/rfcs"))
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--query", default="transport congestion control")
    args = parser.parse_args()

    root = ET.fromstring(fetch_bytes(RFC_INDEX_URL))
    records = list(_rfc_records(root))[-args.limit :]

    spec = CollectionSpec[RfcRecord](
        name="rfcs",
        path="data/rfc_index.jsonl",
        model=RfcRecord,
        fts_fields=["doc_id", "title", "authors", "current_status", "stream", "body"],
        embedding_fields=["title", "body"],
        filter_fields=["current_status", "publication_status", "stream", "year"],
        sort_fields=["number", "title", "year"],
    )
    store = JsonIBase.open(args.root, [spec], rebuild_policy="lazy")
    store.init()

    with store.plan() as plan:
        for record in records:
            plan.upsert("rfcs", record)
    store.apply(plan)

    results = store.search("rfcs", args.query, top=5)
    print_results(args.root, args.query, [result.record_id for result in results])


def _rfc_records(root: ET.Element):
    for entry in root.findall("rfc:rfc-entry", NAMESPACE):
        doc_id = _text(entry, "doc-id") or ""
        number = int(doc_id.removeprefix("RFC"))
        authors = [
            name.text or "" for name in entry.findall("rfc:author/rfc:name", NAMESPACE) if name.text
        ]
        title = _text(entry, "title") or ""
        current_status = _text(entry, "current-status") or ""
        publication_status = _text(entry, "publication-status") or ""
        stream = _text(entry, "stream") or ""
        month = _text(entry, "date/rfc:month")
        year = _text(entry, "date/rfc:year")
        doi = _text(entry, "doi")
        body_parts = [
            doc_id,
            title,
            " ".join(authors),
            current_status,
            publication_status,
            stream,
        ]
        body = " ".join(value for value in body_parts if value)
        yield RfcRecord(
            id=doc_id.lower(),
            doc_id=doc_id,
            number=number,
            title=title,
            authors=authors,
            month=month,
            year=year,
            current_status=current_status,
            publication_status=publication_status,
            stream=stream,
            doi=doi,
            body=body,
        )


def _text(entry: ET.Element, path: str) -> str | None:
    child = entry.find(f"rfc:{path}", NAMESPACE)
    if child is None or child.text is None:
        return None
    return child.text.strip()


if __name__ == "__main__":
    main()
