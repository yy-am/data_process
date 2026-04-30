from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from app.domain.enums import InputType
from app.schemas.common import APIModel


class SheetSnapshot(APIModel):
    sheet_name: str = Field(alias="sheetName")
    headers: list[str]
    normalized_headers: list[str] = Field(alias="normalizedHeaders")
    sample_rows: list[dict[str, Any]] = Field(alias="sampleRows")
    column_stats: dict[str, Any] = Field(alias="columnStats")
    header_confidence: dict[str, float] = Field(alias="headerConfidence")


class InputSnapshot(APIModel):
    task_id: UUID = Field(alias="taskId")
    input_type: InputType = Field(alias="inputType")
    sheets: list[SheetSnapshot]
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParsedSheetSnapshot(APIModel):
    sheet_name: str = Field(alias="sheetName")
    headers: list[str]
    normalized_headers: list[str] = Field(alias="normalizedHeaders")
    sample_rows: list[dict[str, Any]] = Field(alias="sampleRows")
    column_stats: dict[str, Any] = Field(alias="columnStats")
    header_confidence: dict[str, float] = Field(alias="headerConfidence")


class ParsedInputSnapshot(APIModel):
    input_type: InputType = Field(alias="inputType")
    sheets: list[ParsedSheetSnapshot]
    metadata: dict[str, Any] = Field(default_factory=dict)
