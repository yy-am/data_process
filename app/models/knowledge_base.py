from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class TemplateRecord:
    template_code: str
    template_name: str
    source_type: str
    status: str
    description: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class TemplateFieldRecord:
    template_field_id: UUID
    template_code: str
    field_code: str
    field_name: str
    data_type: str
    required: bool
    sort_order: int


@dataclass(slots=True)
class TemplateHeaderAliasRecord:
    template_header_alias_id: UUID
    template_code: str
    field_code: str
    header_alias: str
    normalized_alias: str
    language: str | None
    country_code: str | None
    priority: int
    confidence: float
    created_at: datetime


@dataclass(slots=True)
class TemplateExampleRecord:
    template_example_id: UUID
    template_code: str
    example_name: str
    example_headers_json: list[str]
    example_rows_json: list[dict] | None
    created_at: datetime


@dataclass(slots=True)
class MappingRuleRecord:
    rule_code: str
    rule_name: str
    scene_code: str
    country_code: str
    template_code: str
    source_type: str
    status: str
    priority: int
    mapping_dsl_json: dict
    rule_summary_text: str | None
    version: int
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class RuleMappingItemRecord:
    rule_mapping_item_id: UUID
    rule_code: str
    target_field_code: str
    transform_type: str
    config_json: dict
    sort_order: int


@dataclass(slots=True)
class RuleExampleRecord:
    rule_example_id: UUID
    rule_code: str
    example_name: str
    source_sample_json: dict
    target_sample_json: dict
    created_at: datetime
