from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.domain.enums import InputType, TaskStatus
from app.schemas.task import TaskFileInfo, TaskSummary


@dataclass(slots=True)
class StoredTask:
    summary: TaskSummary
    file: TaskFileInfo
    stored_filename: str


class TaskRepository(ABC):
    @abstractmethod
    def create_task(self, input_type: InputType, file_info: TaskFileInfo) -> StoredTask:
        raise NotImplementedError

    @abstractmethod
    def get_task(self, task_id: UUID) -> StoredTask | None:
        raise NotImplementedError

    @abstractmethod
    def update_task_status(self, task_id: UUID, status: TaskStatus, *, error_code: str | None = None, error_message: str | None = None) -> StoredTask:
        raise NotImplementedError

    @abstractmethod
    def update_task_resolution(
        self,
        task_id: UUID,
        *,
        template_code: str | None,
        scene_code: str | None,
        country_code: str | None,
    ) -> StoredTask:
        raise NotImplementedError


class InMemoryTaskRepository(TaskRepository):
    def __init__(self) -> None:
        self._tasks: dict[UUID, StoredTask] = {}

    def create_task(self, input_type: InputType, file_info: TaskFileInfo, stored_filename: str) -> StoredTask:
        now = datetime.now(timezone.utc)
        task_id = uuid4()
        summary = TaskSummary(
            taskId=task_id,
            inputType=input_type,
            status=TaskStatus.CREATED,
            currentStage=TaskStatus.CREATED,
            createdAt=now,
            updatedAt=now,
        )
        stored = StoredTask(summary=summary, file=file_info, stored_filename=stored_filename)
        self._tasks[task_id] = stored
        return stored

    def get_task(self, task_id: UUID) -> StoredTask | None:
        return self._tasks.get(task_id)

    def update_task_status(self, task_id: UUID, status: TaskStatus, *, error_code: str | None = None, error_message: str | None = None) -> StoredTask:
        stored = self._tasks[task_id]
        updated = stored.summary.model_copy(
            update={
                "status": status,
                "current_stage": status,
                "error_code": error_code,
                "error_message": error_message,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        refreshed = StoredTask(summary=updated, file=stored.file, stored_filename=stored.stored_filename)
        self._tasks[task_id] = refreshed
        return refreshed

    def update_task_resolution(
        self,
        task_id: UUID,
        *,
        template_code: str | None,
        scene_code: str | None,
        country_code: str | None,
    ) -> StoredTask:
        stored = self._tasks[task_id]
        updated = stored.summary.model_copy(
            update={
                "template_code": template_code,
                "scene_code": scene_code,
                "country_code": country_code,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        refreshed = StoredTask(summary=updated, file=stored.file, stored_filename=stored.stored_filename)
        self._tasks[task_id] = refreshed
        return refreshed
