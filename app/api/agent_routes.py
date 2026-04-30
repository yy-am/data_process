from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import get_runtime_config_service, get_task_service
from app.schemas.agent import TemplateIdentificationResult
from app.schemas.common import ApiResponse
from app.schemas.runtime_config import (
    ImageOcrRuntimeConfigRequest,
    ImageOcrRuntimeConfigResponse,
    RuleDraftRuntimeConfigRequest,
    RuleDraftRuntimeConfigResponse,
    TemplateIdentificationRuntimeConfigRequest,
    TemplateIdentificationRuntimeConfigResponse,
)
from app.services.runtime_config_service import RuntimeConfigService
from app.services.task_service import TaskService
from app.schemas.agent import RuleDraftResult


router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.get("/template-identification/config", response_model=ApiResponse[TemplateIdentificationRuntimeConfigResponse | None])
def get_template_identification_config(
    service: RuntimeConfigService = Depends(get_runtime_config_service),
) -> ApiResponse[TemplateIdentificationRuntimeConfigResponse | None]:
    return ApiResponse(data=service.get_template_identification_config())


@router.post("/template-identification/config", response_model=ApiResponse[TemplateIdentificationRuntimeConfigResponse])
def update_template_identification_config(
    request: TemplateIdentificationRuntimeConfigRequest,
    service: RuntimeConfigService = Depends(get_runtime_config_service),
) -> ApiResponse[TemplateIdentificationRuntimeConfigResponse]:
    return ApiResponse(data=service.update_template_identification_config(request))


@router.post("/template-identification/tasks/{task_id}", response_model=ApiResponse[TemplateIdentificationResult])
def identify_template_context(
    task_id: UUID,
    service: TaskService = Depends(get_task_service),
) -> ApiResponse[TemplateIdentificationResult]:
    return ApiResponse(data=service.identify_template_context(task_id))


@router.get("/rule-draft/config", response_model=ApiResponse[RuleDraftRuntimeConfigResponse | None])
def get_rule_draft_config(
    service: RuntimeConfigService = Depends(get_runtime_config_service),
) -> ApiResponse[RuleDraftRuntimeConfigResponse | None]:
    return ApiResponse(data=service.get_rule_draft_config())


@router.post("/rule-draft/config", response_model=ApiResponse[RuleDraftRuntimeConfigResponse])
def update_rule_draft_config(
    request: RuleDraftRuntimeConfigRequest,
    service: RuntimeConfigService = Depends(get_runtime_config_service),
) -> ApiResponse[RuleDraftRuntimeConfigResponse]:
    return ApiResponse(data=service.update_rule_draft_config(request))


@router.get("/image-ocr/config", response_model=ApiResponse[ImageOcrRuntimeConfigResponse | None])
def get_image_ocr_config(
    service: RuntimeConfigService = Depends(get_runtime_config_service),
) -> ApiResponse[ImageOcrRuntimeConfigResponse | None]:
    return ApiResponse(data=service.get_image_ocr_config())


@router.post("/image-ocr/config", response_model=ApiResponse[ImageOcrRuntimeConfigResponse])
def update_image_ocr_config(
    request: ImageOcrRuntimeConfigRequest,
    service: RuntimeConfigService = Depends(get_runtime_config_service),
) -> ApiResponse[ImageOcrRuntimeConfigResponse]:
    return ApiResponse(data=service.update_image_ocr_config(request))


@router.post("/rule-draft/tasks/{task_id}", response_model=ApiResponse[RuleDraftResult])
def draft_rule_package(
    task_id: UUID,
    service: TaskService = Depends(get_task_service),
) -> ApiResponse[RuleDraftResult]:
    return ApiResponse(data=service.draft_rule_package(task_id))
