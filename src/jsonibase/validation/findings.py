from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Severity = Literal["info", "warning", "error"]


class ValidationFinding(BaseModel):
    level: Severity
    code: str
    message: str
    collection: str | None = None
    record_id: str | None = None
    details: dict[str, Any] = Field(default_factory=lambda: dict[str, Any]())


class ValidationReport(BaseModel):
    findings: list[ValidationFinding] = Field(default_factory=lambda: list[ValidationFinding]())

    @property
    def ok(self) -> bool:
        return all(finding.level != "error" for finding in self.findings)
