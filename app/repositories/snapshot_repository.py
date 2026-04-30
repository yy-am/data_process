from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.enums import InputType
from app.schemas.snapshot import InputSnapshot, ParsedInputSnapshot, SheetSnapshot


class SnapshotRepository(ABC):
    @abstractmethod
    def save_snapshot(self, task_id: UUID, parsed_snapshot: ParsedInputSnapshot) -> InputSnapshot:
        raise NotImplementedError

    @abstractmethod
    def get_snapshot(self, task_id: UUID) -> InputSnapshot | None:
        raise NotImplementedError


class InMemorySnapshotRepository(SnapshotRepository):
    def __init__(self) -> None:
        self._snapshots: dict[UUID, InputSnapshot] = {}

    def save_snapshot(self, task_id: UUID, parsed_snapshot: ParsedInputSnapshot) -> InputSnapshot:
        snapshot = InputSnapshot(
            taskId=task_id,
            inputType=InputType(parsed_snapshot.input_type),
            sheets=[
                SheetSnapshot(
                    sheetName=sheet.sheet_name,
                    headers=sheet.headers,
                    normalizedHeaders=sheet.normalized_headers,
                    sampleRows=sheet.sample_rows,
                    columnStats=sheet.column_stats,
                    headerConfidence=sheet.header_confidence,
                )
                for sheet in parsed_snapshot.sheets
            ],
            metadata=dict(parsed_snapshot.metadata),
        )
        self._snapshots[task_id] = snapshot
        return snapshot

    def get_snapshot(self, task_id: UUID) -> InputSnapshot | None:
        return self._snapshots.get(task_id)
