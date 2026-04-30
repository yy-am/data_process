from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.schemas.snapshot import ParsedInputSnapshot


class OCRSnapshotBuilder(ABC):
    @abstractmethod
    def parse_image(self, file_path: Path) -> ParsedInputSnapshot:
        raise NotImplementedError
