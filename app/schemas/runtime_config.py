from __future__ import annotations

from pydantic import Field

from app.schemas.common import APIModel


class TemplateIdentificationRuntimeConfigRequest(APIModel):
    provider: str
    model: str
    timeout_seconds: int = Field(default=30, alias="timeoutSeconds")
    endpoint_url: str | None = Field(default=None, alias="endpointUrl")
    api_key_env_var: str | None = Field(default=None, alias="apiKeyEnvVar")
    api_key: str | None = Field(default=None, alias="apiKey")


class TemplateIdentificationRuntimeConfigResponse(APIModel):
    provider: str
    model: str
    timeout_seconds: int = Field(alias="timeoutSeconds")
    endpoint_url: str | None = Field(default=None, alias="endpointUrl")
    api_key_env_var: str | None = Field(default=None, alias="apiKeyEnvVar")
    has_api_key: bool = Field(alias="hasApiKey")


class RuleDraftRuntimeConfigRequest(APIModel):
    provider: str
    model: str
    timeout_seconds: int = Field(default=30, alias="timeoutSeconds")
    endpoint_url: str | None = Field(default=None, alias="endpointUrl")
    api_key_env_var: str | None = Field(default=None, alias="apiKeyEnvVar")
    api_key: str | None = Field(default=None, alias="apiKey")


class RuleDraftRuntimeConfigResponse(APIModel):
    provider: str
    model: str
    timeout_seconds: int = Field(alias="timeoutSeconds")
    endpoint_url: str | None = Field(default=None, alias="endpointUrl")
    api_key_env_var: str | None = Field(default=None, alias="apiKeyEnvVar")
    has_api_key: bool = Field(alias="hasApiKey")


class ImageOcrRuntimeConfigRequest(APIModel):
    provider: str
    model: str
    timeout_seconds: int = Field(default=30, alias="timeoutSeconds")
    endpoint_url: str | None = Field(default=None, alias="endpointUrl")
    api_key_env_var: str | None = Field(default=None, alias="apiKeyEnvVar")
    api_key: str | None = Field(default=None, alias="apiKey")


class ImageOcrRuntimeConfigResponse(APIModel):
    provider: str
    model: str
    timeout_seconds: int = Field(alias="timeoutSeconds")
    endpoint_url: str | None = Field(default=None, alias="endpointUrl")
    api_key_env_var: str | None = Field(default=None, alias="apiKeyEnvVar")
    has_api_key: bool = Field(alias="hasApiKey")
