from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UNIFIED_RUNNER_PATH = PROJECT_ROOT / "scripts" / "run_unified_model_eval.py"
DEFAULT_SAFE_CONFIG = PROJECT_ROOT / "scripts" / "unified_eval" / "unified_model_eval_config.json"
DEFAULT_LOCAL_CONFIG = PROJECT_ROOT / "scripts" / "unified_eval" / "unified_model_eval_config.local.json"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "scripts" / "unified_eval" / "reports"

DEFAULT_CASE_IDS = {
    "data_processing_template_identification": "DP001",
    "job_creation_from_scene": "JC001",
    "diff_analysis_from_result_and_sop": "DA001",
}


def load_runner_module():
    spec = importlib.util.spec_from_file_location("unified_eval_runner", UNIFIED_RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load unified runner from {UNIFIED_RUNNER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def resolve_default_config() -> Path:
    if DEFAULT_LOCAL_CONFIG.exists():
        return DEFAULT_LOCAL_CONFIG
    return DEFAULT_SAFE_CONFIG


def pick_cases_by_id(cases: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup = {item["id"]: item for item in cases}
    selected: dict[str, dict[str, Any]] = {}
    for suite_type, case_id in DEFAULT_CASE_IDS.items():
        case = lookup.get(case_id)
        if case is None:
            raise RuntimeError(f"Default case {case_id} not found for suite {suite_type}.")
        selected[suite_type] = case
    return selected


def write_smoke_markdown_report(
    path: Path,
    generated_at: str,
    config_path: Path,
    results: list[dict[str, Any]],
) -> None:
    lines = [
        "# 轻量级三用例评测报告",
        "",
        f"- 生成时间：{generated_at}",
        f"- 配置文件：{config_path}",
        f"- 用例数量：{len(results)}",
        "",
        "| 用例ID | 类型 | 标题 | 分数 | 结果 |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for item in results:
        outcome = item.get("outcome", "-")
        title = str(item.get("title", "-")).replace("|", "/")
        lines.append(f"| {item['caseId']} | {item['taskType']} | {title} | {item['score']} | {outcome} |")

    lines.extend(["", "## 明细", ""])
    for item in results:
        note = item.get("scoreDetails", {}).get("reason") or item.get("scoreDetails", {}).get("error") or "-"
        lines.append(f"### {item['caseId']} {item['title']}")
        lines.append("")
        lines.append(f"- 类型：`{item['taskType']}`")
        lines.append(f"- 分数：`{item['score']}`")
        lines.append(f"- 结果：`{item.get('outcome', '-')}`")
        lines.append(f"- 说明：{note}")
        request_debug = item.get("scoreDetails", {}).get("requestDebug")
        if request_debug:
            lines.append("")
            lines.append("请求入参：")
            lines.append("```json")
            lines.append(json.dumps(request_debug, ensure_ascii=False, indent=2))
            lines.append("```")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a serial smoke evaluation with 3 cases only.")
    parser.add_argument(
        "--config-file",
        default=str(resolve_default_config()),
        help="Path to unified eval config file. Defaults to local config when present.",
    )
    parser.add_argument(
        "--report-dir",
        default=str(DEFAULT_REPORT_DIR),
        help="Directory for smoke report outputs.",
    )
    args = parser.parse_args()

    runner = load_runner_module()
    config_path = Path(args.config_file)
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    models, suites, base_url = runner.load_unified_config(config_path)
    if len(models) != 1:
        raise RuntimeError("Smoke script expects exactly one enabled model in the config.")
    model = models[0]
    client = runner.ApiClient(base_url)

    suite_cases: dict[str, list[dict[str, Any]]] = {}
    for suite in suites:
        suite_cases[suite.suite] = json.loads(suite.cases_file.read_text(encoding="utf-8"))

    selected_cases = pick_cases_by_id([item for values in suite_cases.values() for item in values])

    results: list[dict[str, Any]] = []
    for suite in suites:
        case = selected_cases.get(suite.suite_type)
        if case is None:
            continue

        if suite.suite_type == "data_processing_template_identification":
            runner.configure_template_model(client, model)
            result = runner.evaluate_data_processing_case(client, model, case)
        else:
            result = runner.evaluate_prompt_case(model, suite.suite_type, case)
        results.append(result)

    generated_at = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    json_report_path = report_dir / f"unified_model_eval_smoke_report_{generated_at}.json"
    md_report_path = report_dir / f"unified_model_eval_smoke_report_{generated_at}.md"

    json_report_path.write_text(
        json.dumps(
            {
                "generatedAt": generated_at,
                "configFile": str(config_path),
                "model": model.label,
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    write_smoke_markdown_report(md_report_path, generated_at, config_path, results)

    print(f"JSON report: {json_report_path}")
    print(f"Markdown report: {md_report_path}")


if __name__ == "__main__":
    main()
