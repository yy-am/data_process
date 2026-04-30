from __future__ import annotations

from pathlib import Path

from app.parsers.excel_parser import ExcelParser
from app.repositories.knowledge_base_repository import MarkdownKnowledgeBaseRepository
from app.repositories.local_knowledge_base_rule_repository import LocalKnowledgeBaseRuleRepository


def build_knowledge_base_repository() -> MarkdownKnowledgeBaseRepository:
    return MarkdownKnowledgeBaseRepository(
        knowledge_base_root=Path("knowledge_base"),
        excel_parser=ExcelParser(),
    )


def build_rule_repository() -> LocalKnowledgeBaseRuleRepository:
    return LocalKnowledgeBaseRuleRepository(knowledge_base_root=Path("knowledge_base"))
