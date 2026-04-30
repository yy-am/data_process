from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class StagingResultRecord:
    staging_result_id: UUID
    task_id: UUID
    result_version: int
    row_no: int
    source_row_ref: dict
    target_data_json: dict
    validation_status: str
    warning_flags_json: list[str]
    created_at: datetime


@dataclass(slots=True)
class StagingSummaryRecord:
    staging_summary_id: UUID
    task_id: UUID
    result_version: int
    total_rows: int
    success_rows: int
    warning_rows: int
    error_rows: int
    created_at: datetime


@dataclass(slots=True)
class ExportRecord:
    export_record_id: UUID
    task_id: UUID
    result_version: int
    export_status: str
    export_file_path: str | None
    created_at: datetime
