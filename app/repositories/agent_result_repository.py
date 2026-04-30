from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.schemas.agent import RuleDraftResult
from app.schemas.agent import TemplateIdentificationResult


class AgentResultRepository(ABC):
    @abstractmethod
    def save_template_identification_result(
        self,
        task_id: UUID,
        result: TemplateIdentificationResult,
    ) -> TemplateIdentificationResult:
        raise NotImplementedError

    @abstractmethod
    def get_template_identification_result(
        self,
        task_id: UUID,
    ) -> TemplateIdentificationResult | None:
        raise NotImplementedError

    @abstractmethod
    def save_rule_draft_result(
        self,
        task_id: UUID,
        result: RuleDraftResult,
    ) -> RuleDraftResult:
        raise NotImplementedError

    @abstractmethod
    def get_rule_draft_result(
        self,
        task_id: UUID,
    ) -> RuleDraftResult | None:
        raise NotImplementedError


class InMemoryAgentResultRepository(AgentResultRepository):
    def __init__(self) -> None:
        self._template_results: dict[UUID, TemplateIdentificationResult] = {}
        self._rule_draft_results: dict[UUID, RuleDraftResult] = {}

    def save_template_identification_result(
        self,
        task_id: UUID,
        result: TemplateIdentificationResult,
    ) -> TemplateIdentificationResult:
        self._template_results[task_id] = result
        return result

    def get_template_identification_result(
        self,
        task_id: UUID,
    ) -> TemplateIdentificationResult | None:
        return self._template_results.get(task_id)

    def save_rule_draft_result(
        self,
        task_id: UUID,
        result: RuleDraftResult,
    ) -> RuleDraftResult:
        self._rule_draft_results[task_id] = result
        return result

    def get_rule_draft_result(
        self,
        task_id: UUID,
    ) -> RuleDraftResult | None:
        return self._rule_draft_results.get(task_id)
