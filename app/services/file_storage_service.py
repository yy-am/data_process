from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


@dataclass(slots=True)
class FileStorageService:
    root_dir: Path

    async def save_upload(self, upload_file: UploadFile) -> tuple[str, int]:
        suffix = Path(upload_file.filename or "").suffix.lower()
        stored_name = f"{uuid4()}{suffix}"
        target_dir = self.root_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / stored_name

        content = await upload_file.read()
        target_path.write_bytes(content)
        await upload_file.seek(0)
        return str(target_path), len(content)
