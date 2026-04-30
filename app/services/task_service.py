from __future__ import annotations

from app.agents.template_identification_agent import TemplateIdentificationAgent
from app.agents.rule_draft_agent import RuleDraftAgent
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile

from app.core.exceptions import DomainError, NotImplementedDomainError
from app.domain.enums import InputType, TaskStatus
from app.ocr.base import OCRSnapshotBuilder
from app.parsers.base import InputParser
from app.image_tax.mapping import (
    TAX_SCREENSHOT_COUNTRY_CODE,
    TAX_SCREENSHOT_RULE_CODE,
    TAX_SCREENSHOT_SCENE_CODE,
    TAX_SCREENSHOT_TEMPLATE_CODE,
    build_image_preview_from_mapped_record,
)
from app.repositories.agent_result_repository import AgentResultRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.repositories.preview_repository import PreviewRepository
from app.repositories.retrieval_result_repository import RetrievalResultRepository
from app.repositories.rule_retrieval_result_repository import RuleRetrievalResultRepository
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.task_repository import StoredTask, TaskRepository
from app.retrieval.rule_retriever import RuleRetriever
from app.retrieval.template_retriever import TemplateRetriever
from app.schemas.confirmation import ConfirmationPackage, ConfirmationRequest, FinalConfirmRequest
from app.schemas.preview import PreviewRow, PreviewRowsPage, PreviewSummary
from app.schemas.retrieval import RetrievalCandidate, RetrievalCandidatesResponse
from app.schemas.snapshot import InputSnapshot
from app.schemas.task import TaskFileInfo, TaskUploadResult
from app.services.file_storage_service import FileStorageService


