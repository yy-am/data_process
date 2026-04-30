from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DomainError(Exception):
    code: str
    message: str
    status_code: int


class NotImplementedDomainError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(code="NOT_IMPLEMENTED", message=message, status_code=501)
