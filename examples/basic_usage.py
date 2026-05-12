from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import BaseModel

from jsonibase import CollectionSpec, JsonIBase


class Standard(BaseModel):
    id: str
    title: str
    body: str
    status: str


def main() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        standards = CollectionSpec[Standard](
            name="standards",
            path="data/standards.jsonl",
            model=Standard,
            fts_fields=["title", "body"],
            embedding_fields=["title", "body"],
            filter_fields=["status"],
        )
        store = JsonIBase.open(root, [standards])
        store.init()
        store.add(
            "standards",
            Standard(
                id="std_001",
                title="Managed services",
                body="Prefer managed services where possible.",
                status="active",
            ),
        )
        results = store.search("standards", "managed services")
        print(results[0].record_id)


if __name__ == "__main__":
    main()
