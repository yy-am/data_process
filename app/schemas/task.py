from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.domain.enums import InputType, TaskStatus
from app.schemas.common import APIModel


class TaskSummary(APIModel):
    task_id: UUID = Field(alias="taskId")
    input_type: InputType = Field(alias="inputType")
    status: TaskStatus
    current_stage: TaskStatus = Field(alias="currentStage")
    current_rule_version: int = Field(default=0, alias="currentRuleVersion")
    current_result_version: int = Field(default=0, alias="currentResultVersion")
    template_code: str | None = Field(default=None, alias="templateCode")
    rule_code: str | None = Field(default=None, alias="ruleCode")
    scene_code: str | None = Field(default=None, alias="sceneCode")
    country_code: str | None = Field(default=None, alias="countryCode")
    source_fix_required: bool = Field(default=False, alias="sourceFixRequired")
    error_code: str | None = Field(default=None, alias="errorCode")
    error_message: str | None = Field(default=None, alias="errorMessage")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class TaskFileInfo(APIModel):
    original_filename: str = Field(alias="originalFilename")
    content_type: str = Field(alias="contentType")
    size: int


class TaskUploadResult(APIModel):
    task: TaskSummary
    file: TaskFileInfo
