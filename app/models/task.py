from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class TaskRecord:
    task_id: UUID
    input_type: str
    status: str
    current_stage: str
    current_rule_version: int
    current_result_version: int
    template_code: str | None
    rule_code: str | None
    scene_code: str | None
    country_code: str | None
    source_fix_required: bool
    error_code: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class TaskFileRecord:
    task_file_id: UUID
    task_id: UUID
    original_filename: str
    stored_filename: str
    content_type: str
    file_size: int
    created_at: datetime
