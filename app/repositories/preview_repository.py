from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.schemas.preview import PreviewRow, PreviewRowsPage, PreviewSummary


class PreviewRepository(ABC):
    @abstractmethod
    def save_preview(self, task_id: UUID, summary: PreviewSummary, page: PreviewRowsPage) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_preview_summary(self, task_id: UUID) -> PreviewSummary | None:
        raise NotImplementedError

    @abstractmethod
    def get_preview_page(self, task_id: UUID) -> PreviewRowsPage | None:
        raise NotImplementedError

    @abstractmethod
    def get_preview_row(self, task_id: UUID, row_no: int) -> PreviewRow | None:
        raise NotImplementedError


class InMemoryPreviewRepository(PreviewRepository):
    def __init__(self) -> None:
        self._summary_by_task: dict[UUID, PreviewSummary] = {}
        self._page_by_task: dict[UUID, PreviewRowsPage] = {}

    def save_preview(self, task_id: UUID, summary: PreviewSummary, page: PreviewRowsPage) -> None:
        self._summary_by_task[task_id] = summary
        self._page_by_task[task_id] = page

    def get_preview_summary(self, task_id: UUID) -> PreviewSummary | None:
        return self._summary_by_task.get(task_id)

    def get_preview_page(self, task_id: UUID) -> PreviewRowsPage | None:
        return self._page_by_task.get(task_id)

    def get_preview_row(self, task_id: UUID, row_no: int) -> PreviewRow | None:
        page = self._page_by_task.get(task_id)
        if page is None:
            return None
        for item in page.items:
            if item.row_no == row_no:
                return item
        return None
