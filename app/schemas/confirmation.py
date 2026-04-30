from __future__ import annotations

from typing import Any

from pydantic import Field

from app.schemas.common import APIModel


class ConfirmationPackage(APIModel):
    template_code: str | None = Field(default=None, alias="templateCode")
    scene_code: str | None = Field(default=None, alias="sceneCode")
    country_code: str | None = Field(default=None, alias="countryCode")
    draft_dsl: dict[str, Any] | None = Field(default=None, alias="draftDsl")
    ambiguous_mappings: list[dict[str, Any]] = Field(default_factory=list, alias="ambiguousMappings")
    missing_fields: list[dict[str, Any]] = Field(default_factory=list, alias="missingFields")
    default_suggestions: list[dict[str, Any]] = Field(default_factory=list, alias="defaultSuggestions")
    blocking_issues: list[dict[str, Any]] = Field(default_factory=list, alias="blockingIssues")


class ConfirmationRequest(APIModel):
    selected_template_code: str = Field(alias="selectedTemplateCode")
    selected_rule_code: str = Field(alias="selectedRuleCode")
    confirmed_mappings: list[dict[str, Any]] = Field(alias="confirmedMappings")
    confirmed_defaults: list[dict[str, Any]] = Field(alias="confirmedDefaults")


class FinalConfirmRequest(APIModel):
    result_version: int = Field(alias="resultVersion")
