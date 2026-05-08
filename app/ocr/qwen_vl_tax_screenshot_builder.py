from __future__ import annotations

import base64
import json
import os
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request

from app.core.config import AgentRuntimeConfig, TemplateIdentificationClientConfig
from app.core.exceptions import DomainError
from app.image_tax.mapping import (
    TAX_SCREENSHOT_COUNTRY_CODE,
    TAX_SCREENSHOT_SCENE_CODE,
    TAX_SCREENSHOT_TARGET_FIELDS,
    TAX_SCREENSHOT_TEMPLATE_CODE,
)
from app.ocr.base import OCRSnapshotBuilder
from app.schemas.snapshot import ParsedInputSnapshot, ParsedSheetSnapshot


@dataclass(slots=True)
class QwenVlTaxScreenshotBuilder(OCRSnapshotBuilder):
    runtime_config: AgentRuntimeConfig

    def parse_image(self, file_path: Path) -> ParsedInputSnapshot:
        config = self._require_config()
        payload = self._call_openai_compatible_vision(config, file_path)
        content_text = self._extract_openai_compatible_text(payload)
        result = self._parse_result_json(content_text)
        return self._build_snapshot(result)

    def _require_config(self) -> TemplateIdentificationClientConfig:
        config = self.runtime_config.image_ocr_client
        if config is None:
            raise DomainError(
                code="LLM_CLIENT_NOT_CONFIGURED",
                message="Image OCR client configuration is missing.",
                status_code=503,
            )
        if not config.endpoint_url:
            raise DomainError(
                code="LLM_CLIENT_NOT_CONFIGURED",
                message="Image OCR endpointUrl is required.",
                status_code=503,
            )
        return config

    def _call_openai_compatible_vision(
        self,
        config: TemplateIdentificationClientConfig,
        file_path: Path,
    ) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        api_key = self._resolve_api_key(config)
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        data_uri = self._build_data_uri(file_path)
        payload = {
            "model": config.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": self._build_system_prompt()},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self._build_user_prompt()},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                },
            ],
        }
        if config.include_response_format:
            payload["response_format"] = {"type": "json_object"}

        body = json.dumps(payload).encode("utf-8")
        http_request = request.Request(config.endpoint_url, data=body, headers=headers, method="POST")
        opener = request.build_opener(request.ProxyHandler({}))
        try:
            with opener.open(http_request, timeout=config.timeout_seconds) as response:
                payload = response.read().decode("utf-8")
        except error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="ignore")
            raise DomainError(
                code="LLM_HTTP_ERROR",
                message=f"Image OCR provider returned HTTP {exc.code}: {error_body}",
                status_code=502,
            ) from exc
        except error.URLError as exc:
            raise DomainError(
                code="LLM_CONNECTION_ERROR",
                message=f"Failed to reach image OCR provider: {exc.reason}",
                status_code=502,
            ) from exc
        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise DomainError(
                code="LLM_RESPONSE_INVALID",
                message="Image OCR provider returned non-JSON response.",
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
                    text_parts: list[str] = []
                    for item in content:
                        if isinstance(item, dict) and isinstance(item.get("text"), str):
                            text_parts.append(item["text"])
                    if text_parts:
                        return "\n".join(text_parts)
        raise DomainError(
            code="LLM_RESPONSE_INVALID",
            message="Image OCR provider response does not contain recognizable text content.",
            status_code=502,
        )

    def _parse_result_json(self, content_text: str) -> dict[str, Any]:
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
                message="Image OCR provider did not return valid JSON.",
                status_code=502,
            ) from exc
        if not isinstance(payload, dict):
            raise DomainError(
                code="LLM_RESPONSE_INVALID",
                message="Image OCR provider JSON payload must be an object.",
                status_code=502,
            )
        return payload

    def _build_snapshot(self, payload: dict[str, Any]) -> ParsedInputSnapshot:
        source_fields = payload.get("sourceFields")
        source_record = payload.get("sourceRecord")
        mapped_record = payload.get("mappedRecord")
        confidence = payload.get("confidence")
        rationale = payload.get("rationale")

        if not isinstance(source_fields, list) or not all(isinstance(item, str) for item in source_fields):
            raise DomainError(
                code="LLM_RESPONSE_INVALID",
                message="Image OCR response must contain sourceFields as a string array.",
                status_code=502,
            )
        if not isinstance(source_record, dict):
            raise DomainError(
                code="LLM_RESPONSE_INVALID",
                message="Image OCR response must contain sourceRecord as an object.",
                status_code=502,
            )
        if not isinstance(mapped_record, dict):
            raise DomainError(
                code="LLM_RESPONSE_INVALID",
                message="Image OCR response must contain mappedRecord as an object.",
                status_code=502,
            )
        if not isinstance(confidence, (int, float)):
            raise DomainError(
                code="LLM_RESPONSE_INVALID",
                message="Image OCR response must contain numeric confidence.",
                status_code=502,
            )
        if isinstance(rationale, str):
            rationale = [rationale] if rationale.strip() else []
        if rationale is None:
            rationale = []
        if not isinstance(rationale, list) or not all(isinstance(item, str) for item in rationale):
            raise DomainError(
                code="LLM_RESPONSE_INVALID",
                message="Image OCR response must contain rationale as a string array.",
                status_code=502,
            )

        cleaned_headers = [header.strip() for header in source_fields if header.strip()]
        if not cleaned_headers:
            raise DomainError(
                code="HEADER_NOT_DETECTED",
                message="Image OCR did not return any usable fields.",
                status_code=422,
            )

        normalized_record = {header: str(source_record.get(header, "") or "").strip() for header in cleaned_headers}
        normalized_headers = [self._normalize_header(header) for header in cleaned_headers]
        header_confidence = {header: float(confidence) for header in cleaned_headers}
        column_stats = {
            header: {
                "nonEmptySampleCount": 1 if normalized_record.get(header) else 0,
                "sampleValueCount": 1,
            }
            for header in cleaned_headers
        }
        normalized_mapped = {field: self._normalize_mapped_value(mapped_record.get(field)) for field in TAX_SCREENSHOT_TARGET_FIELDS}

        return ParsedInputSnapshot(
            inputType="IMAGE",
            sheets=[
                ParsedSheetSnapshot(
                    sheetName="TaxScreenshot",
                    headers=cleaned_headers,
                    normalizedHeaders=normalized_headers,
                    sampleRows=[normalized_record],
                    columnStats=column_stats,
                    headerConfidence=header_confidence,
                )
            ],
            metadata={
                "mappedRecord": normalized_mapped,
                "ocrConfidence": float(confidence),
                "ocrRationale": rationale,
                "templateCode": TAX_SCREENSHOT_TEMPLATE_CODE,
                "sceneCode": TAX_SCREENSHOT_SCENE_CODE,
                "countryCode": TAX_SCREENSHOT_COUNTRY_CODE,
            },
        )

    def _build_data_uri(self, file_path: Path) -> str:
        mime_type, _ = mimetypes.guess_type(file_path.name)
        mime_type = mime_type or "image/png"
        encoded = base64.b64encode(file_path.read_bytes()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    def _build_system_prompt(self) -> str:
        target_fields = ", ".join(TAX_SCREENSHOT_TARGET_FIELDS)
        return (
            "You are an OCR and structured extraction assistant for Chinese tax bureau website screenshots. "
            "Extract visible key-value fields from the screenshot and map them into one fixed target schema. "
            "Return JSON only. Do not add commentary. "
            "The JSON object must contain keys: sourceFields, sourceRecord, mappedRecord, confidence, rationale. "
            f"mappedRecord must be an object with exactly these keys: {target_fields}. "
            "If a field is not visible, set it to an empty string. "
            "sourceFields should preserve the visible field labels shown in the screenshot. "
            "sourceRecord should map visible source labels to extracted text values."
        )

    def _build_user_prompt(self) -> str:
        return (
            "This image is a Chinese tax bureau website screenshot. "
            "Please identify the visible invoice/tax detail fields, extract the values, and map them into the fixed schema. "
            "The mappedRecord target fields are: "
            + ", ".join(TAX_SCREENSHOT_TARGET_FIELDS)
            + ". "
            "Use invoice-related values such as invoice code, invoice number, invoice date, buyer/seller names, buyer/seller tax numbers, amount, tax amount, total amount, check code, status, and remarks when present."
        )

    def _normalize_header(self, header: str) -> str:
        return "".join(char.lower() for char in header.strip() if not char.isspace())

    def _normalize_mapped_value(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

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
