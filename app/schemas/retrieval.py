from __future__ import annotations

from pydantic import Field

from app.schemas.common import APIModel


class RetrievalCandidate(APIModel):
    code: str
    name: str
    score: float
    reasons: list[str]


class RetrievalCandidatesResponse(APIModel):
    candidates: list[RetrievalCandidate]
    retrieved_at: str = Field(alias="retrievedAt")
