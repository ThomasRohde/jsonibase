from __future__ import annotations

import argparse
from pathlib import Path

from _internet_common import fetch_json, print_results
from pydantic import BaseModel

from jsonibase import CollectionSpec, JsonIBase

PEPS_URL = "https://peps.python.org/api/peps.json"


class PepRecord(BaseModel):
    id: str
    number: int
    title: str
    status: str
    type: str
    topic: str
    authors: str
    author_names: list[str]
    python_version: str | None
    url: str
    body: str


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Python PEP metadata into JsonIBase.")
    parser.add_argument("--root", type=Path, default=Path("example-workspaces/peps"))
    parser.add_argument("--limit", type=int, default=250)
    parser.add_argument("--query", default="typing generics protocols")
    args = parser.parse_args()

    raw = fetch_json(PEPS_URL)
    records = [
        PepRecord(
            id=f"pep_{item['number']:04d}",
            number=item["number"],
            title=item["title"],
            status=item["status"],
            type=item["type"],
            topic=item["topic"] or "",
            authors=item["authors"],
            author_names=item["author_names"],
            python_version=item["python_version"],
            url=item["url"],
            body=" ".join(
                value
                for value in [
                    item["title"],
                    item["status"],
                    item["type"],
                    item["topic"] or "",
                    item["authors"],
                    item["python_version"] or "",
                ]
                if value
            ),
        )
        for item in sorted(raw.values(), key=lambda pep: pep["number"])[: args.limit]
    ]

    spec = CollectionSpec[PepRecord](
        name="peps",
        path="data/peps.jsonl",
        model=PepRecord,
        fts_fields=["title", "body", "authors", "topic"],
        embedding_fields=["title", "body"],
        filter_fields=["status", "type", "topic"],
        sort_fields=["number", "title"],
    )
    store = JsonIBase.open(args.root, [spec], rebuild_policy="lazy")
    store.init()

    with store.plan() as plan:
        for record in records:
            plan.upsert("peps", record)
    store.apply(plan)

    results = store.search("peps", args.query, top=5)
    print_results(args.root, args.query, [result.record_id for result in results])


if __name__ == "__main__":
    main()
