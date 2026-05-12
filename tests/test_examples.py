from __future__ import annotations

import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_internet_ingestion_examples_compile() -> None:
    for path in [
        ROOT / "examples" / "ingest_peps.py",
        ROOT / "examples" / "ingest_cisa_kev.py",
        ROOT / "examples" / "ingest_rfc_index.py",
    ]:
        py_compile.compile(str(path), doraise=True)


def test_ingestion_source_catalog_documents_urls() -> None:
    catalog = (ROOT / "docs" / "ingestion-sources.md").read_text(encoding="utf-8")

    assert "https://peps.python.org/api/peps.json" in catalog
    assert (
        "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
        in catalog
    )
    assert "https://www.rfc-editor.org/rfc-index.xml" in catalog
