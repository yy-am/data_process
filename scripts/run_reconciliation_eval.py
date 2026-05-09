from __future__ import annotations

import argparse
import json
import os
import re
import socket
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib import error, request


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES_FILE = PROJECT_ROOT / "scripts" / "reconciliation_eval_cases.json"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "reports"

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
    authorization_header: str | None
    timeout_seconds: int
    include_response_format: bool = True


@dataclass(frozen=True)
class EvalCase:
    id: str
    task_type: str
    title: str
    input_text: str
    expected: dict[str, Any]


def load_cases(path: Path) -> list[EvalCase]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        EvalCase(
            id=item["id"],
            task_type=item["taskType"],
            title=item["title"],
            input_text=item["input"],
            expected=item["expected"],
        )
        for item in raw
    ]


def load_model_configs(config_file: Path) -> list[ModelConfig]:
    raw = json.loads(config_file.read_text(encoding="utf-8"))
    configs: list[ModelConfig] = []
    for item in raw:
        api_key = item.get("apiKey")
        api_key_env = item.get("apiKeyEnv")
        if not api_key and api_key_env:
            api_key = os.getenv(api_key_env)
        authorization_header = item.get("authorizationHeader")
        authorization_header_env = item.get("authorizationHeaderEnv")
        if not authorization_header and authorization_header_env:
            authorization_header = os.getenv(authorization_header_env)
        if not api_key and not authorization_header:
            raise RuntimeError(
                f"Model {item.get('label') or item.get('modelName')} missing apiKey/apiKeyEnv or authorizationHeader/authorizationHeaderEnv."
            )
        configs.append(
            ModelConfig(
                label=item.get("label") or item["modelName"],
                provider=item.get("provider", "openai_compatible_chat"),
                endpoint_url=item["endpointUrl"],
                model_name=item["modelName"],
                api_key=api_key or "",
                authorization_header=authorization_header,
                timeout_seconds=int(item.get("timeoutSeconds", 90)),
                include_response_format=bool(item.get("includeResponseFormat", True)),
            )
        )
    return configs


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


