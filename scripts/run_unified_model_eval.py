from __future__ import annotations

import argparse
import json
import mimetypes
import os
import socket
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib import error, request


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_ROOT / "reports"
EXCEL_INPUT_DIR = PROJECT_ROOT / "sample_excels" / "input_files"

JOB_CREATION_SCHEMA_HINT = {
    "intent": "create_reconciliation_job_from_existing_scene | consultation_only | unknown",
    "needClarification": True,
    "systems": ["erp", "bank"],
    "matchKeys": ["transaction_id"],
    "compareMetrics": ["amount", "status"],
    "schedule": ["daily"],
    "tolerances": ["amount", "date"],
    "filters": ["optional_filter_code"],
    "summary": "short explanation in Chinese",
}

DIFF_ANALYSIS_SCHEMA_HINT = {
    "matchedSops": ["payment_missing_order | bank_duplicate | fx_rounding | tax_rule_gap"],
    "triggeredChecks": [
        {
            "checkCode": "CHECK_SAMPLE",
            "hit": True,
            "reason": "short explanation in Chinese",
        }
    ],
    "primaryCauses": [
        "missing_source_data | late_arrival | duplicate_records | key_mismatch | amount_rounding | exchange_rate_mismatch | tax_rule_mismatch | status_timing_gap | manual_adjustment | mapping_error | scope_filter_mismatch | refund_reversal_offset | cross_period_cutoff | upstream_bug | unknown_insufficient_evidence"
    ],
    "needHumanReview": True,
    "evidence": ["short evidence in Chinese"],
    "recommendedActions": ["short action in Chinese"],
    "summary": "short explanation in Chinese",
}


@dataclass(frozen=True)
class ModelConfig:
    label: str
    provider: str
    endpoint_url: str
    model_name: str
    api_key: str
    timeout_seconds: int
    include_response_format: bool = True


@dataclass(frozen=True)
class SuiteConfig:
    suite: str
    display_name: str
    suite_type: str
    cases_file: Path
    enabled: bool


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def call_json(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        timeout: int = 180,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(url=url, method=method, data=data, headers=headers)
        opener = request.build_opener(request.ProxyHandler({}))
        try:
            with opener.open(req, timeout=timeout) as resp:
                parsed = json.loads(resp.read().decode("utf-8"))
                return parsed["data"]
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"{method} {path} failed: {exc.code} {body}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"{method} {path} failed: connection error {exc.reason}") from exc
        except TimeoutError as exc:
            raise RuntimeError(f"{method} {path} failed: request timed out") from exc
        except socket.timeout as exc:
            raise RuntimeError(f"{method} {path} failed: request timed out") from exc

    def upload_excel(self, file_path: Path, input_type: str = "EXCEL", timeout: int = 180) -> dict[str, Any]:
        boundary = f"----CodexBoundary{uuid.uuid4().hex}"
        file_bytes = file_path.read_bytes()
        file_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        parts: list[bytes] = []

        def add_text(name: str, value: str) -> None:
            parts.extend(
                [
                    f"--{boundary}\r\n".encode("utf-8"),
                    f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
                    value.encode("utf-8"),
                    b"\r\n",
                ]
            )

        add_text("inputType", input_type)
        parts.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'.encode("utf-8"),
                f"Content-Type: {file_type}\r\n\r\n".encode("utf-8"),
                file_bytes,
                b"\r\n",
                f"--{boundary}--\r\n".encode("utf-8"),
            ]
        )

        req = request.Request(
            url=f"{self.base_url}/api/v1/tasks/upload",
            method="POST",
            data=b"".join(parts),
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Accept": "application/json",
            },
        )
        opener = request.build_opener(request.ProxyHandler({}))
        try:
            with opener.open(req, timeout=timeout) as resp:
                parsed = json.loads(resp.read().decode("utf-8"))
                return parsed["data"]
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"upload {file_path.name} failed: {exc.code} {body}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"upload {file_path.name} failed: connection error {exc.reason}") from exc
        except TimeoutError as exc:
            raise RuntimeError(f"upload {file_path.name} failed: request timed out") from exc
        except socket.timeout as exc:
            raise RuntimeError(f"upload {file_path.name} failed: request timed out") from exc


