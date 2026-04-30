from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.schemas.retrieval import RetrievalCandidatesResponse


class RuleRetrievalResultRepository(ABC):
    @abstractmethod
    def save_rule_candidates(self, task_id: UUID, response: RetrievalCandidatesResponse) -> RetrievalCandidatesResponse:
        raise NotImplementedError

    @abstractmethod
    def get_rule_candidates(self, task_id: UUID) -> RetrievalCandidatesResponse | None:
        raise NotImplementedError


class InMemoryRuleRetrievalResultRepository(RuleRetrievalResultRepository):
    def __init__(self) -> None:
        self._rule_candidates: dict[UUID, RetrievalCandidatesResponse] = {}

    def save_rule_candidates(self, task_id: UUID, response: RetrievalCandidatesResponse) -> RetrievalCandidatesResponse:
        self._rule_candidates[task_id] = response
        return response

    def get_rule_candidates(self, task_id: UUID) -> RetrievalCandidatesResponse | None:
        return self._rule_candidates.get(task_id)
