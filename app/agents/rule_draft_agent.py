from __future__ import annotations

from abc import ABC, abstractmethod

from app.agents.rule_draft_prompt import build_rule_draft_system_prompt, build_rule_draft_user_prompt
from app.clients.rule_draft_client import RuleDraftClient
from app.core.config import AgentRuntimeConfig
from app.core.exceptions import DomainError
from app.schemas.agent import RuleDraftRequest, RuleDraftResult
from app.schemas.retrieval import RetrievalCandidatesResponse
from app.schemas.snapshot import InputSnapshot


class RuleDraftAgent(ABC):
    @abstractmethod
    def draft(
        self,
        snapshot: InputSnapshot,
        template_code: str,
        scene_code: str,
        country_code: str,
        rule_candidates: RetrievalCandidatesResponse,
    ) -> RuleDraftResult:
        raise NotImplementedError


class ConfigurableRuleDraftAgent(RuleDraftAgent):
    def __init__(
        self,
        client: RuleDraftClient | None = None,
        config: AgentRuntimeConfig | None = None,
    ) -> None:
        self._client = client
        self._config = config

    def draft(
        self,
        snapshot: InputSnapshot,
        template_code: str,
        scene_code: str,
        country_code: str,
        rule_candidates: RetrievalCandidatesResponse,
    ) -> RuleDraftResult:
        self._validate_inputs(snapshot, template_code, scene_code, country_code, rule_candidates)
        client = self._require_client()
        request = RuleDraftRequest(
            snapshot=snapshot,
            templateCode=template_code,
            sceneCode=scene_code,
            countryCode=country_code,
            ruleCandidates=rule_candidates,
            systemPrompt=build_rule_draft_system_prompt(),
            userPrompt=build_rule_draft_user_prompt(
                snapshot,
                template_code,
                scene_code,
                country_code,
                rule_candidates,
            ),
        )
        return RuleDraftResult.model_validate(client.draft(request))

    def _validate_inputs(
        self,
        snapshot: InputSnapshot,
        template_code: str,
        scene_code: str,
        country_code: str,
        rule_candidates: RetrievalCandidatesResponse,
    ) -> None:
        if not snapshot.sheets:
            raise DomainError(
                code="RULE_DRAFT_INPUT_INVALID",
                message="Rule draft requires at least one parsed sheet.",
                status_code=422,
            )
        if not template_code or not scene_code or not country_code:
            raise DomainError(
                code="RULE_DRAFT_INPUT_INVALID",
                message="Rule draft requires resolved templateCode, sceneCode, and countryCode.",
                status_code=422,
            )
        if rule_candidates is None:
            raise DomainError(
                code="RULE_DRAFT_INPUT_INVALID",
                message="Rule draft requires a rule candidates payload.",
                status_code=422,
            )

    def _require_client(self) -> RuleDraftClient:
        if self._config is None or self._config.rule_draft_client is None:
            raise DomainError(
                code="LLM_CLIENT_NOT_CONFIGURED",
                message="Rule draft client configuration is missing.",
                status_code=503,
            )
        if self._client is None:
            raise DomainError(
                code="LLM_CLIENT_NOT_CONFIGURED",
                message="Rule draft client is not configured.",
                status_code=503,
            )
        return self._client