def resolve_path(path_like: str, relative_to: Path) -> Path:
    path = Path(path_like)
    if path.is_absolute():
        return path
    return (relative_to / path).resolve()


def load_unified_config(config_path: Path) -> tuple[list[ModelConfig], list[SuiteConfig], str]:
    raw = json.loads(config_path.read_text(encoding="utf-8"))

    models: list[ModelConfig] = []
    for item in raw.get("models", []):
        if not item.get("enabled", True):
            continue
        api_key = item.get("apiKey")
        api_key_env = item.get("apiKeyEnv")
        if not api_key and api_key_env:
            api_key = os.environ.get(api_key_env)
        if not api_key:
            raise RuntimeError(f"Model {item.get('label') or item.get('modelName')} missing apiKey or apiKeyEnv.")
        models.append(
            ModelConfig(
                label=item.get("label") or item["modelName"],
                provider=item.get("provider", "openai_compatible_chat"),
                endpoint_url=item["endpointUrl"],
                model_name=item["modelName"],
                api_key=api_key,
                timeout_seconds=int(item.get("timeoutSeconds", 90)),
                include_response_format=bool(item.get("includeResponseFormat", True)),
            )
        )
    if not models:
        raise RuntimeError("No enabled models found in unified model config.")

    manifest_path = resolve_path(raw["suitesManifest"], PROJECT_ROOT)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    suites: list[SuiteConfig] = []
    for item in manifest:
        if not item.get("enabled", True):
            continue
        suites.append(
            SuiteConfig(
                suite=item["suite"],
                display_name=item.get("displayName") or item["suite"],
                suite_type=item.get("suiteType") or item["suite"],
                cases_file=resolve_path(item["casesFile"], PROJECT_ROOT),
                enabled=bool(item.get("enabled", True)),
            )
        )

    base_url = raw.get("dataProcessing", {}).get("baseUrl", "http://127.0.0.1:8000")
    return models, suites, base_url


def normalize_token(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def normalize_list(values: Any) -> set[str]:
    if not isinstance(values, list):
        return set()
    normalized: set[str] = set()
    for item in values:
        if isinstance(item, str) and item.strip():
            normalized.add(normalize_token(item))
    return normalized


def mask_api_key(api_key: str) -> str:
    if len(api_key) <= 10:
        return "*" * len(api_key)
    return f"{api_key[:6]}***{api_key[-4:]}"


def build_chat_request_payload(
    system_prompt: str,
    user_prompt: str,
    model_name: str,
    include_response_format: bool = True,
) -> dict[str, Any]:
    payload = {
        "model": model_name,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    if include_response_format:
        payload["response_format"] = {"type": "json_object"}
    return payload


def build_chat_request_debug(config: ModelConfig, system_prompt: str, user_prompt: str) -> dict[str, Any]:
    payload = build_chat_request_payload(
        system_prompt,
        user_prompt,
        config.model_name,
        include_response_format=config.include_response_format,
    )
    return {
        "endpointUrl": config.endpoint_url,
        "provider": config.provider,
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {mask_api_key(config.api_key)}",
        },
        "body": payload,
    }


def call_openai_compatible_chat(config: ModelConfig, system_prompt: str, user_prompt: str) -> tuple[dict[str, Any], dict[str, Any]]:
    request_debug = build_chat_request_debug(config, system_prompt, user_prompt)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.api_key}",
    }
    body = json.dumps(request_debug["body"], ensure_ascii=False).encode("utf-8")
    http_request = request.Request(
        url=config.endpoint_url,
        data=body,
        headers=headers,
        method="POST",
    )
    opener = request.build_opener(request.ProxyHandler({}))
    try:
        with opener.open(http_request, timeout=config.timeout_seconds) as response:
            payload = response.read().decode("utf-8")
    except error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"{config.label} HTTP {exc.code}: {error_body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"{config.label} connection error: {exc.reason}") from exc
    except TimeoutError as exc:
        raise RuntimeError(f"{config.label} request timed out") from exc
    except socket.timeout as exc:
        raise RuntimeError(f"{config.label} request timed out") from exc
    return json.loads(payload), request_debug


