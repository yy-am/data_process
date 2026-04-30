from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class TemplateRetrievalResultRecord:
    retrieval_result_id: UUID
    task_id: UUID
    snapshot_version: int
    template_code: str
    score: float
    score_detail_json: dict
    rank_no: int
    created_at: datetime


@dataclass(slots=True)
class RuleRetrievalResultRecord:
    retrieval_result_id: UUID
    task_id: UUID
    snapshot_version: int
    rule_code: str
    score: float
    score_detail_json: dict
    rank_no: int
    created_at: datetime
