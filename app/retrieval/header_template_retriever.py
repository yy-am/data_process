from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.domain.enums import InputType
from app.image_tax.mapping import TAX_SCREENSHOT_COUNTRY_CODE, TAX_SCREENSHOT_SCENE_CODE, TAX_SCREENSHOT_TEMPLATE_CODE
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository, TemplateDefinition
from app.retrieval.template_retriever import TemplateRetriever
from app.schemas.retrieval import RetrievalCandidate, RetrievalCandidatesResponse
from app.schemas.snapshot import InputSnapshot


@dataclass(slots=True)
class HeaderTemplateRetriever(TemplateRetriever):
    knowledge_base_repository: KnowledgeBaseRepository

    def retrieve(self, snapshot: InputSnapshot) -> RetrievalCandidatesResponse:
        if snapshot.input_type == InputType.IMAGE:
            return RetrievalCandidatesResponse(
                candidates=[
                    RetrievalCandidate(
                        code=TAX_SCREENSHOT_TEMPLATE_CODE,
                        name=TAX_SCREENSHOT_TEMPLATE_CODE,
                        score=1.0,
                        reasons=[
                            "source=image_fixed_tax_mapping",
                            f"scene={TAX_SCREENSHOT_SCENE_CODE}",
                            f"country={TAX_SCREENSHOT_COUNTRY_CODE}",
                            "image_tax_screenshot_single_mapping=true",
                        ],
                    )
                ],
                retrievedAt=datetime.now(timezone.utc).isoformat(),
            )
        templates = self.knowledge_base_repository.list_templates(source_type=snapshot.input_type.value)
        candidates = [self._catalog_candidate(template) for template in templates]
        return RetrievalCandidatesResponse(
            candidates=candidates,
            retrievedAt=datetime.now(timezone.utc).isoformat(),
        )

    def _catalog_candidate(self, template: TemplateDefinition) -> RetrievalCandidate:
        headers = [alias.header_alias for alias in template.header_aliases if alias.header_alias]
        preview_headers = headers[:8]
        return RetrievalCandidate(
            code=template.template_code,
            name=template.template_name,
            score=0.0,
            reasons=[
                "source=template_catalog_md",
                f"scene={template.scene or 'unknown'}",
                f"country={template.country or 'unknown'}",
                f"header_count={len(headers)}",
                f"headers_preview={', '.join(preview_headers)}",
            ],
        )
