from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.exceptions import NotImplementedDomainError
from app.ocr.base import OCRSnapshotBuilder
from app.schemas.snapshot import ParsedInputSnapshot


@dataclass(slots=True)
class PaddleOCRSnapshotBuilder(OCRSnapshotBuilder):
    def parse_image(self, file_path: Path) -> ParsedInputSnapshot:
        raise NotImplementedDomainError(
            f"PaddleOCR-based snapshot building is not implemented yet for file {file_path.name}."
        )
