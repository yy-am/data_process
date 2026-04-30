from __future__ import annotations

from abc import ABC, abstractmethod

from app.agents.template_identification_prompt import (
    build_template_identification_system_prompt,
    build_template_identification_user_prompt,
)
from app.clients.template_identification_client import TemplateIdentificationClient
from app.core.config import AgentRuntimeConfig
from app.core.exceptions import DomainError
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.schemas.agent import TemplateIdentificationResult
from app.schemas.retrieval import RetrievalCandidatesResponse
from app.schemas.snapshot import InputSnapshot


class TemplateIdentificationAgent(ABC):
    @abstractmethod
    def identify(
        self,
        snapshot: InputSnapshot,
        candidates: RetrievalCandidatesResponse,
    ) -> TemplateIdentificationResult:
        raise NotImplementedError


class ConfigurableTemplateIdentificationAgent(TemplateIdentificationAgent):
    def __init__(
        self,
        client: TemplateIdentificationClient | None = None,
        config: AgentRuntimeConfig | None = None,
        knowledge_base_repository: KnowledgeBaseRepository | None = None,
    ) -> None:
        self._client = client
        self._config = config
        self._knowledge_base_repository = knowledge_base_repository

    def identify(
        self,
        snapshot: InputSnapshot,
        candidates: RetrievalCandidatesResponse,
    ) -> TemplateIdentificationResult:
        self._validate_inputs(snapshot, candidates)
        client = self._require_client()
        request = self._build_request(snapshot, candidates)
        result = client.identify(request)
        return TemplateIdentificationResult.model_validate(result)

    def _validate_inputs(
        self,
        snapshot: InputSnapshot,
        candidates: RetrievalCandidatesResponse,
    ) -> None:
        if not snapshot.sheets:
            raise DomainError(
                code="TEMPLATE_IDENTIFICATION_INPUT_INVALID",
                message="Template identification requires at least one parsed sheet.",
                status_code=422,
            )
        for sheet in snapshot.sheets:
            if not sheet.headers:
                raise DomainError(
                    code="TEMPLATE_IDENTIFICATION_INPUT_INVALID",
                    message="Template identification requires sheet headers.",
                    status_code=422,
                )
        if candidates is None:
            raise DomainError(
                code="TEMPLATE_IDENTIFICATION_INPUT_INVALID",
                message="Template identification requires a candidates payload.",
                status_code=422,
            )

    def _require_client(self) -> TemplateIdentificationClient:
        if self._config is None or self._config.template_identification_client is None:
            raise DomainError(
                code="LLM_CLIENT_NOT_CONFIGURED",
                message="Template identification client configuration is missing.",
                status_code=503,
            )
        if self._client is None:
            raise DomainError(
                code="LLM_CLIENT_NOT_CONFIGURED",
                message="Template identification client is not configured.",
                status_code=503,
            )
        return self._client

    def _build_request(
        self,
        snapshot: InputSnapshot,
        candidates: RetrievalCandidatesResponse,
    ) -> "TemplateIdentificationRequest":
        from app.schemas.agent import TemplateIdentificationRequest
        catalog_markdown = self._require_catalog_markdown()

        return TemplateIdentificationRequest(
            snapshot=snapshot,
            candidates=candidates,
            catalogMarkdown=catalog_markdown,
            systemPrompt=build_template_identification_system_prompt(),
            userPrompt=build_template_identification_user_prompt(snapshot, candidates, catalog_markdown),
        )

    def _require_catalog_markdown(self) -> str:
        if self._knowledge_base_repository is None:
            raise DomainError(
                code="TEMPLATE_IDENTIFICATION_INPUT_INVALID",
                message="Template identification requires a knowledge-base catalog repository.",
                status_code=422,
            )
        return self._knowledge_base_repository.get_catalog_markdown()