def extract_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts: list[str] = []
                for item in content:
                    if isinstance(item, dict) and isinstance(item.get("text"), str):
                        parts.append(item["text"])
                if parts:
                    return "\n".join(parts)
    raise RuntimeError("Model response does not contain recognizable text content.")


def parse_json_text(text: str) -> dict[str, Any]:
    normalized = text.strip()
    if normalized.startswith("```"):
        normalized = normalized.strip("`")
        if normalized.startswith("json"):
            normalized = normalized[4:].strip()
    return json.loads(normalized)


def build_job_creation_prompts(case: dict[str, Any]) -> tuple[str, str]:
    system_prompt = (
        "You are an assistant that creates reconciliation jobs from an already-known reconciliation scene. "
        "Return only JSON. Do not invent missing systems, keys, schedule, filters, or tolerances. "
        "If the user is only asking a question, use consultation_only. "
        "If required information is missing, set needClarification=true."
    )
    user_prompt = (
        "Convert the following requirement into JSON.\n"
        f"Schema:\n{json.dumps(JOB_CREATION_SCHEMA_HINT, ensure_ascii=False, indent=2)}\n"
        "Rules:\n"
        "- systems, matchKeys, compareMetrics, schedule, tolerances, filters must be arrays\n"
        "- intent should be create_reconciliation_job_from_existing_scene when the request is to create a job under an existing reconciliation scene\n"
        "- schedule should use intraday, daily, weekly, monthly, or adhoc\n"
        f"\nCase ID: {case['id']}\nTitle: {case['title']}\nUser Input: {case['input']}\n"
    )
    return system_prompt, user_prompt


def build_diff_analysis_prompts(case: dict[str, Any]) -> tuple[str, str]:
    sop_payload = case.get("expected", {}).get("sop", {})
    system_prompt = (
        "You are an assistant that analyzes reconciliation diffs based on system-generated results and pre-defined SOP rules. "
        "Return only JSON. You must identify the best matched SOP and the checks triggered by the evidence. "
        "If evidence is insufficient, use unknown_insufficient_evidence and set needHumanReview=true."
    )
    user_prompt = (
        "Analyze the following reconciliation result summary and return JSON.\n"
        f"Schema:\n{json.dumps(DIFF_ANALYSIS_SCHEMA_HINT, ensure_ascii=False, indent=2)}\n"
        "Rules:\n"
        "- primaryCauses must use only the provided labels\n"
        "- matchedSops must be an array of SOP codes\n"
        "- triggeredChecks must contain the triggered checkCode values with reasons\n"
        f"\nCase ID: {case['id']}\nTitle: {case['title']}\nSystem Result And Diff Description: {case['input']}\n"
        f"\nPredefined SOP:\n{json.dumps(sop_payload, ensure_ascii=False, indent=2)}\n"
    )
    return system_prompt, user_prompt


