from __future__ import annotations

import json

from app.schemas.retrieval import RetrievalCandidatesResponse
from app.schemas.snapshot import InputSnapshot


def build_template_identification_system_prompt() -> str:
    return (
        "You are a template-identification agent for structured business Excel inputs. "
        "Your job is to infer templateCode, sceneCode, and countryCode from the provided input snapshot "
        "and the template catalog markdown. The catalog is the single source of truth. "
        "You must choose only templateCode, sceneCode, and countryCode values that already exist in the catalog. "
        "Do not invent templates, scenes, or countries outside the catalog. "
        "If evidence is insufficient or multiple catalog entries remain plausible, set needUserConfirm to true "
        "and use null for uncertain fields. Return JSON only with keys: templateCode, sceneCode, countryCode, "
        "confidence, alternatives, needUserConfirm, rationale. alternatives must be an array of objects with keys "
        "templateCode, sceneCode, countryCode, confidence, reasons."
    )


def build_template_identification_user_prompt(
    snapshot: InputSnapshot,
    candidates: RetrievalCandidatesResponse,
    catalog_markdown: str,
) -> str:
    snapshot_summary = {
        "taskId": str(snapshot.task_id),
        "inputType": snapshot.input_type.value,
        "sheets": [
            {
                "sheetName": sheet.sheet_name,
                "headers": sheet.headers,
                "normalizedHeaders": sheet.normalized_headers,
                "sampleRows": sheet.sample_rows[:3],
            }
            for sheet in snapshot.sheets
        ],
    }
    catalog_hint = {
        "entries": [
            {
                "code": candidate.code,
                "name": candidate.name,
                "score": candidate.score,
                "reasons": candidate.reasons,
            }
            for candidate in candidates.candidates[:20]
        ]
    }
    return (
        "Identify the most likely template context from the following parsed input snapshot and template catalog.\n\n"
        f"Input snapshot:\n{json.dumps(snapshot_summary, ensure_ascii=True, indent=2)}\n\n"
        f"Template catalog markdown:\n{catalog_markdown}\n\n"
        f"Catalog hint entries:\n{json.dumps(catalog_hint, ensure_ascii=True, indent=2)}\n\n"
        "Decision rules:\n"
        "1. The template catalog markdown is the source of truth.\n"
        "2. Choose only from catalog entries.\n"
        "3. Prefer strong header-set similarity and clear scene/country evidence from the input.\n"
        "4. If more than one catalog entry remains plausible, keep needUserConfirm=true.\n"
        "5. rationale must be a short list of evidence statements.\n"
        "6. confidence must be a number between 0 and 1.\n"
    )
