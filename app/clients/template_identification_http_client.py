from __future__ import annotations

import json
import os
import socket
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from app.core.config import AgentRuntimeConfig, TemplateIdentificationClientConfig
from app.core.exceptions import DomainError
from app.schemas.agent import TemplateIdentificationRequest, TemplateIdentificationResult


@dataclass(slots=True)
class RuntimeConfiguredTemplateIdentificationClient:
    runtime_config: AgentRuntimeConfig

    def identify(self, request_payload: TemplateIdentificationRequest) -> TemplateIdentificationResult:
        config = self._require_config()
        if config.provider == "openai_compatible_chat":
            response_payload = self._call_openai_compatible_chat(config, request_payload)
            content_text = self._extract_openai_compatible_text(response_payload)
            return self._parse_result_json(content_text)

        raise DomainError(
            code="LLM_PROVIDER_UNSUPPORTED",
            message=f"Unsupported template identification provider {config.provider}.",
            status_code=422,
        )

    def _require_config(self) -> TemplateIdentificationClientConfig:
        config = self.runtime_config.template_identification_client
        if config is None:
            raise DomainError(
                code="LLM_CLIENT_NOT_CONFIGURED",
                message="Template identification client configuration is missing.",
                status_code=503,
            )
        if not config.endpoint_url:
            raise DomainError(
                code="LLM_CLIENT_NOT_CONFIGURED",
                message="Template identification endpointUrl is required.",
                status_code=503,
            )
        return config

    def _call_openai_compatible_chat(
        self,
        config: TemplateIdentificationClientConfig,
        request_payload: TemplateIdentificationRequest,
    ) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        authorization_header = self._resolve_authorization_header(config)
        if authorization_header:
            headers["Authorization"] = authorization_header

        payload = {
            "model": config.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": request_payload.system_prompt},
                {"role": "user", "content": request_payload.user_prompt},
            ],
        }
        if config.include_response_format:
            payload["response_format"] = {"type": "json_object"}

        body = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            url=config.endpoint_url,
            data=body,
            headers=headers,
            method="POST",
        )
        opener = request.build_opener(request.ProxyHandler({}))
        try:
            with opener.open(http_request, timeout=config.timeout_seconds) as response:
                payload = response.read().decode("utf-8")
        except error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="ignore")
            raise DomainError(
                code="LLM_HTTP_ERROR",
                message=f"LLM provider returned HTTP {exc.code}: {error_body}",
                status_code=502,
            ) from exc
        except error.URLError as exc:
            raise DomainError(
                code="LLM_CONNECTION_ERROR",
                message=f"Failed to reach LLM provider: {exc.reason}",
                status_code=502,
            ) from exc
        except TimeoutError as exc:
            raise DomainError(
                code="LLM_TIMEOUT",
                message="LLM provider request timed out.",
                status_code=504,
            ) from exc
        except socket.timeout as exc:
            raise DomainError(
                code="LLM_TIMEOUT",
                message="LLM provider request timed out.",
                status_code=504,
            ) from exc

        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise DomainError(
                code="LLM_RESPONSE_INVALID",
                message="LLM provider returned non-JSON response.",
                status_code=502,
            ) from exc

    def _extract_openai_compatible_text(self, payload: dict[str, Any]) -> str:
        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict) and isinstance(item.get("text"), str):
                            text_parts.append(item["text"])
                    if text_parts:
                        return "\n".join(text_parts)

        output = payload.get("output")
        if isinstance(output, list):
            text_parts = []
            for item in output:
                if not isinstance(item, dict):
                    continue
                content = item.get("content")
                if not isinstance(content, list):
                    continue
                for content_item in content:
                    if isinstance(content_item, dict) and isinstance(content_item.get("text"), str):
                        text_parts.append(content_item["text"])
            if text_parts:
                return "\n".join(text_parts)

        if isinstance(payload.get("content"), str):
            return payload["content"]
        raise DomainError(
            code="LLM_RESPONSE_INVALID",
            message="LLM provider response does not contain recognizable text content.",
            status_code=502,
        )

    def _parse_result_json(self, content_text: str) -> TemplateIdentificationResult:
        normalized = content_text.strip()
        if normalized.startswith("```"):
            normalized = normalized.strip("`")
            if normalized.startswith("json"):
                normalized = normalized[4:].strip()
        try:
            payload = json.loads(normalized)
        except json.JSONDecodeError as exc:
            raise DomainError(
                code="LLM_RESPONSE_INVALID",
                message="LLM provider did not return valid JSON for template identification.",
                status_code=502,
            ) from exc
        return TemplateIdentificationResult.model_validate(payload)

    def _resolve_api_key(self, config: TemplateIdentificationClientConfig) -> str | None:
        if config.api_key:
            return config.api_key
        if config.api_key_env_var:
            api_key = os.getenv(config.api_key_env_var)
            if not api_key:
                raise DomainError(
                    code="LLM_CLIENT_NOT_CONFIGURED",
                    message=f"Environment variable {config.api_key_env_var} is not set.",
                    status_code=503,
                )
            return api_key
        return None

    def _resolve_authorization_header(self, config: TemplateIdentificationClientConfig) -> str | None:
        if config.authorization_header:
            return config.authorization_header
        if config.authorization_header_env_var:
            header_value = os.getenv(config.authorization_header_env_var)
            if not header_value:
                raise DomainError(
                    code="LLM_CLIENT_NOT_CONFIGURED",
                    message=f"Environment variable {config.authorization_header_env_var} is not set.",
                    status_code=503,
                )
            return header_value
        api_key = self._resolve_api_key(config)
        if api_key:
            return f"Bearer {api_key}"
        return None
