from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from app.api.dependencies import get_task_service
from app.domain.enums import InputType
from app.schemas.common import ApiResponse
from app.schemas.confirmation import ConfirmationPackage, ConfirmationRequest, FinalConfirmRequest
from app.schemas.preview import PreviewRow, PreviewRowsPage, PreviewSummary
from app.schemas.retrieval import RetrievalCandidatesResponse
from app.schemas.snapshot import InputSnapshot
from app.schemas.task import TaskSummary, TaskUploadResult
from app.services.task_service import TaskService


router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.post("/upload", response_model=ApiResponse[TaskUploadResult])
async def upload_task(
    file: UploadFile = File(...),
    input_type: InputType = Form(..., alias="inputType"),
    service: TaskService = Depends(get_task_service),
) -> ApiResponse[TaskUploadResult]:
    result = await service.upload_task(upload_file=file, input_type=input_type)
    return ApiResponse(data=result)


@router.get("/{task_id}", response_model=ApiResponse[TaskSummary])
def get_task(task_id: UUID, service: TaskService = Depends(get_task_service)) -> ApiResponse[TaskSummary]:
    return ApiResponse(data=service.get_task_summary(task_id))


@router.get("/{task_id}/input-snapshot", response_model=ApiResponse[InputSnapshot])
def get_input_snapshot(task_id: UUID, service: TaskService = Depends(get_task_service)) -> ApiResponse[InputSnapshot]:
    return ApiResponse(data=service.get_input_snapshot(task_id))


@router.get("/{task_id}/template-candidates", response_model=ApiResponse[RetrievalCandidatesResponse])
def get_template_candidates(task_id: UUID, service: TaskService = Depends(get_task_service)) -> ApiResponse[RetrievalCandidatesResponse]:
    return ApiResponse(data=service.get_template_candidates(task_id))


@router.get("/{task_id}/rule-candidates", response_model=ApiResponse[RetrievalCandidatesResponse])
def get_rule_candidates(task_id: UUID, service: TaskService = Depends(get_task_service)) -> ApiResponse[RetrievalCandidatesResponse]:
    return ApiResponse(data=service.get_rule_candidates(task_id))


@router.get("/{task_id}/confirmation-package", response_model=ApiResponse[ConfirmationPackage])
def get_confirmation_package(task_id: UUID, service: TaskService = Depends(get_task_service)) -> ApiResponse[ConfirmationPackage]:
    return ApiResponse(data=service.get_confirmation_package(task_id))


@router.post("/{task_id}/confirmation", response_model=ApiResponse[dict[str, str]])
def submit_confirmation(
    task_id: UUID,
    request: ConfirmationRequest,
    service: TaskService = Depends(get_task_service),
) -> ApiResponse[dict[str, str]]:
    service.submit_confirmation(task_id, request)
    return ApiResponse(data={"taskId": str(task_id), "status": "CONFIRMED"})


@router.post("/{task_id}/run", response_model=ApiResponse[dict[str, str]])
def run_transformation(task_id: UUID, service: TaskService = Depends(get_task_service)) -> ApiResponse[dict[str, str]]:
    service.run_transformation(task_id)
    summary = service.get_task_summary(task_id)
    return ApiResponse(data={"taskId": str(task_id), "status": summary.status.value})


@router.get("/{task_id}/preview-summary", response_model=ApiResponse[PreviewSummary])
def get_preview_summary(task_id: UUID, service: TaskService = Depends(get_task_service)) -> ApiResponse[PreviewSummary]:
    return ApiResponse(data=service.get_preview_summary(task_id))


@router.get("/{task_id}/preview-rows", response_model=ApiResponse[PreviewRowsPage])
def get_preview_rows(
    task_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, alias="pageSize", ge=1, le=200),
    service: TaskService = Depends(get_task_service),
) -> ApiResponse[PreviewRowsPage]:
    return ApiResponse(data=service.get_preview_rows(task_id, page=page, page_size=page_size))


@router.get("/{task_id}/preview-rows/{row_no}", response_model=ApiResponse[PreviewRow])
def get_preview_row(task_id: UUID, row_no: int, service: TaskService = Depends(get_task_service)) -> ApiResponse[PreviewRow]:
    return ApiResponse(data=service.get_preview_row(task_id, row_no=row_no))


@router.post("/{task_id}/final-confirm", response_model=ApiResponse[dict[str, str]])
def final_confirm(
    task_id: UUID,
    request: FinalConfirmRequest,
    service: TaskService = Depends(get_task_service),
) -> ApiResponse[dict[str, str]]:
    service.final_confirm(task_id, request)
    return ApiResponse(data={"taskId": str(task_id), "status": "FINAL_CONFIRMED"})


@router.post("/{task_id}/export", response_model=ApiResponse[dict[str, str]])
def export_result(task_id: UUID, service: TaskService = Depends(get_task_service)) -> ApiResponse[dict[str, str]]:
    service.export_result(task_id)
    return ApiResponse(data={"taskId": str(task_id), "status": "EXPORTED"})


@router.get("/{task_id}/export-file", response_model=ApiResponse[dict[str, str]])
def get_export_file(task_id: UUID, service: TaskService = Depends(get_task_service)) -> ApiResponse[dict[str, str]]:
    service.get_export_file(task_id)
    return ApiResponse(data={"taskId": str(task_id), "status": "DOWNLOADED"})
