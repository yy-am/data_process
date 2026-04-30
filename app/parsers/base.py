from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.schemas.snapshot import ParsedInputSnapshot


class InputParser(ABC):
    @abstractmethod
    def parse(self, file_path: Path) -> ParsedInputSnapshot:
        raise NotImplementedError
