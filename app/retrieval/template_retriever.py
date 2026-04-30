from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.retrieval import RetrievalCandidatesResponse
from app.schemas.snapshot import InputSnapshot


class TemplateRetriever(ABC):
    @abstractmethod
    def retrieve(self, snapshot: InputSnapshot) -> RetrievalCandidatesResponse:
        raise NotImplementedError
