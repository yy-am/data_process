from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class InputSnapshotRecord:
    snapshot_id: UUID
    task_id: UUID
    snapshot_version: int
    input_type: str
    snapshot_json: dict
    created_at: datetime


@dataclass(slots=True)
class SheetSnapshotRecord:
    sheet_snapshot_id: UUID
    task_id: UUID
    snapshot_version: int
    sheet_name: str
    headers_json: list[str]
    normalized_headers_json: list[str]
    sample_rows_json: list[dict]
    column_stats_json: dict
    header_confidence_json: dict[str, float]
    created_at: datetime
