from __future__ import annotations

from typing import Any

from pydantic import Field

from app.domain.enums import PreviewValidationStatus
from app.schemas.common import APIModel


class PreviewSummary(APIModel):
    total_rows: int = Field(alias="totalRows")
    success_rows: int = Field(alias="successRows")
    warning_rows: int = Field(alias="warningRows")
    error_rows: int = Field(alias="errorRows")


class PreviewRow(APIModel):
    row_no: int = Field(alias="rowNo")
    source_row_ref: dict[str, Any] = Field(alias="sourceRowRef")
    target_data: dict[str, Any] = Field(alias="targetData")
    validation_status: PreviewValidationStatus = Field(alias="validationStatus")
    warning_flags: list[str] = Field(alias="warningFlags")


class PreviewRowsPage(APIModel):
    items: list[PreviewRow]
    page: int
    page_size: int = Field(alias="pageSize")
    total: int
