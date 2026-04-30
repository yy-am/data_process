from __future__ import annotations

from typing import Protocol

from app.schemas.agent import TemplateIdentificationRequest, TemplateIdentificationResult


class TemplateIdentificationClient(Protocol):
    def identify(self, request: TemplateIdentificationRequest) -> TemplateIdentificationResult:
        ...
