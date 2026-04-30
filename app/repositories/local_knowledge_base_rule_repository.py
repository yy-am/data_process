from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from app.core.exceptions import DomainError
from app.repositories.rule_repository import (
    MappingRuleDefinition,
    ResolvedRuleContext,
    RuleMappingItem,
    RuleRepository,
)


@dataclass(slots=True)
class LocalKnowledgeBaseRuleRepository(RuleRepository):
    knowledge_base_root: Path
    _context_by_template_code: dict[str, ResolvedRuleContext] = field(default_factory=dict, init=False)
    _context_by_template_path: dict[Path, ResolvedRuleContext] = field(default_factory=dict, init=False)
    _context_by_rule_path: dict[Path, ResolvedRuleContext] = field(default_factory=dict, init=False)
    _rules_by_rule_path: dict[Path, MappingRuleDefinition] = field(default_factory=dict, init=False)
    _index_loaded: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.knowledge_base_root = Path(self.knowledge_base_root).resolve()

    def resolve_rule_context(
        self,
        *,
        template_code: str | None = None,
        template_path: Path | None = None,
        rule_path: Path | None = None,
    ) -> ResolvedRuleContext:
        if rule_path is not None:
            return self._resolve_from_rule_path(rule_path)
        if template_path is not None:
            return self._resolve_from_template_path(template_path)
        if template_code is not None:
            return self._resolve_from_template_code(template_code)
        raise DomainError(
            code="RULE_NOT_RESOLVED",
            message="Either template_code, template_path, or rule_path is required to resolve a rule context.",
            status_code=409,
        )

    def refresh(self) -> None:
        self._context_by_template_code.clear()
        self._context_by_template_path.clear()
        self._context_by_rule_path.clear()
        self._rules_by_rule_path.clear()
        self._index_loaded = False

    def list_rules(
        self,
        *,
        template_code: str,
        scene_code: str,
        country_code: str,
        source_type: str,
        status: str,
    ) -> list[MappingRuleDefinition]:
        resolved_context = self.resolve_rule_context(template_code=template_code)
        if (
            resolved_context.scene_code.strip().upper() != scene_code.strip().upper()
            or resolved_context.country_code.strip().upper() != country_code.strip().upper()
        ):
            return []

        rule = self._load_rule_definition(resolved_context.rule_path)
        if rule.source_type != source_type or rule.status != status:
            return []
        return [rule]

    def _resolve_from_template_code(self, template_code: str) -> ResolvedRuleContext:
        self._ensure_index_loaded()
        try:
            return self._context_by_template_code[template_code]
        except KeyError as exc:
            raise DomainError(
                code="RULE_NOT_RESOLVED",
                message=f"No knowledge-base rule context found for templateCode={template_code}.",
                status_code=409,
            ) from exc

    def _resolve_from_template_path(self, template_path: Path) -> ResolvedRuleContext:
        resolved_template_path = template_path.resolve()
        self._ensure_path_within_root(resolved_template_path)
        rule_path = resolved_template_path.parent / "rule.json"
        if not rule_path.is_file():
            raise DomainError(
                code="RULE_NOT_RESOLVED",
                message=f"No rule.json found next to matched template: {resolved_template_path}.",
                status_code=409,
            )

        context = self._resolve_from_rule_path(rule_path)
        if context.template_code != resolved_template_path.stem:
            raise DomainError(
                code="RULE_NOT_RESOLVED",
                message=(
                    f"Matched template file {resolved_template_path.name} does not match "
                    f"rule templateCode={context.template_code}."
                ),
                status_code=409,
            )

        if resolved_template_path.suffix.lower() != ".xlsx":
            raise DomainError(
                code="RULE_NOT_RESOLVED",
                message=f"Matched template must be an .xlsx file: {resolved_template_path}.",
                status_code=409,
            )

        return ResolvedRuleContext(
            template_code=context.template_code,
            scene_code=context.scene_code,
            country_code=context.country_code,
            rule_path=context.rule_path,
            template_path=resolved_template_path,
        )

    def _resolve_from_rule_path(self, rule_path: Path) -> ResolvedRuleContext:
        resolved_rule_path = rule_path.resolve()
        self._ensure_path_within_root(resolved_rule_path)
        rule = self._load_rule_definition(resolved_rule_path)
        template_path = resolved_rule_path.parent / f"{rule.template_code}.xlsx"
        if not template_path.is_file():
            template_path = None

        return ResolvedRuleContext(
            template_code=rule.template_code,
            scene_code=rule.scene_code,
            country_code=rule.country_code,
            rule_path=resolved_rule_path,
            template_path=template_path,
        )

    def _ensure_index_loaded(self) -> None:
        if self._index_loaded:
            return

        knowledge_base_root = self.knowledge_base_root
        if not knowledge_base_root.is_dir():
            raise DomainError(
                code="RULE_NOT_RESOLVED",
                message=f"Knowledge base directory does not exist: {knowledge_base_root}.",
                status_code=409,
            )

        for rule_path in knowledge_base_root.glob("*/*/rule.json"):
            context = self._resolve_from_rule_path(rule_path)
            if context.template_code in self._context_by_template_code:
                raise DomainError(
                    code="RULE_NOT_RESOLVED",
                    message=f"Duplicate rule context found for templateCode={context.template_code}.",
                    status_code=409,
                )
            self._context_by_template_code[context.template_code] = context
            if context.rule_path is not None:
                self._context_by_rule_path[context.rule_path] = context
            if context.template_path is not None:
                self._context_by_template_path[context.template_path] = context

        self._index_loaded = True

    def _ensure_path_within_root(self, path: Path) -> None:
        try:
            path.relative_to(self.knowledge_base_root)
        except ValueError as exc:
            raise DomainError(
                code="RULE_NOT_RESOLVED",
                message=f"Resolved path is outside the knowledge base root: {path}.",
                status_code=409,
            ) from exc

    def _load_rule_definition(self, rule_path: Path | None) -> MappingRuleDefinition:
        if rule_path is None:
            raise DomainError(
                code="RULE_NOT_RESOLVED",
                message="Rule path is required to load a knowledge-base mapping rule.",
                status_code=409,
            )

        resolved_rule_path = rule_path.resolve()
        cached_rule = self._rules_by_rule_path.get(resolved_rule_path)
        if cached_rule is not None:
            return cached_rule

        if not resolved_rule_path.is_file():
            raise DomainError(
                code="RULE_NOT_RESOLVED",
                message=f"Rule file does not exist: {resolved_rule_path}.",
                status_code=409,
            )

        payload = json.loads(resolved_rule_path.read_text(encoding="utf-8"))
        mapping_dsl = payload.get("mappingDsl")
        if not isinstance(mapping_dsl, dict):
            raise DomainError(
                code="RULE_NOT_RESOLVED",
                message=f"Rule file is missing mappingDsl: {resolved_rule_path}.",
                status_code=409,
            )

        mappings = mapping_dsl.get("mappings")
        if not isinstance(mappings, list):
            raise DomainError(
                code="RULE_NOT_RESOLVED",
                message=f"Rule file is missing mappingDsl.mappings: {resolved_rule_path}.",
                status_code=409,
            )

        rule = MappingRuleDefinition(
            rule_code=self._require_string(payload, "ruleCode", resolved_rule_path),
            rule_name=self._require_string(payload, "ruleName", resolved_rule_path),
            scene_code=self._require_string(payload, "sceneCode", resolved_rule_path),
            country_code=self._require_string(payload, "countryCode", resolved_rule_path),
            template_code=self._require_string(payload, "templateCode", resolved_rule_path),
            source_type=self._require_string(payload, "sourceType", resolved_rule_path),
            status=self._require_string(payload, "status", resolved_rule_path),
            priority=self._require_int(payload, "priority", resolved_rule_path),
            version=self._require_int(payload, "version", resolved_rule_path),
            mapping_dsl=mapping_dsl,
            rule_summary_text=payload.get("ruleSummaryText"),
            mapping_items=self._build_mapping_items(mappings),
            examples=self._optional_list(payload.get("examples"), "examples", resolved_rule_path),
        )
        self._rules_by_rule_path[resolved_rule_path] = rule
        return rule

    def _build_mapping_items(self, mappings: list[object]) -> list[RuleMappingItem]:
        items: list[RuleMappingItem] = []
        for index, mapping in enumerate(mappings, start=1):
            if not isinstance(mapping, dict):
                raise DomainError(
                    code="RULE_NOT_RESOLVED",
                    message="Each mappingDsl.mappings item must be an object.",
                    status_code=409,
                )
            target_field_code = mapping.get("targetField") or mapping.get("targetFieldCode")
            transform_type = mapping.get("type") or mapping.get("transformType")
            if not isinstance(target_field_code, str) or not target_field_code.strip():
                raise DomainError(
                    code="RULE_NOT_RESOLVED",
                    message="Each mappingDsl.mappings item must define targetField.",
                    status_code=409,
                )
            if not isinstance(transform_type, str) or not transform_type.strip():
                raise DomainError(
                    code="RULE_NOT_RESOLVED",
                    message="Each mappingDsl.mappings item must define type.",
                    status_code=409,
                )
            config = {
                key: value
                for key, value in mapping.items()
                if key not in {"targetField", "targetFieldCode", "type", "transformType"}
            }
            items.append(
                RuleMappingItem(
                    target_field_code=target_field_code,
                    transform_type=transform_type,
                    config=config,
                    sort_order=index,
                )
            )
        return items

    def _require_string(self, payload: dict, key: str, rule_path: Path) -> str:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise DomainError(
                code="RULE_NOT_RESOLVED",
                message=f"Rule file is missing {key}: {rule_path}.",
                status_code=409,
            )
        return value.strip()

    def _require_int(self, payload: dict, key: str, rule_path: Path) -> int:
        value = payload.get(key)
        if not isinstance(value, int):
            raise DomainError(
                code="RULE_NOT_RESOLVED",
                message=f"Rule file is missing {key}: {rule_path}.",
                status_code=409,
            )
        return value

    def _optional_list(self, value: object, key: str, rule_path: Path) -> list[dict]:
        if value is None:
            return []
        if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
            raise DomainError(
                code="RULE_NOT_RESOLVED",
                message=f"Rule file field {key} must be a list of objects: {rule_path}.",
                status_code=409,
            )
        return list(value)