def score_job_creation(expected: dict[str, Any], actual: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    score = 20
    details: dict[str, Any] = {}

    expected_intent = normalize_token(str(expected.get("intent", "unknown")))
    actual_intent = normalize_token(str(actual.get("intent", "unknown")))
    details["intent"] = actual_intent
    if actual_intent == expected_intent:
        score += 10

    expected_clarify = bool(expected.get("needClarification"))
    actual_clarify = bool(actual.get("needClarification"))
    details["needClarification"] = actual_clarify
    if actual_clarify == expected_clarify:
        score += 20

    expected_systems = normalize_list(expected.get("systems"))
    actual_systems = normalize_list(actual.get("systems"))
    details["systems"] = sorted(actual_systems)
    score += round(20 * len(expected_systems & actual_systems) / len(expected_systems)) if expected_systems else 20

    expected_keys = normalize_list(expected.get("matchKeys"))
    actual_keys = normalize_list(actual.get("matchKeys"))
    details["matchKeys"] = sorted(actual_keys)
    score += round(15 * len(expected_keys & actual_keys) / len(expected_keys)) if expected_keys else 15

    expected_metrics = normalize_list(expected.get("compareMetrics"))
    actual_metrics = normalize_list(actual.get("compareMetrics"))
    details["compareMetrics"] = sorted(actual_metrics)
    score += round(10 * len(expected_metrics & actual_metrics) / len(expected_metrics)) if expected_metrics else 10

    expected_schedule = normalize_list(expected.get("schedule"))
    actual_schedule = normalize_list(actual.get("schedule"))
    expected_tolerances = normalize_list(expected.get("tolerances"))
    actual_tolerances = normalize_list(actual.get("tolerances"))
    expected_filters = normalize_list(expected.get("filters"))
    actual_filters = normalize_list(actual.get("filters"))
    structural_hits = 0
    structural_total = 0
    for left, right in (
        (expected_schedule, actual_schedule),
        (expected_tolerances, actual_tolerances),
        (expected_filters, actual_filters),
    ):
        if left:
            structural_total += len(left)
            structural_hits += len(left & right)
    score += round(5 * structural_hits / structural_total) if structural_total else 5

    return min(score, 100), details


def score_diff_analysis(expected: dict[str, Any], actual: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    score = 20
    details: dict[str, Any] = {}

    expected_sop_code = normalize_token(str(expected.get("sop", {}).get("sopCode", "")))
    actual_sops = normalize_list(actual.get("matchedSops"))
    details["matchedSops"] = sorted(actual_sops)
    if expected_sop_code:
        score += 10 if expected_sop_code in actual_sops else 0

    expected_check_codes = normalize_list(expected.get("sop", {}).get("mustHitChecks"))
    actual_check_codes = set()
    raw_checks = actual.get("triggeredChecks")
    if isinstance(raw_checks, list):
        for item in raw_checks:
            if isinstance(item, dict) and isinstance(item.get("checkCode"), str):
                actual_check_codes.add(normalize_token(item["checkCode"]))
    details["triggeredChecks"] = sorted(actual_check_codes)
    if expected_check_codes:
        score += round(10 * len(expected_check_codes & actual_check_codes) / len(expected_check_codes))

    expected_causes = normalize_list(expected.get("primaryCauses"))
    actual_causes = normalize_list(actual.get("primaryCauses"))
    details["primaryCauses"] = sorted(actual_causes)
    if expected_causes:
        score += round(30 * len(expected_causes & actual_causes) / len(expected_causes))

    expected_review = bool(expected.get("needHumanReview"))
    actual_review = bool(actual.get("needHumanReview"))
    details["needHumanReview"] = actual_review
    if expected_review == actual_review:
        score += 10

    evidence_blob = json.dumps(actual.get("evidence", []), ensure_ascii=False)
    evidence_keywords = expected.get("evidenceKeywords", [])
    evidence_hits = sum(1 for keyword in evidence_keywords if keyword in evidence_blob)
    if evidence_keywords:
        score += round(20 * evidence_hits / len(evidence_keywords))

    action_blob = json.dumps(actual.get("recommendedActions", []), ensure_ascii=False)
    action_keywords = expected.get("actionKeywords", [])
    action_hits = sum(1 for keyword in action_keywords if keyword in action_blob)
    if action_keywords:
        score += round(10 * action_hits / len(action_keywords))

    return min(score, 100), details


def evaluate_data_processing_case(client: ApiClient, config: ModelConfig, case: dict[str, Any]) -> dict[str, Any]:
    file_path = EXCEL_INPUT_DIR / case["fileName"]
    upload_result = client.upload_excel(file_path)
    task_id = upload_result["task"]["taskId"]

    snapshot = client.call_json("GET", f"/api/v1/tasks/{task_id}/input-snapshot")
    template_candidates = client.call_json("GET", f"/api/v1/tasks/{task_id}/template-candidates")
    identify = client.call_json(
        "POST",
        f"/api/v1/agents/template-identification/tasks/{task_id}",
        timeout=max(config.timeout_seconds + 15, 30),
    )
    task_summary = client.call_json("GET", f"/api/v1/tasks/{task_id}")

    actual_template = identify.get("templateCode")
    actual_scene = identify.get("sceneCode")
    actual_country = identify.get("countryCode")
    need_confirm = bool(identify.get("needUserConfirm"))

    if case.get("expectedTemplate") is None:
        passed = actual_template is None and need_confirm
        reason = "歧义样例保持未解析并要求人工确认，结果符合预期。" if passed else "预期应保持未解析并要求人工确认，但实际结果不符合预期。"
    else:
        passed = (
            actual_template == case.get("expectedTemplate")
            and actual_scene == case.get("expectedScene")
            and actual_country == case.get("expectedCountry")
        )
        reason = "模板、场景和国家均与预期一致。" if passed else "识别出的模板、场景或国家与预期不一致。"

    first_sheet = (snapshot.get("sheets") or [{}])[0]
    return {
        "caseId": case["id"],
        "suite": "data_processing_template_identification",
        "taskType": "data_processing_template_identification",
        "title": case["title"],
        "score": 100 if passed else 0,
        "outcome": "passed" if passed else "failed",
        "expected": {
            "templateCode": case.get("expectedTemplate"),
            "sceneCode": case.get("expectedScene"),
            "countryCode": case.get("expectedCountry"),
        },
        "actual": identify,
        "scoreDetails": {
            "taskId": task_id,
            "taskStatus": task_summary.get("status"),
            "sheetName": first_sheet.get("sheetName", "-"),
            "headerCount": len(first_sheet.get("headers", [])),
            "needUserConfirm": need_confirm,
            "reason": reason,
            "templateCandidates": template_candidates,
        },
        "rawText": None,
    }


def evaluate_prompt_case(config: ModelConfig, suite_type: str, case: dict[str, Any]) -> dict[str, Any]:
    if suite_type == "job_creation_from_scene":
        system_prompt, user_prompt = build_job_creation_prompts(case)
    elif suite_type == "diff_analysis_from_result_and_sop":
        system_prompt, user_prompt = build_diff_analysis_prompts(case)
    else:
        raise RuntimeError(f"Unsupported prompt suite type {suite_type}")

    raw_payload, request_debug = call_openai_compatible_chat(config, system_prompt, user_prompt)
    raw_text = extract_text(raw_payload)
    parsed = parse_json_text(raw_text)

    if suite_type == "job_creation_from_scene":
        score, score_details = score_job_creation(case["expected"], parsed)
    else:
        score, score_details = score_diff_analysis(case["expected"], parsed)

    return {
        "caseId": case["id"],
        "suite": suite_type,
        "taskType": suite_type,
        "title": case["title"],
        "score": score,
        "outcome": "passed" if score >= 80 else "needs_review",
        "expected": case["expected"],
        "actual": parsed,
        "scoreDetails": {
            **score_details,
            "requestDebug": request_debug,
        },
        "rawText": raw_text,
    }


def build_prompt_request_debug(config: ModelConfig, suite_type: str, case: dict[str, Any]) -> dict[str, Any] | None:
    if suite_type == "job_creation_from_scene":
        system_prompt, user_prompt = build_job_creation_prompts(case)
    elif suite_type == "diff_analysis_from_result_and_sop":
        system_prompt, user_prompt = build_diff_analysis_prompts(case)
    else:
        return None
    return build_chat_request_debug(config, system_prompt, user_prompt)


def configure_template_model(client: ApiClient, config: ModelConfig) -> None:
    payload = {
        "provider": config.provider,
        "model": config.model_name,
        "endpointUrl": config.endpoint_url,
        "apiKey": config.api_key,
        "timeoutSeconds": config.timeout_seconds,
        "includeResponseFormat": config.include_response_format,
    }
    client.call_json(
        "POST",
        "/api/v1/agents/template-identification/config",
        payload=payload,
        timeout=max(config.timeout_seconds + 15, 30),
    )


def summarize_suite(results: list[dict[str, Any]]) -> dict[str, Any]:
    case_count = len(results)
    avg_score = round(sum(item["score"] for item in results) / case_count, 2) if case_count else 0
    passed = sum(1 for item in results if item["outcome"] == "passed")
    return {
        "caseCount": case_count,
        "averageScore": avg_score,
        "passedCases": passed,
        "passRate": round(passed / case_count, 4) if case_count else 0,
    }


def summarize_model(model: ModelConfig, suite_results: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    all_results = [item for results in suite_results.values() for item in results]
    overall = summarize_suite(all_results)
    by_suite = {suite: summarize_suite(results) for suite, results in suite_results.items()}
    return {
        "model": model.label,
        "provider": model.provider,
        "modelName": model.model_name,
        "endpointUrl": model.endpoint_url,
        "timeoutSeconds": model.timeout_seconds,
        "includeResponseFormat": model.include_response_format,
        "overall": overall,
        "bySuite": by_suite,
    }


def format_outcome_label(outcome: str) -> str:
    mapping = {
        "passed": "通过",
        "needs_review": "待复核",
        "failed": "失败",
    }
    return mapping.get(outcome, outcome)


def format_case_cell(result: dict[str, Any] | None) -> str:
    if result is None:
        return "-"
    return f"{result['score']}（{format_outcome_label(result['outcome'])}）"


def write_markdown_report(
    path: Path,
    generated_at: str,
    model_summaries: list[dict[str, Any]],
    suite_configs: list[SuiteConfig],
    suite_cases: dict[str, list[dict[str, Any]]],
    model_results: dict[str, dict[str, list[dict[str, Any]]]],
) -> None:
    suite_title_map = {
        "data_processing_template_identification": "数据加工模板识别",
        "job_creation_from_scene": "根据已有对账场景建作业",
        "diff_analysis_from_result_and_sop": "根据系统结果 + SOP 分析差异",
    }
    lines = [
        "# 统一大模型评测报告",
        "",
        f"- 生成时间：{generated_at}",
        f"- 参评模型数：{len(model_summaries)}",
        f"- 用例类型数：{len(suite_configs)}",
        "",
        "## 模型总览",
        "",
        "| 模型 | 总体均分 | 总体通过率 | 数据加工模板识别 | 根据已有对账场景建作业 | 根据系统结果 + SOP 分析差异 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for summary in model_summaries:
        by_suite = summary["bySuite"]
        lines.append(
            "| {model} | {overall_avg} | {overall_pass} | {dp} | {job} | {diff} |".format(
                model=summary["model"],
                overall_avg=summary["overall"]["averageScore"],
                overall_pass=summary["overall"]["passRate"],
                dp=by_suite.get("data_processing_template_identification", {}).get("averageScore", "-"),
                job=by_suite.get("job_creation_from_scene", {}).get("averageScore", "-"),
                diff=by_suite.get("diff_analysis_from_result_and_sop", {}).get("averageScore", "-"),
            )
        )

    for suite in suite_configs:
        suite_title = suite_title_map.get(suite.suite, suite.display_name)
        lines.extend(["", f"## {suite_title}", ""])
        lines.append("| 用例ID | 标题 | " + " | ".join(summary["model"] for summary in model_summaries) + " |")
        lines.append("| --- | --- | " + " | ".join("---" for _ in model_summaries) + " |")

        case_index = {item["id"]: item for item in suite_cases[suite.suite]}
        for case_id, case in case_index.items():
            cells = [case_id, case["title"]]
            for summary in model_summaries:
                model_name = summary["model"]
                result_lookup = {item["caseId"]: item for item in model_results[model_name][suite.suite]}
                cells.append(format_case_cell(result_lookup.get(case_id)))
            lines.append("| " + " | ".join(cells) + " |")

        lines.extend(["", f"### {suite_title} 明细说明", ""])
        for summary in model_summaries:
            model_name = summary["model"]
            lines.append(f"#### {model_name}")
            lines.append("")
            lines.append("| 用例ID | 分数 | 结果 | 说明 |")
            lines.append("| --- | ---: | --- | --- |")
            for item in model_results[model_name][suite.suite]:
                note = item["scoreDetails"].get("reason") or item["scoreDetails"].get("error") or "-"
                lines.append(
                    f"| {item['caseId']} | {item['score']} | {format_outcome_label(item['outcome'])} | {str(note).replace('|', '/')} |"
                )
                request_debug = item["scoreDetails"].get("requestDebug")
                if request_debug:
                    request_debug_text = json.dumps(request_debug, ensure_ascii=False, indent=2)
                    lines.append("")
                    lines.append(f"请求入参：`{item['caseId']}`")
                    lines.append("```json")
                    lines.append(request_debug_text)
                    lines.append("```")
                lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run unified model evaluation across three suites.")
    parser.add_argument(
        "--config-file",
        default=str(PROJECT_ROOT / "scripts" / "unified_model_eval_config.json"),
        help="Path to unified model evaluation config JSON file.",
    )
    parser.add_argument(
        "--report-dir",
        default=str(REPORT_DIR),
        help="Directory for report outputs.",
    )
    args = parser.parse_args()

    config_path = Path(args.config_file)
    models, suites, base_url = load_unified_config(config_path)
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    suite_cases: dict[str, list[dict[str, Any]]] = {}
    for suite in suites:
        suite_cases[suite.suite] = json.loads(suite.cases_file.read_text(encoding="utf-8"))

    generated_at = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    model_summaries: list[dict[str, Any]] = []
    model_results: dict[str, dict[str, list[dict[str, Any]]]] = {}

    for model in models:
        per_suite_results: dict[str, list[dict[str, Any]]] = {}
        client = ApiClient(base_url)

        for suite in suites:
            results: list[dict[str, Any]] = []
            cases = suite_cases[suite.suite]

            if suite.suite_type == "data_processing_template_identification":
                try:
                    configure_template_model(client, model)
                except Exception as exc:  # noqa: BLE001
                    for case in cases:
                        results.append(
                            {
                                "caseId": case["id"],
                                "suite": suite.suite,
                                "taskType": suite.suite_type,
                                "title": case["title"],
                                "score": 0,
                                "outcome": "failed",
                                "expected": case,
                                "actual": None,
                                "scoreDetails": {"error": str(exc)},
                                "rawText": None,
                            }
                        )
                    per_suite_results[suite.suite] = results
                    continue

            for case in cases:
                try:
                    if suite.suite_type == "data_processing_template_identification":
                        result = evaluate_data_processing_case(client, model, case)
                    else:
                        result = evaluate_prompt_case(model, suite.suite_type, case)
                except Exception as exc:  # noqa: BLE001
                    request_debug = None
                    if suite.suite_type != "data_processing_template_identification":
                        request_debug = build_prompt_request_debug(model, suite.suite_type, case)
                    result = {
                        "caseId": case["id"],
                        "suite": suite.suite,
                        "taskType": suite.suite_type,
                        "title": case["title"],
                        "score": 0,
                        "outcome": "failed",
                        "expected": case.get("expected", case),
                        "actual": None,
                        "scoreDetails": {
                            "error": str(exc),
                            **({"requestDebug": request_debug} if request_debug else {}),
                        },
                        "rawText": None,
                    }
                results.append(result)

            per_suite_results[suite.suite] = results

        model_results[model.label] = per_suite_results
        model_summaries.append(summarize_model(model, per_suite_results))

    json_report_path = report_dir / f"unified_model_eval_report_{generated_at}.json"
    md_report_path = report_dir / f"unified_model_eval_report_{generated_at}.md"
    json_report_path.write_text(
        json.dumps(
            {
                "generatedAt": generated_at,
                "configFile": str(config_path),
                "baseUrl": base_url,
                "summaries": model_summaries,
                "suites": [
                    {
                        "suite": suite.suite,
                        "displayName": suite.display_name,
                        "casesFile": str(suite.cases_file),
                        "caseCount": len(suite_cases[suite.suite]),
                    }
                    for suite in suites
                ],
                "results": model_results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    write_markdown_report(md_report_path, generated_at, model_summaries, suites, suite_cases, model_results)

    print(f"JSON report: {json_report_path}")
    print(f"Markdown report: {md_report_path}")


if __name__ == "__main__":
    main()
