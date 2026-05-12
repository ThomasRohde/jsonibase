from __future__ import annotations

from pydantic import BaseModel

from jsonibase import CollectionSpec
from jsonibase.config import RelationshipSpec
from jsonibase.validation import (
    ValidationContext,
    ValidationFinding,
    validate_workspace,
)


class Standard(BaseModel):
    id: str
    title: str
    owner: str


class Link(BaseModel):
    id: str
    target_id: str


def test_validate_workspace_accepts_valid_sources(tmp_path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "standards.jsonl").write_text(
        '{"id":"std_001","owner":"platform","title":"One"}\n',
        encoding="utf-8",
    )
    spec = CollectionSpec[Standard](
        name="standards",
        path="data/standards.jsonl",
        model=Standard,
    )

    report = validate_workspace(tmp_path, [spec])

    assert report.ok
    assert report.findings == []


def test_validate_workspace_reports_jsonl_and_schema_errors(tmp_path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "standards.jsonl").write_text(
        '{"id":"std_001"}\n',
        encoding="utf-8",
    )
    spec = CollectionSpec[Standard](
        name="standards",
        path="data/standards.jsonl",
        model=Standard,
    )

    report = validate_workspace(tmp_path, [spec])

    assert not report.ok
    assert report.findings[0].level == "error"
    assert report.findings[0].code == "JSONL_SCHEMA_ERROR"
    assert report.findings[0].collection == "standards"
    assert report.findings[0].details["line_number"] == 1


def test_validate_workspace_reports_duplicate_ids(tmp_path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "standards.jsonl").write_text(
        '{"id":"std_001","owner":"platform","title":"One"}\n'
        '{"id":"std_001","owner":"platform","title":"Duplicate"}\n',
        encoding="utf-8",
    )
    spec = CollectionSpec[Standard](
        name="standards",
        path="data/standards.jsonl",
        model=Standard,
    )

    report = validate_workspace(tmp_path, [spec])

    assert not report.ok
    finding = report.findings[0]
    assert finding.code == "DUPLICATE_ID"
    assert finding.collection == "standards"
    assert finding.record_id == "std_001"
    assert finding.details["first_line_number"] == 1
    assert finding.details["duplicate_line_number"] == 2


def test_validate_workspace_reports_missing_relationship_targets(tmp_path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "standards.jsonl").write_text(
        '{"id":"std_001","owner":"platform","title":"One"}\n',
        encoding="utf-8",
    )
    (tmp_path / "data" / "links.jsonl").write_text(
        '{"id":"lnk_001","target_id":"std_999"}\n',
        encoding="utf-8",
    )
    standards = CollectionSpec[Standard](
        name="standards",
        path="data/standards.jsonl",
        model=Standard,
    )
    links = CollectionSpec[Link](
        name="links",
        path="data/links.jsonl",
        model=Link,
        relationships=[RelationshipSpec(field="target_id", target_collection="standards")],
    )

    report = validate_workspace(tmp_path, [standards, links])

    assert not report.ok
    finding = report.findings[0]
    assert finding.code == "RELATION_TARGET_MISSING"
    assert finding.collection == "links"
    assert finding.record_id == "lnk_001"
    assert finding.details["target_collection"] == "standards"
    assert finding.details["target_id"] == "std_999"


def test_validate_workspace_runs_custom_validators(tmp_path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "standards.jsonl").write_text(
        '{"id":"std_001","owner":"unknown","title":"One"}\n',
        encoding="utf-8",
    )
    spec = CollectionSpec[Standard](
        name="standards",
        path="data/standards.jsonl",
        model=Standard,
    )

    class OwnerValidator:
        name = "owner-validator"

        def validate(self, context: ValidationContext) -> list[ValidationFinding]:
            records = context.records["standards"]
            if records[0].record.owner == "unknown":
                return [
                    ValidationFinding(
                        level="error",
                        code="OWNER_UNKNOWN",
                        collection="standards",
                        record_id=records[0].record.id,
                        message="owner cannot be unknown",
                    )
                ]
            return []

    report = validate_workspace(tmp_path, [spec], validators=[OwnerValidator()])

    assert not report.ok
    assert report.findings[0].code == "OWNER_UNKNOWN"
