from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.repositories.rule_repository import MappingRuleDefinition, RuleRepository
from app.retrieval.rule_retriever import RuleRetriever
from app.schemas.retrieval import RetrievalCandidate, RetrievalCandidatesResponse
from app.schemas.snapshot import InputSnapshot


@dataclass(slots=True)
class PriorityRuleRetriever(RuleRetriever):
    rule_repository: RuleRepository

    def retrieve(self, snapshot: InputSnapshot, template_code: str) -> RetrievalCandidatesResponse:
        resolved_context = self.rule_repository.resolve_rule_context(template_code=template_code)
        rules = self.rule_repository.list_rules(
            template_code=resolved_context.template_code,
            scene_code=resolved_context.scene_code,
            country_code=resolved_context.country_code,
            source_type=snapshot.input_type.value,
            status="ACTIVE",
        )
        ranked_rules = sorted(
            (self._score_rule(snapshot, rule) for rule in rules),
            key=lambda item: item.score,
            reverse=True,
        )
        return RetrievalCandidatesResponse(
            candidates=ranked_rules,
            retrievedAt=datetime.now(timezone.utc).isoformat(),
        )

    def _score_rule(self, snapshot: InputSnapshot, rule: MappingRuleDefinition) -> RetrievalCandidate:
        input_headers = {
            normalized_header
            for sheet in snapshot.sheets
            for normalized_header in sheet.normalized_headers
            if normalized_header
        }
        dsl_coverage = self._calculate_dsl_coverage(rule, input_headers)
        example_score = self._calculate_example_score(rule)
        priority_score = min(rule.priority / 100.0, 1.0)
        score = round(priority_score * 0.6 + dsl_coverage * 0.3 + example_score * 0.1, 4)
        return RetrievalCandidate(
            code=rule.rule_code,
            name=rule.rule_name,
            score=score,
            reasons=[
                f"priority={rule.priority}",
                f"dsl_coverage={dsl_coverage:.2f}",
                f"example_count={len(rule.examples)}",
            ],
        )

    def _calculate_dsl_coverage(self, rule: MappingRuleDefinition, input_headers: set[str]) -> float:
        source_fields: set[str] = set()
        for item in rule.mapping_items:
            source_field = item.config.get("sourceField") or item.config.get("source_field")
            if isinstance(source_field, str) and source_field.strip():
                source_fields.add(self._normalize_header(source_field))

        if not source_fields:
            return 0.0

        matched_fields = sum(1 for field in source_fields if field in input_headers)
        return matched_fields / len(source_fields)

    def _calculate_example_score(self, rule: MappingRuleDefinition) -> float:
        if not rule.examples:
            return 0.0
        return min(len(rule.examples) / 5.0, 1.0)

    def _normalize_header(self, value: str) -> str:
        return "".join(char.lower() for char in value.strip() if not char.isspace())
