from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from app.core.exceptions import DomainError


@dataclass(slots=True)
class RuleMappingItem:
    target_field_code: str
    transform_type: str
    config: dict
    sort_order: int


@dataclass(slots=True)
class MappingRuleDefinition:
    rule_code: str
    rule_name: str
    scene_code: str
    country_code: str
    template_code: str
    source_type: str
    status: str
    priority: int
    version: int
    mapping_dsl: dict
    rule_summary_text: str | None
    mapping_items: list[RuleMappingItem]
    examples: list[dict]


@dataclass(slots=True)
class ResolvedRuleContext:
    template_code: str
    scene_code: str
    country_code: str
    rule_path: Path | None = None
    template_path: Path | None = None


class RuleRepository(ABC):
    def refresh(self) -> None:
        return None

    @abstractmethod
    def resolve_rule_context(
        self,
        *,
        template_code: str | None = None,
        template_path: Path | None = None,
        rule_path: Path | None = None,
    ) -> ResolvedRuleContext:
        raise NotImplementedError

    @abstractmethod
    def list_rules(
        self,
        *,
        template_code: str,
        scene_code: str,
        country_code: str,
        source_type: str,
        status: str,
    ) -> list[MappingRuleDefinition]:
        raise NotImplementedError


class InMemoryRuleRepository(RuleRepository):
    def __init__(self, rules: list[MappingRuleDefinition] | None = None) -> None:
        self._rules = rules or []

    @classmethod
    def from_seed_data(cls, rules: list[MappingRuleDefinition]) -> "InMemoryRuleRepository":
        return cls(rules=list(rules))

    def resolve_rule_context(
        self,
        *,
        template_code: str | None = None,
        template_path: Path | None = None,
        rule_path: Path | None = None,
    ) -> ResolvedRuleContext:
        resolved_template_code = template_code
        if template_path is not None:
            resolved_template_code = template_path.stem
        if rule_path is not None:
            raise DomainError(
                code="RULE_NOT_RESOLVED",
                message="In-memory rule repository cannot resolve context from a rule file path.",
                status_code=409,
            )
        if not resolved_template_code:
            raise DomainError(
                code="RULE_NOT_RESOLVED",
                message="Template code is required to resolve the rule context.",
                status_code=409,
            )

        matched_rules = [rule for rule in self._rules if rule.template_code == resolved_template_code]
        if not matched_rules:
            raise DomainError(
                code="RULE_NOT_RESOLVED",
                message=f"No rule context found for templateCode={resolved_template_code}.",
                status_code=409,
            )

        distinct_contexts = {
            (rule.scene_code, rule.country_code)
            for rule in matched_rules
        }
        if len(distinct_contexts) != 1:
            raise DomainError(
                code="RULE_NOT_RESOLVED",
                message=f"Multiple rule contexts found for templateCode={resolved_template_code}.",
                status_code=409,
            )

        scene_code, country_code = next(iter(distinct_contexts))
        return ResolvedRuleContext(
            template_code=resolved_template_code,
            scene_code=scene_code,
            country_code=country_code,
            template_path=template_path,
        )

    def list_rules(
        self,
        *,
        template_code: str,
        scene_code: str,
        country_code: str,
        source_type: str,
        status: str,
    ) -> list[MappingRuleDefinition]:
        return [
            rule
            for rule in self._rules
            if rule.template_code == template_code
            and rule.scene_code == scene_code
            and rule.country_code == country_code
            and rule.source_type == source_type
            and rule.status == status
        ]