@dataclass(slots=True)
class TaskService:
    task_repository: TaskRepository
    snapshot_repository: SnapshotRepository
    retrieval_result_repository: RetrievalResultRepository
    rule_retrieval_result_repository: RuleRetrievalResultRepository
    preview_repository: PreviewRepository
    agent_result_repository: AgentResultRepository
    knowledge_base_repository: KnowledgeBaseRepository
    file_storage_service: FileStorageService
    excel_parser: InputParser
    ocr_snapshot_builder: OCRSnapshotBuilder
    template_retriever: TemplateRetriever
    rule_retriever: RuleRetriever
    template_identification_agent: TemplateIdentificationAgent
    rule_draft_agent: RuleDraftAgent

    async def upload_task(self, upload_file: UploadFile, input_type: InputType) -> TaskUploadResult:
        stored_filename, size = await self.file_storage_service.save_upload(upload_file)
        file_info = TaskFileInfo(
            originalFilename=upload_file.filename or "",
            contentType=upload_file.content_type or "application/octet-stream",
            size=size,
        )
        stored = self.task_repository.create_task(
            input_type=input_type,
            file_info=file_info,
            stored_filename=stored_filename,
        )
        self.task_repository.update_task_status(stored.summary.task_id, TaskStatus.PARSING_INPUT)
        try:
            parsed_snapshot = self._parse_input(stored_filename=stored.stored_filename, input_type=input_type)
            self.snapshot_repository.save_snapshot(stored.summary.task_id, parsed_snapshot)
            stored = self.task_repository.update_task_status(stored.summary.task_id, TaskStatus.INPUT_PARSED)
            if input_type == InputType.IMAGE:
                stored = self.task_repository.update_task_resolution(
                    stored.summary.task_id,
                    template_code=TAX_SCREENSHOT_TEMPLATE_CODE,
                    scene_code=TAX_SCREENSHOT_SCENE_CODE,
                    country_code=TAX_SCREENSHOT_COUNTRY_CODE,
                )
        except DomainError as exc:
            stored = self.task_repository.update_task_status(
                stored.summary.task_id,
                TaskStatus.FAILED,
                error_code=exc.code,
                error_message=exc.message,
            )
            raise exc
        return TaskUploadResult(task=stored.summary, file=stored.file)

    def get_task_summary(self, task_id: UUID):
        return self._require_task(task_id).summary

    def get_input_snapshot(self, task_id: UUID) -> InputSnapshot:
        self._require_status(task_id, {TaskStatus.INPUT_PARSED, TaskStatus.TEMPLATE_RETRIEVED, TaskStatus.RULE_RETRIEVED, TaskStatus.RULE_DRAFTED, TaskStatus.WAITING_CONFIRMATION, TaskStatus.READY_TO_RUN, TaskStatus.TRANSFORMING, TaskStatus.PREVIEW_READY, TaskStatus.FINAL_CONFIRMED, TaskStatus.EXPORTED})
        snapshot = self.snapshot_repository.get_snapshot(task_id)
        if snapshot is None:
            raise DomainError(
                code="HEADER_NOT_DETECTED",
                message="Input snapshot does not exist for the current task.",
                status_code=404,
            )
        return snapshot

    def get_template_candidates(self, task_id: UUID) -> RetrievalCandidatesResponse:
        stored = self._require_status(task_id, {TaskStatus.INPUT_PARSED, TaskStatus.TEMPLATE_RETRIEVED, TaskStatus.RULE_RETRIEVED, TaskStatus.RULE_DRAFTED, TaskStatus.WAITING_CONFIRMATION, TaskStatus.READY_TO_RUN, TaskStatus.TRANSFORMING, TaskStatus.PREVIEW_READY, TaskStatus.FINAL_CONFIRMED, TaskStatus.EXPORTED})
        existing = self.retrieval_result_repository.get_template_candidates(task_id)
        if existing is not None:
            return existing

        snapshot = self.snapshot_repository.get_snapshot(task_id)
        if snapshot is None:
            raise DomainError(
                code="HEADER_NOT_DETECTED",
                message="Input snapshot does not exist for the current task.",
                status_code=404,
            )

        response = self.template_retriever.retrieve(snapshot)
        self.retrieval_result_repository.save_template_candidates(task_id, response)
        self._try_resolve_template_from_candidates(task_id, response)
        if stored.summary.status == TaskStatus.INPUT_PARSED:
            self.task_repository.update_task_status(task_id, TaskStatus.TEMPLATE_RETRIEVED)
        return response

    def identify_template_context(self, task_id: UUID):
        stored = self._require_status(task_id, {TaskStatus.TEMPLATE_RETRIEVED, TaskStatus.RULE_RETRIEVED, TaskStatus.RULE_DRAFTED, TaskStatus.WAITING_CONFIRMATION, TaskStatus.READY_TO_RUN, TaskStatus.TRANSFORMING, TaskStatus.PREVIEW_READY, TaskStatus.FINAL_CONFIRMED, TaskStatus.EXPORTED})
        if stored.summary.template_code and stored.summary.scene_code and stored.summary.country_code:
            raise DomainError(
                code="TASK_STATUS_INVALID",
                message="Template context is already resolved from knowledge-base matching.",
                status_code=409,
            )
        existing = self.agent_result_repository.get_template_identification_result(task_id)
        if existing is not None:
            return existing

        snapshot = self.snapshot_repository.get_snapshot(task_id)
        if snapshot is None:
            raise DomainError(
                code="HEADER_NOT_DETECTED",
                message="Input snapshot does not exist for the current task.",
                status_code=404,
            )

        candidates = self.retrieval_result_repository.get_template_candidates(task_id)
        if candidates is None:
            raise DomainError(
                code="TEMPLATE_NOT_RESOLVED",
                message="Template candidates must be retrieved before template identification.",
                status_code=409,
            )

        result = self.template_identification_agent.identify(snapshot, candidates)
        self.agent_result_repository.save_template_identification_result(task_id, result)
        self.task_repository.update_task_resolution(
            task_id,
            template_code=result.template_code,
            scene_code=result.scene_code,
            country_code=result.country_code,
        )
        return result

    def get_rule_candidates(self, task_id: UUID) -> RetrievalCandidatesResponse:
        stored = self._require_status(task_id, {TaskStatus.INPUT_PARSED, TaskStatus.TEMPLATE_RETRIEVED, TaskStatus.RULE_RETRIEVED, TaskStatus.RULE_DRAFTED, TaskStatus.WAITING_CONFIRMATION, TaskStatus.READY_TO_RUN, TaskStatus.TRANSFORMING, TaskStatus.PREVIEW_READY, TaskStatus.FINAL_CONFIRMED, TaskStatus.EXPORTED})
        existing = self.rule_retrieval_result_repository.get_rule_candidates(task_id)
        if existing is not None:
            return existing

        summary = stored.summary
        if summary.input_type == InputType.IMAGE:
            response = RetrievalCandidatesResponse(
                candidates=[
                    RetrievalCandidate(
                        code=TAX_SCREENSHOT_RULE_CODE,
                        name=TAX_SCREENSHOT_RULE_CODE,
                        score=1.0,
                        reasons=[
                            "source=image_fixed_tax_mapping",
                            "single_mapping_logic=true",
                            f"templateCode={TAX_SCREENSHOT_TEMPLATE_CODE}",
                        ],
                    )
                ],
                retrievedAt=datetime.now(timezone.utc).isoformat(),
            )
            self.rule_retrieval_result_repository.save_rule_candidates(task_id, response)
            if stored.summary.status in {TaskStatus.INPUT_PARSED, TaskStatus.TEMPLATE_RETRIEVED}:
                self.task_repository.update_task_status(task_id, TaskStatus.RULE_RETRIEVED)
            return response
        if not summary.template_code:
            raise DomainError(
                code="TEMPLATE_NOT_RESOLVED",
                message="Rule retrieval requires a matched templateCode before querying rules.",
                status_code=409,
            )
        if not summary.scene_code or not summary.country_code:
            raise DomainError(
                code="RULE_NOT_RESOLVED",
                message="Rule retrieval requires matched sceneCode and countryCode before querying rules.",
                status_code=409,
            )

        snapshot = self.snapshot_repository.get_snapshot(task_id)
        if snapshot is None:
            raise DomainError(
                code="HEADER_NOT_DETECTED",
                message="Input snapshot does not exist for the current task.",
                status_code=404,
            )

        snapshot = snapshot.model_copy(
            update={
                "metadata": {
                    **snapshot.metadata,
                    "sceneCode": summary.scene_code,
                    "countryCode": summary.country_code,
                }
            }
        )
        response = self.rule_retriever.retrieve(snapshot, summary.template_code)
        self.rule_retrieval_result_repository.save_rule_candidates(task_id, response)
        if stored.summary.status in {TaskStatus.INPUT_PARSED, TaskStatus.TEMPLATE_RETRIEVED}:
            self.task_repository.update_task_status(task_id, TaskStatus.RULE_RETRIEVED)
        return response

    def draft_rule_package(self, task_id: UUID):
        stored = self._require_status(task_id, {TaskStatus.RULE_RETRIEVED, TaskStatus.RULE_DRAFTED, TaskStatus.WAITING_CONFIRMATION, TaskStatus.READY_TO_RUN})
        existing = self.agent_result_repository.get_rule_draft_result(task_id)
        if existing is not None:
            return existing

        summary = stored.summary
        if not summary.template_code or not summary.scene_code or not summary.country_code:
            raise DomainError(
                code="RULE_NOT_RESOLVED",
                message="Rule draft requires resolved templateCode, sceneCode, and countryCode.",
                status_code=409,
            )
        snapshot = self.snapshot_repository.get_snapshot(task_id)
        if snapshot is None:
            raise DomainError(
                code="HEADER_NOT_DETECTED",
                message="Input snapshot does not exist for the current task.",
                status_code=404,
            )
        rule_candidates = self.rule_retrieval_result_repository.get_rule_candidates(task_id)
        if rule_candidates is None:
            raise DomainError(
                code="RULE_NOT_RESOLVED",
                message="Rule candidates must be retrieved before rule drafting.",
                status_code=409,
            )
        result = self.rule_draft_agent.draft(
            snapshot=snapshot,
            template_code=summary.template_code,
            scene_code=summary.scene_code,
            country_code=summary.country_code,
            rule_candidates=rule_candidates,
        )
        self.agent_result_repository.save_rule_draft_result(task_id, result)
        if stored.summary.status == TaskStatus.RULE_RETRIEVED:
            self.task_repository.update_task_status(task_id, TaskStatus.RULE_DRAFTED)
        return result

    def get_confirmation_package(self, task_id: UUID) -> ConfirmationPackage:
        stored = self._require_status(task_id, {TaskStatus.RULE_DRAFTED, TaskStatus.WAITING_CONFIRMATION, TaskStatus.READY_TO_RUN, TaskStatus.TRANSFORMING, TaskStatus.PREVIEW_READY, TaskStatus.FINAL_CONFIRMED, TaskStatus.EXPORTED})
        existing = self.agent_result_repository.get_rule_draft_result(task_id)
        if existing is None:
            raise DomainError(
                code="BLOCKING_ISSUES_EXIST",
                message="Rule draft package does not exist for the current task.",
                status_code=409,
            )
        if stored.summary.status == TaskStatus.RULE_DRAFTED:
            self.task_repository.update_task_status(task_id, TaskStatus.WAITING_CONFIRMATION)
        return ConfirmationPackage.model_validate(existing.model_dump(by_alias=True))

    def submit_confirmation(self, task_id: UUID, request: ConfirmationRequest) -> None:
        self._require_status(task_id, {TaskStatus.WAITING_CONFIRMATION})
        raise NotImplementedDomainError("Confirmation persistence and effective rule generation are not implemented yet.")

    def run_transformation(self, task_id: UUID) -> None:
        stored = self._require_status(task_id, {TaskStatus.INPUT_PARSED, TaskStatus.READY_TO_RUN, TaskStatus.RULE_RETRIEVED, TaskStatus.RULE_DRAFTED, TaskStatus.WAITING_CONFIRMATION})
        if stored.summary.input_type == InputType.IMAGE:
            snapshot = self.snapshot_repository.get_snapshot(task_id)
            if snapshot is None:
                raise DomainError(
                    code="HEADER_NOT_DETECTED",
                    message="Input snapshot does not exist for the current task.",
                    status_code=404,
                )
            mapped_record = snapshot.metadata.get("mappedRecord")
            if not isinstance(mapped_record, dict):
                raise DomainError(
                    code="RULE_NOT_RESOLVED",
                    message="Image OCR snapshot does not contain a mapped record.",
                    status_code=409,
                )
            summary, page = build_image_preview_from_mapped_record(mapped_record)
            self.preview_repository.save_preview(task_id, summary, page)
            self.task_repository.update_task_status(task_id, TaskStatus.PREVIEW_READY)
            return
        self._require_status(task_id, {TaskStatus.READY_TO_RUN})
        raise NotImplementedDomainError("Rule execution and staging writes are not implemented yet.")

    def get_preview_summary(self, task_id: UUID) -> PreviewSummary:
        stored = self._require_status(task_id, {TaskStatus.PREVIEW_READY, TaskStatus.FINAL_CONFIRMED, TaskStatus.EXPORTED})
        if stored.summary.input_type == InputType.IMAGE:
            summary = self.preview_repository.get_preview_summary(task_id)
            if summary is None:
                raise DomainError(
                    code="PREVIEW_NOT_READY",
                    message="Preview summary does not exist for the current task.",
                    status_code=404,
                )
            return summary
        raise NotImplementedDomainError("Staging summary querying is not implemented yet.")

    def get_preview_rows(self, task_id: UUID, page: int, page_size: int) -> PreviewRowsPage:
        stored = self._require_status(task_id, {TaskStatus.PREVIEW_READY, TaskStatus.FINAL_CONFIRMED, TaskStatus.EXPORTED})
        if stored.summary.input_type == InputType.IMAGE:
            rows_page = self.preview_repository.get_preview_page(task_id)
            if rows_page is None:
                raise DomainError(
                    code="PREVIEW_NOT_READY",
                    message="Preview rows do not exist for the current task.",
                    status_code=404,
                )
            return rows_page
        raise NotImplementedDomainError("Staging row pagination is not implemented yet.")

    def get_preview_row(self, task_id: UUID, row_no: int) -> PreviewRow:
        stored = self._require_status(task_id, {TaskStatus.PREVIEW_READY, TaskStatus.FINAL_CONFIRMED, TaskStatus.EXPORTED})
        if stored.summary.input_type == InputType.IMAGE:
            row = self.preview_repository.get_preview_row(task_id, row_no)
            if row is None:
                raise DomainError(
                    code="PREVIEW_NOT_READY",
                    message=f"Preview row {row_no} does not exist for the current task.",
                    status_code=404,
                )
            return row
        raise NotImplementedDomainError("Staging row detail querying is not implemented yet.")

    def final_confirm(self, task_id: UUID, request: FinalConfirmRequest) -> None:
        self._require_status(task_id, {TaskStatus.PREVIEW_READY})
        raise NotImplementedDomainError("Final confirmation is not implemented yet.")

    def export_result(self, task_id: UUID) -> None:
        self._require_status(task_id, {TaskStatus.FINAL_CONFIRMED})
        raise NotImplementedDomainError("Export is not implemented yet.")

    def get_export_file(self, task_id: UUID) -> None:
        self._require_status(task_id, {TaskStatus.EXPORTED})
        raise NotImplementedDomainError("Export file download is not implemented yet.")


    def _require_task(self, task_id: UUID) -> StoredTask:
        stored = self.task_repository.get_task(task_id)
        if stored is None:
            raise DomainError(code="TASK_NOT_FOUND", message="Task does not exist.", status_code=404)
        return stored

    def _require_status(self, task_id: UUID, allowed_statuses: set[TaskStatus]) -> StoredTask:
        stored = self._require_task(task_id)
        if stored.summary.status not in allowed_statuses:
            raise DomainError(
                code="TASK_STATUS_INVALID",
                message=f"Operation is not allowed when task status is {stored.summary.status}.",
                status_code=409,
            )
        return stored

    def _parse_input(self, stored_filename: str, input_type: InputType):
        if input_type == InputType.EXCEL:
            return self.excel_parser.parse(Path(stored_filename))
        if input_type == InputType.IMAGE:
            return self.ocr_snapshot_builder.parse_image(Path(stored_filename))
        raise DomainError(code="UNSUPPORTED_FILE_TYPE", message=f"Unsupported input type {input_type}.", status_code=422)

    def _try_resolve_template_from_candidates(
        self,
        task_id: UUID,
        candidates: RetrievalCandidatesResponse,
    ) -> None:
        if not candidates.candidates:
            return

        ranked = sorted(candidates.candidates, key=lambda item: item.score, reverse=True)
        top_candidate = ranked[0]
        if top_candidate.score <= 0:
            return

        tied_top = [candidate for candidate in ranked if candidate.score == top_candidate.score]
        if len(tied_top) != 1:
            return

        matched_template = next(
            (template for template in self.knowledge_base_repository.list_all_templates() if template.template_code == top_candidate.code),
            None,
        )
        if matched_template is None:
            return
        if not matched_template.scene or not matched_template.country:
            return

        self.task_repository.update_task_resolution(
            task_id,
            template_code=matched_template.template_code,
            scene_code=matched_template.scene.upper(),
            country_code=matched_template.country.upper(),
        )
