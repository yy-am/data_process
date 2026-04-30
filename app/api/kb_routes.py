from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.dependencies import get_knowledge_base_service
from app.schemas.common import ApiResponse
from app.schemas.knowledge_base import KnowledgeBundleImportResult, TemplateImportResult, TemplateKnowledgeItem
from app.services.knowledge_base_service import KnowledgeBaseService


router = APIRouter(prefix="/api/v1/kb/templates", tags=["knowledge-base"])


@router.post("/import", response_model=ApiResponse[TemplateImportResult])
async def import_template_excel(
    file: UploadFile = File(...),
    template_code: str = Form(..., alias="templateCode"),
    template_name: str = Form(..., alias="templateName"),
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> ApiResponse[TemplateImportResult]:
    result = await service.import_template_excel(
        upload_file=file,
        template_code=template_code,
        template_name=template_name,
    )
    return ApiResponse(data=result)


@router.get("", response_model=ApiResponse[list[TemplateKnowledgeItem]])
def list_templates(
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> ApiResponse[list[TemplateKnowledgeItem]]:
    return ApiResponse(data=service.list_templates())


@router.post("/bundle", response_model=ApiResponse[KnowledgeBundleImportResult])
async def import_knowledge_bundle(
    scene: str = Form(...),
    country: str = Form(...),
    spec_file: UploadFile = File(..., alias="specFile"),
    instruction_text: str | None = Form(default=None, alias="instructionText"),
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> ApiResponse[KnowledgeBundleImportResult]:
    result = await service.import_knowledge_bundle(
        scene=scene,
        country=country,
        spec_file=spec_file,
        instruction_text=instruction_text,
    )
    return ApiResponse(data=result)
