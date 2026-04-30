from pathlib import Path

from app.agents.not_implemented_template_agent import NotImplementedTemplateIdentificationAgent
from app.agents.rule_draft_agent import ConfigurableRuleDraftAgent
from app.bootstrap.repositories import build_knowledge_base_repository, build_rule_repository
from app.clients.rule_draft_http_client import RuntimeConfiguredRuleDraftClient
from app.clients.template_identification_http_client import RuntimeConfiguredTemplateIdentificationClient
from app.core.config import AgentRuntimeConfig
from app.ocr.qwen_vl_tax_screenshot_builder import QwenVlTaxScreenshotBuilder
from app.repositories.preview_repository import InMemoryPreviewRepository, PreviewRepository
from app.repositories.agent_result_repository import InMemoryAgentResultRepository, AgentResultRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.repositories.retrieval_result_repository import InMemoryRetrievalResultRepository, RetrievalResultRepository
from app.repositories.rule_repository import RuleRepository
from app.repositories.rule_retrieval_result_repository import InMemoryRuleRetrievalResultRepository, RuleRetrievalResultRepository
from app.repositories.runtime_config_repository import InMemoryRuntimeConfigRepository, RuntimeConfigRepository
from app.repositories.task_repository import InMemoryTaskRepository, TaskRepository
from app.repositories.snapshot_repository import InMemorySnapshotRepository, SnapshotRepository
from app.parsers.excel_parser import ExcelParser
from app.retrieval.header_template_retriever import HeaderTemplateRetriever
from app.retrieval.priority_rule_retriever import PriorityRuleRetriever
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.file_storage_service import FileStorageService
from app.services.runtime_config_service import RuntimeConfigService
from app.services.task_service import TaskService


_task_repository = InMemoryTaskRepository()
_snapshot_repository = InMemorySnapshotRepository()
_knowledge_base_repository = build_knowledge_base_repository()
_retrieval_result_repository = InMemoryRetrievalResultRepository()
_rule_repository = build_rule_repository()
_rule_retrieval_result_repository = InMemoryRuleRetrievalResultRepository()
_preview_repository = InMemoryPreviewRepository()
_agent_result_repository = InMemoryAgentResultRepository()
_runtime_config_repository = InMemoryRuntimeConfigRepository()
_file_storage_service = FileStorageService(root_dir=Path("storage/uploads"))
_excel_parser = ExcelParser()
_ocr_snapshot_builder = QwenVlTaxScreenshotBuilder(runtime_config=_runtime_config_repository.get_runtime_config())
_template_retriever = HeaderTemplateRetriever(knowledge_base_repository=_knowledge_base_repository)
_rule_retriever = PriorityRuleRetriever(rule_repository=_rule_repository)
_agent_runtime_config = _runtime_config_repository.get_runtime_config()
_template_identification_client = RuntimeConfiguredTemplateIdentificationClient(runtime_config=_agent_runtime_config)
_rule_draft_client = RuntimeConfiguredRuleDraftClient(runtime_config=_agent_runtime_config)
_template_identification_agent = NotImplementedTemplateIdentificationAgent(
    client=_template_identification_client,
    config=_agent_runtime_config,
    knowledge_base_repository=_knowledge_base_repository,
)
_rule_draft_agent = ConfigurableRuleDraftAgent(
    client=_rule_draft_client,
    config=_agent_runtime_config,
)
_task_service = TaskService(
    task_repository=_task_repository,
    snapshot_repository=_snapshot_repository,
    retrieval_result_repository=_retrieval_result_repository,
    rule_retrieval_result_repository=_rule_retrieval_result_repository,
    preview_repository=_preview_repository,
    agent_result_repository=_agent_result_repository,
    knowledge_base_repository=_knowledge_base_repository,
    file_storage_service=_file_storage_service,
    excel_parser=_excel_parser,
    ocr_snapshot_builder=_ocr_snapshot_builder,
    template_retriever=_template_retriever,
    rule_retriever=_rule_retriever,
    template_identification_agent=_template_identification_agent,
    rule_draft_agent=_rule_draft_agent,
)
_knowledge_base_service = KnowledgeBaseService(
    file_storage_service=_file_storage_service,
    excel_parser=_excel_parser,
    knowledge_base_repository=_knowledge_base_repository,
    rule_repository=_rule_repository,
    knowledge_base_root=Path("knowledge_base"),
)
_runtime_config_service = RuntimeConfigService(runtime_config_repository=_runtime_config_repository)


def get_task_repository() -> TaskRepository:
    return _task_repository


def get_snapshot_repository() -> SnapshotRepository:
    return _snapshot_repository


def get_knowledge_base_repository() -> KnowledgeBaseRepository:
    return _knowledge_base_repository


def get_retrieval_result_repository() -> RetrievalResultRepository:
    return _retrieval_result_repository


def get_rule_repository() -> RuleRepository:
    return _rule_repository


def get_rule_retrieval_result_repository() -> RuleRetrievalResultRepository:
    return _rule_retrieval_result_repository


def get_preview_repository() -> PreviewRepository:
    return _preview_repository


def get_agent_result_repository() -> AgentResultRepository:
    return _agent_result_repository


def get_runtime_config_repository() -> RuntimeConfigRepository:
    return _runtime_config_repository


def get_knowledge_base_service() -> KnowledgeBaseService:
    return _knowledge_base_service


def get_runtime_config_service() -> RuntimeConfigService:
    return _runtime_config_service


def get_task_service() -> TaskService:
    return _task_service