def call_openai_compatible_chat(config: ModelConfig, system_prompt: str, user_prompt: str) -> dict[str, Any]:
    headers = {
        "Content-Type": "application/json",
    }
    if config.authorization_header:
        headers["Authorization"] = config.authorization_header
    elif config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"
    payload = {
        "model": config.model_name,
        "temperature": 0,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    if config.include_response_format:
        payload["response_format"] = {"type": "json_object"}
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
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
    return json.loads(payload)


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


def extract_json_payload(text: str) -> dict[str, Any]:
    normalized = text.strip()
    if normalized.startswith("```"):
        normalized = normalized.strip("`")
        if normalized.startswith("json"):
            normalized = normalized[4:].strip()
    normalized = re.sub(r"<think>.*?</think>", "", normalized, flags=re.DOTALL | re.IGNORECASE).strip()

    decoder = json.JSONDecoder()
    for index, ch in enumerate(normalized):
        if ch not in "{[":
            continue
        try:
            payload, _ = decoder.raw_decode(normalized[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    raise json.JSONDecodeError("No JSON object found in text.", normalized, 0)


def parse_json_text(text: str) -> dict[str, Any]:
    return extract_json_payload(text)


def build_job_creation_prompts(case: EvalCase) -> tuple[str, str]:
    system_prompt = (
        "你是对账作业配置助手。"
        "你的任务是把用户的自然语言需求抽取成结构化 JSON。"
        "如果信息不足、存在冲突、或用户明确表示不要创建任务，必须如实表达。"
        "不要编造系统、匹配键、调度或容差。"
        "只能输出 JSON。"
    )
    user_prompt = (
        "请根据下面的自然语言需求输出 JSON。\n"
        "字段要求：\n"
        f"{json.dumps(JOB_CREATION_SCHEMA_HINT, ensure_ascii=False, indent=2)}\n"
        "规范：\n"
        "- systems、matchKeys、compareMetrics、schedule、tolerances、filters 都输出数组\n"
        "- schedule 可选：intraday, daily, weekly, monthly, adhoc\n"
        "- systems 建议用短码，例如 erp, bank, ecommerce, payment_gateway, wms, customs, tax_portal, settlement_platform, general_ledger, pos\n"
        "- compareMetrics 建议用短码，例如 amount, status, tax, fee, quantity, currency, order_count, invoice_count\n"
        "- 如果用户只是咨询而非创建任务，intent 输出 consultation_only\n"
        "- 如果关键信息缺失，needClarification 必须为 true\n"
        f"\n用例ID: {case.id}\n标题: {case.title}\n用户输入: {case.input_text}\n"
    )
    return system_prompt, user_prompt


def build_diff_analysis_prompts(case: EvalCase) -> tuple[str, str]:
    sop_payload = case.expected.get("sop", {})
    system_prompt = (
        "你是对账差异分析助手。"
        "你的任务是根据给定的对账异常描述和预置 SOP，输出结构化归因 JSON。"
        "你必须优先识别最匹配的 SOP，并说明哪些检查规则被触发。"
        "不要超出证据瞎猜；证据不足时应返回 unknown_insufficient_evidence 并提示人工复核。"
        "只能输出 JSON。"
    )
    user_prompt = (
        "请根据下面的异常描述输出 JSON。\n"
        "字段要求：\n"
        f"{json.dumps(DIFF_ANALYSIS_SCHEMA_HINT, ensure_ascii=False, indent=2)}\n"
        "规范：\n"
        "- primaryCauses 只使用给定标签\n"
        "- matchedSops 输出命中的 SOP 编码数组\n"
        "- triggeredChecks 输出你认为被证据触发的检查项\n"
        "- recommendedActions 输出具体动作短句\n"
        "- 如果证据不够，needHumanReview 应为 true\n"
        f"\n用例ID: {case.id}\n标题: {case.title}\n异常描述: {case.input_text}\n"
        f"\n预置 SOP:\n{json.dumps(sop_payload, ensure_ascii=False, indent=2)}\n"
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
    if expected_systems:
        score += round(20 * len(expected_systems & actual_systems) / len(expected_systems))
    else:
        score += 20 if not actual_systems else 0

    expected_keys = normalize_list(expected.get("matchKeys"))
    actual_keys = normalize_list(actual.get("matchKeys"))
    details["matchKeys"] = sorted(actual_keys)
    if expected_keys:
        score += round(15 * len(expected_keys & actual_keys) / len(expected_keys))
    else:
        score += 15 if not actual_keys else 0

    expected_metrics = normalize_list(expected.get("compareMetrics"))
    actual_metrics = normalize_list(actual.get("compareMetrics"))
    details["compareMetrics"] = sorted(actual_metrics)
    if expected_metrics:
        score += round(10 * len(expected_metrics & actual_metrics) / len(expected_metrics))
    else:
        score += 10 if not actual_metrics else 0

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
    if structural_total:
        score += round(5 * structural_hits / structural_total)
    else:
        score += 5

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


def evaluate_case(config: ModelConfig, case: EvalCase) -> dict[str, Any]:
    if case.task_type == "job_creation_from_scene":
        system_prompt, user_prompt = build_job_creation_prompts(case)
    elif case.task_type == "diff_analysis_from_result_and_sop":
        system_prompt, user_prompt = build_diff_analysis_prompts(case)
    else:
        raise RuntimeError(f"Unsupported task type {case.task_type}")

    raw_payload = call_openai_compatible_chat(config, system_prompt, user_prompt)
    raw_text = extract_text(raw_payload)
    parsed = parse_json_text(raw_text)

    if case.task_type == "job_creation_from_scene":
        score, score_details = score_job_creation(case.expected, parsed)
    else:
        score, score_details = score_diff_analysis(case.expected, parsed)

    return {
        "caseId": case.id,
        "taskType": case.task_type,
        "title": case.title,
        "score": score,
        "expected": case.expected,
        "actual": parsed,
        "scoreDetails": score_details,
        "rawText": raw_text,
    }


def summarize_results(label: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    avg_score = round(sum(item["score"] for item in results) / total, 2) if total else 0
    by_task: dict[str, list[int]] = {}
    for item in results:
        by_task.setdefault(item["taskType"], []).append(item["score"])
    task_summary = {
        task_type: round(sum(scores) / len(scores), 2)
        for task_type, scores in by_task.items()
    }
    return {
        "model": label,
        "caseCount": total,
        "avgScore": avg_score,
        "avgByTaskType": task_summary,
    }


def write_markdown_report(path: Path, run_started_at: str, summaries: list[dict[str, Any]], details: dict[str, Any]) -> None:
    lines = [
        "# 对账大模型评测报告",
        "",
        f"- 生成时间：{run_started_at}",
        f"- 模型数：{len(summaries)}",
        "",
        "## 汇总",
        "",
        "| 模型 | 用例数 | 总均分 | 建作业均分 | 差异分析均分 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for summary in summaries:
        job_score = summary["avgByTaskType"].get("job_creation_from_scene", "-")
        diff_score = summary["avgByTaskType"].get("diff_analysis_from_result_and_sop", "-")
        lines.append(
            f"| {summary['model']} | {summary['caseCount']} | {summary['avgScore']} | {job_score} | {diff_score} |"
        )

    lines.extend(["", "## 逐模型明细", ""])
    for summary in summaries:
        model = summary["model"]
        lines.append(f"### {model}")
        lines.append("")
        lines.append("| 用例 | 类型 | 分数 | 标题 |")
        lines.append("| --- | --- | ---: | --- |")
        for item in details[model]["results"]:
            lines.append(f"| {item['caseId']} | {item['taskType']} | {item['score']} | {item['title']} |")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run reconciliation LLM evaluation.")
    parser.add_argument("--config-file", required=True, help="Path to model config JSON file.")
    parser.add_argument("--cases-file", default=str(DEFAULT_CASES_FILE), help="Path to evaluation cases JSON file.")
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR), help="Directory for report outputs.")
    args = parser.parse_args()

    cases = load_cases(Path(args.cases_file))
    model_configs = load_model_configs(Path(args.config_file))
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    run_started_at = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    run_details: dict[str, Any] = {}
    summaries: list[dict[str, Any]] = []

    for config in model_configs:
        model_results: list[dict[str, Any]] = []
        for case in cases:
            try:
                result = evaluate_case(config, case)
            except Exception as exc:  # noqa: BLE001
                result = {
                    "caseId": case.id,
                    "taskType": case.task_type,
                    "title": case.title,
                    "score": 0,
                    "expected": case.expected,
                    "actual": None,
                    "scoreDetails": {"error": str(exc)},
                    "rawText": None,
                }
            model_results.append(result)

        run_details[config.label] = {
            "config": {
                "label": config.label,
                "provider": config.provider,
                "endpointUrl": config.endpoint_url,
                "modelName": config.model_name,
                "timeoutSeconds": config.timeout_seconds,
            },
            "results": model_results,
        }
        summaries.append(summarize_results(config.label, model_results))

    json_report = report_dir / f"reconciliation_eval_report_{run_started_at}.json"
    md_report = report_dir / f"reconciliation_eval_report_{run_started_at}.md"
    json_report.write_text(
        json.dumps(
            {
                "generatedAt": run_started_at,
                "summaries": summaries,
                "details": run_details,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    write_markdown_report(md_report, run_started_at, summaries, run_details)

    print(f"JSON report: {json_report}")
    print(f"Markdown report: {md_report}")


if __name__ == "__main__":
    main()

