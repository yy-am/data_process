from __future__ import annotations

from pydantic import Field

from app.schemas.common import APIModel
from app.schemas.confirmation import ConfirmationPackage
from app.schemas.retrieval import RetrievalCandidatesResponse
from app.schemas.snapshot import InputSnapshot


class TemplateAlternative(APIModel):
    template_code: str | None = Field(default=None, alias="templateCode")
    scene_code: str | None = Field(default=None, alias="sceneCode")
    country_code: str | None = Field(default=None, alias="countryCode")
    confidence: float
    reasons: list[str]


class TemplateIdentificationResult(APIModel):
    template_code: str | None = Field(default=None, alias="templateCode")
    scene_code: str | None = Field(default=None, alias="sceneCode")
    country_code: str | None = Field(default=None, alias="countryCode")
    confidence: float
    alternatives: list[TemplateAlternative]
    need_user_confirm: bool = Field(alias="needUserConfirm")
    rationale: list[str]


class TemplateIdentificationRequest(APIModel):
    snapshot: InputSnapshot
    candidates: RetrievalCandidatesResponse
    catalog_markdown: str = Field(alias="catalogMarkdown")
    system_prompt: str = Field(alias="systemPrompt")
    user_prompt: str = Field(alias="userPrompt")


class RuleDraftRequest(APIModel):
    snapshot: InputSnapshot
    template_code: str = Field(alias="templateCode")
    scene_code: str = Field(alias="sceneCode")
    country_code: str = Field(alias="countryCode")
    rule_candidates: RetrievalCandidatesResponse = Field(alias="ruleCandidates")
    system_prompt: str = Field(alias="systemPrompt")
    user_prompt: str = Field(alias="userPrompt")


class RuleDraftResult(ConfirmationPackage):
    rationale: list[str]
