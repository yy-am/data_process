from __future__ import annotations

import json

from app.schemas.retrieval import RetrievalCandidatesResponse
from app.schemas.snapshot import InputSnapshot


def build_rule_draft_system_prompt() -> str:
    return (
        "You are a rule-draft agent for structured business documents. "
        "Draft a mapping DSL and identify ambiguity, missing fields, default suggestions, "
        "and blocking issues based only on the provided input snapshot, resolved template context, "
        "and rule candidates. Do not invent hidden fallback transformations. "
        "Only use these transform types: direct, constant, trim, trim_upper, trim_lower, "
        "to_number, to_date, enum_map, concat, fallback. "
        "Return JSON only with keys: templateCode, sceneCode, countryCode, draftDsl, "
        "ambiguousMappings, missingFields, defaultSuggestions, blockingIssues, rationale."
    )


def build_rule_draft_user_prompt(
    snapshot: InputSnapshot,
    template_code: str,
    scene_code: str,
    country_code: str,
    rule_candidates: RetrievalCandidatesResponse,
) -> str:
    snapshot_summary = {
        "taskId": str(snapshot.task_id),
        "inputType": snapshot.input_type.value,
        "headers": [sheet.headers for sheet in snapshot.sheets],
        "sampleRows": [sheet.sample_rows[:3] for sheet in snapshot.sheets],
    }
    candidate_summary = {
        "templateCode": template_code,
        "sceneCode": scene_code,
        "countryCode": country_code,
        "ruleCandidates": [
            {"code": c.code, "name": c.name, "score": c.score, "reasons": c.reasons}
            for c in rule_candidates.candidates[:5]
        ],
    }
    return (
        "Draft a rule package for the following parsed input and resolved context.\n\n"
        f"Input snapshot:\n{json.dumps(snapshot_summary, ensure_ascii=True, indent=2)}\n\n"
        f"Resolved context:\n{json.dumps(candidate_summary, ensure_ascii=True, indent=2)}\n\n"
        "Rules:\n"
        "1. If source fields are ambiguous, put them in ambiguousMappings.\n"
        "2. If required target fields cannot be mapped, list them in missingFields.\n"
        "3. If any missing input prevents safe execution, add blockingIssues.\n"
        "4. Do not fabricate guaranteed-success mappings.\n"
        "5. rationale must briefly explain why the draft is safe or why confirmation is needed.\n"
    )
