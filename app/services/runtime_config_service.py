from __future__ import annotations

from dataclasses import dataclass

from app.core.config import TemplateIdentificationClientConfig
from app.repositories.runtime_config_repository import RuntimeConfigRepository
from app.schemas.runtime_config import (
    ImageOcrRuntimeConfigRequest,
    ImageOcrRuntimeConfigResponse,
    RuleDraftRuntimeConfigRequest,
    RuleDraftRuntimeConfigResponse,
    TemplateIdentificationRuntimeConfigRequest,
    TemplateIdentificationRuntimeConfigResponse,
)


@dataclass(slots=True)
class RuntimeConfigService:
    runtime_config_repository: RuntimeConfigRepository

    def get_template_identification_config(self) -> TemplateIdentificationRuntimeConfigResponse | None:
        config = self.runtime_config_repository.get_runtime_config().template_identification_client
        if config is None:
            return None
        return self._to_response(config)

    def update_template_identification_config(
        self,
        request: TemplateIdentificationRuntimeConfigRequest,
    ) -> TemplateIdentificationRuntimeConfigResponse:
        config = TemplateIdentificationClientConfig(
            provider=request.provider,
            model=request.model,
            timeout_seconds=request.timeout_seconds,
            endpoint_url=request.endpoint_url,
            api_key_env_var=request.api_key_env_var,
            api_key=request.api_key,
            include_response_format=request.include_response_format,
        )
        runtime_config = self.runtime_config_repository.update_template_identification_config(config)
        return self._to_response(runtime_config.template_identification_client)

    def get_rule_draft_config(self) -> RuleDraftRuntimeConfigResponse | None:
        config = self.runtime_config_repository.get_runtime_config().rule_draft_client
        if config is None:
            return None
        return self._to_rule_draft_response(config)

    def update_rule_draft_config(
        self,
        request: RuleDraftRuntimeConfigRequest,
    ) -> RuleDraftRuntimeConfigResponse:
        config = TemplateIdentificationClientConfig(
            provider=request.provider,
            model=request.model,
            timeout_seconds=request.timeout_seconds,
            endpoint_url=request.endpoint_url,
            api_key_env_var=request.api_key_env_var,
            api_key=request.api_key,
            include_response_format=request.include_response_format,
        )
        runtime_config = self.runtime_config_repository.update_rule_draft_config(config)
        return self._to_rule_draft_response(runtime_config.rule_draft_client)

    def get_image_ocr_config(self) -> ImageOcrRuntimeConfigResponse | None:
        config = self.runtime_config_repository.get_runtime_config().image_ocr_client
        if config is None:
            return None
        return self._to_image_ocr_response(config)

    def update_image_ocr_config(
        self,
        request: ImageOcrRuntimeConfigRequest,
    ) -> ImageOcrRuntimeConfigResponse:
        config = TemplateIdentificationClientConfig(
            provider=request.provider,
            model=request.model,
            timeout_seconds=request.timeout_seconds,
            endpoint_url=request.endpoint_url,
            api_key_env_var=request.api_key_env_var,
            api_key=request.api_key,
            include_response_format=request.include_response_format,
        )
        runtime_config = self.runtime_config_repository.update_image_ocr_config(config)
        return self._to_image_ocr_response(runtime_config.image_ocr_client)

    def _to_response(
        self,
        config: TemplateIdentificationClientConfig | None,
    ) -> TemplateIdentificationRuntimeConfigResponse:
        assert config is not None
        return TemplateIdentificationRuntimeConfigResponse(
            provider=config.provider,
            model=config.model,
            timeoutSeconds=config.timeout_seconds,
            endpointUrl=config.endpoint_url,
            apiKeyEnvVar=config.api_key_env_var,
            hasApiKey=bool(config.api_key),
            includeResponseFormat=config.include_response_format,
        )

    def _to_rule_draft_response(
        self,
        config: TemplateIdentificationClientConfig | None,
    ) -> RuleDraftRuntimeConfigResponse:
        assert config is not None
        return RuleDraftRuntimeConfigResponse(
            provider=config.provider,
            model=config.model,
            timeoutSeconds=config.timeout_seconds,
            endpointUrl=config.endpoint_url,
            apiKeyEnvVar=config.api_key_env_var,
            hasApiKey=bool(config.api_key),
            includeResponseFormat=config.include_response_format,
        )

    def _to_image_ocr_response(
        self,
        config: TemplateIdentificationClientConfig | None,
    ) -> ImageOcrRuntimeConfigResponse:
        assert config is not None
        return ImageOcrRuntimeConfigResponse(
            provider=config.provider,
            model=config.model,
            timeoutSeconds=config.timeout_seconds,
            endpointUrl=config.endpoint_url,
            apiKeyEnvVar=config.api_key_env_var,
            hasApiKey=bool(config.api_key),
            includeResponseFormat=config.include_response_format,
        )
