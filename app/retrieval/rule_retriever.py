from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.retrieval import RetrievalCandidatesResponse
from app.schemas.snapshot import InputSnapshot


class RuleRetriever(ABC):
    @abstractmethod
    def retrieve(self, snapshot: InputSnapshot, template_code: str) -> RetrievalCandidatesResponse:
        raise NotImplementedError
