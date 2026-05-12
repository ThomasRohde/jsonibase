from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

USER_AGENT = "jsonibase-example/0.1 (+https://github.com/local/jsonibase)"


def fetch_json(url: str) -> Any:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def fetch_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=60) as response:
        return response.read()


def print_results(root: Path, query: str, record_ids: list[str]) -> None:
    print(f"Workspace: {root}")
    print(f"Query: {query!r}")
    print("Top results:")
    for record_id in record_ids:
        print(f"- {record_id}")
