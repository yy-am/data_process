from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.schemas.retrieval import RetrievalCandidatesResponse


class RetrievalResultRepository(ABC):
    @abstractmethod
    def save_template_candidates(self, task_id: UUID, response: RetrievalCandidatesResponse) -> RetrievalCandidatesResponse:
        raise NotImplementedError

    @abstractmethod
    def get_template_candidates(self, task_id: UUID) -> RetrievalCandidatesResponse | None:
        raise NotImplementedError


class InMemoryRetrievalResultRepository(RetrievalResultRepository):
    def __init__(self) -> None:
        self._template_candidates: dict[UUID, RetrievalCandidatesResponse] = {}

    def save_template_candidates(self, task_id: UUID, response: RetrievalCandidatesResponse) -> RetrievalCandidatesResponse:
        self._template_candidates[task_id] = response
        return response

    def get_template_candidates(self, task_id: UUID) -> RetrievalCandidatesResponse | None:
        return self._template_candidates.get(task_id)
