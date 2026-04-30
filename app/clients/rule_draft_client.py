from __future__ import annotations

from typing import Protocol

from app.schemas.agent import RuleDraftRequest, RuleDraftResult


class RuleDraftClient(Protocol):
    def draft(self, request: RuleDraftRequest) -> RuleDraftResult:
        ...
