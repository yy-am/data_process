from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class RuleDraftRecord:
    rule_draft_id: UUID
    task_id: UUID
    draft_version: int
    template_code: str | None
    rule_code: str | None
    scene_code: str | None
    country_code: str | None
    draft_dsl_json: dict
    ambiguous_mappings_json: list[dict]
    missing_fields_json: list[dict]
    default_suggestions_json: list[dict]
    blocking_issues_json: list[dict]
    created_at: datetime


@dataclass(slots=True)
class ConfirmationPackageRecord:
    confirmation_package_id: UUID
    task_id: UUID
    package_version: int
    package_json: dict
    created_at: datetime


@dataclass(slots=True)
class ConfirmationResultRecord:
    confirmation_result_id: UUID
    task_id: UUID
    package_version: int
    result_json: dict
    created_at: datetime


@dataclass(slots=True)
class EffectiveRuleRecord:
    effective_rule_id: UUID
    task_id: UUID
    rule_version: int
    template_code: str
    rule_code: str
    effective_dsl_json: dict
    created_at: datetime
