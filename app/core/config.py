from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TemplateIdentificationClientConfig:
    provider: str
    model: str
    timeout_seconds: int = 30
    endpoint_url: str | None = None
    api_key_env_var: str | None = None
    api_key: str | None = None
    authorization_header_env_var: str | None = None
    authorization_header: str | None = None
    include_response_format: bool = True


@dataclass(slots=True)
class AgentRuntimeConfig:
    template_identification_client: TemplateIdentificationClientConfig | None = None
    rule_draft_client: TemplateIdentificationClientConfig | None = None
    image_ocr_client: TemplateIdentificationClientConfig | None = None
