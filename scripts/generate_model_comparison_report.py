from __future__ import annotations

import argparse
import json
import mimetypes
import os
import socket
import uuid
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib import error, request
from xml.sax.saxutils import escape


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = PROJECT_ROOT / "sample_excels" / "input_files"
OUTPUT_DIR = PROJECT_ROOT / "reports"
DEFAULT_BASE_URL = "http://127.0.0.1:8000"


@dataclass(frozen=True)
class CaseSpec:
    file_name: str
    case_type: str
    expected_template: str | None
    expected_scene: str | None
    expected_country: str | None
    description: str


@dataclass(frozen=True)
class ModelConfig:
    label: str
    provider: str
    endpoint_url: str
    model_name: str
    api_key: str
    timeout_seconds: int


CASES: list[CaseSpec] = [
    CaseSpec("input_payment_us_clean.xlsx", "标准命中", "PAYMENT_INVOICE_STANDARD_US", "payment", "us", "标准付款发票样例，列名与知识库模板高度一致。"),
    CaseSpec("input_payment_us_variant_headers.xlsx", "相似列名", "PAYMENT_INVOICE_STANDARD_US", "payment", "us", "付款发票变体表头，测试别名和相似列名识别。"),
    CaseSpec("input_payment_us_similar_headers_v2.xlsx", "相似列名", "PAYMENT_INVOICE_STANDARD_US", "payment", "us", "付款发票第二组相似列名样例。"),
    CaseSpec("input_customs_cn_clean.xlsx", "标准命中", "CUSTOMS_DECLARATION_STANDARD_CN", "customs", "cn", "中国报关单标准列名样例。"),
    CaseSpec("input_customs_cn_similar_headers_v2.xlsx", "相似列名", "CUSTOMS_DECLARATION_STANDARD_CN", "customs", "cn", "中国报关单相似列名样例。"),
    CaseSpec("input_vendor_eu_variant.xlsx", "相似列名", "VENDOR_SETTLEMENT_STANDARD_EU", "settlement", "eu", "欧洲供应商结算变体列名样例。"),
    CaseSpec("input_settlement_eu_similar_headers_v2.xlsx", "相似列名", "VENDOR_SETTLEMENT_STANDARD_EU", "settlement", "eu", "欧洲结算第二组相似列名样例。"),
    CaseSpec("input_fulfillment_jp_22cols_variant.xlsx", "复杂表头", "ORDER_FULFILLMENT_STANDARD_JP", "fulfillment", "jp", "日本履约场景，20+ 列，测试复杂列集合命中。"),
    CaseSpec("input_rebate_mx_similar_headers_v2.xlsx", "复杂映射前置", "REBATE_MX_TEMPLATE", "rebate", "mx", "返利场景相似列名样例。"),
    CaseSpec("input_rebate_mx_unrelated_headers_22cols.xlsx", "复杂映射前置", "CHANNEL_REBATE_STANDARD_MX", "rebate", "mx", "返利场景 20+ 列样例，验证大模型从模板目录中选出更合适模板。"),
    CaseSpec("input_ambiguous_trade_document.xlsx", "歧义样例", None, None, None, "故意构造的歧义单据，预期返回 needUserConfirm。"),
]


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def call_json(self, method: str, path: str, payload: dict[str, Any] | None = None, timeout: int = 180) -> dict[str, Any]:
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


def classify_result(case: CaseSpec, actual: dict[str, Any]) -> tuple[str, str]:
    actual_template = actual.get("templateCode")
    actual_scene = actual.get("sceneCode")
    actual_country = actual.get("countryCode")
    need_confirm = bool(actual.get("needUserConfirm"))

    if case.expected_template is None:
        passed = actual_template is None and need_confirm
        return ("通过" if passed else "未通过", "歧义样例应保持未解析并要求人工确认。")

    passed = (
        actual_template == case.expected_template
        and actual_scene == case.expected_scene
        and actual_country == case.expected_country
    )
    return ("通过" if passed else "未通过", "模板、场景、国家全部命中。" if passed else "实际识别结果与预期不一致。")


def load_model_configs(args: argparse.Namespace) -> list[ModelConfig]:
    if args.config_file:
        raw = json.loads(Path(args.config_file).read_text(encoding="utf-8"))
        if not isinstance(raw, list) or not raw:
            raise RuntimeError("config-file 必须是非空 JSON 数组。")
        configs: list[ModelConfig] = []
        for item in raw:
            api_key = item.get("apiKey")
            api_key_env = item.get("apiKeyEnv")
            if not api_key and api_key_env:
                api_key = os.environ.get(api_key_env)
            if not api_key:
                raise RuntimeError(f"模型 {item.get('label') or item.get('modelName')} 缺少 apiKey 或 apiKeyEnv。")
            configs.append(
                ModelConfig(
                    label=item.get("label") or item["modelName"],
                    provider=item.get("provider", "openai_compatible_chat"),
                    endpoint_url=item["endpointUrl"],
                    model_name=item["modelName"],
                    api_key=api_key,
                    timeout_seconds=int(item.get("timeoutSeconds", 60)),
                )
            )
        return configs

    api_key = args.api_key or (os.environ.get(args.api_key_env) if args.api_key_env else None)
    if not api_key:
        raise RuntimeError("单模型模式下必须提供 --api-key 或 --api-key-env。")
    return [
        ModelConfig(
            label=args.label or args.model_name,
            provider=args.provider,
            endpoint_url=args.endpoint_url,
            model_name=args.model_name,
            api_key=api_key,
            timeout_seconds=args.timeout_seconds,
        )
    ]


def configure_template_model(client: ApiClient, config: ModelConfig) -> None:
    payload = {
        "provider": config.provider,
        "model": config.model_name,
        "endpointUrl": config.endpoint_url,
        "apiKey": config.api_key,
        "timeoutSeconds": config.timeout_seconds,
    }
    client.call_json("POST", "/api/v1/agents/template-identification/config", payload=payload, timeout=max(config.timeout_seconds + 15, 30))


def evaluate_model(client: ApiClient, config: ModelConfig) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    configure_template_model(client, config)
    started_at = datetime.now(UTC)
    results: list[dict[str, Any]] = []

    for index, case in enumerate(CASES, start=1):
        try:
            file_path = INPUT_DIR / case.file_name
            upload_result = client.upload_excel(file_path)
            task_id = upload_result["task"]["taskId"]

            snapshot = client.call_json("GET", f"/api/v1/tasks/{task_id}/input-snapshot")
            template_candidates = client.call_json("GET", f"/api/v1/tasks/{task_id}/template-candidates")
            identify = client.call_json(
                "POST",
                f"/api/v1/agents/template-identification/tasks/{task_id}",
                timeout=max(config.timeout_seconds + 15, 30),
            )

            try:
                rule_candidates = client.call_json("GET", f"/api/v1/tasks/{task_id}/rule-candidates")
                rule_list = rule_candidates.get("candidates", [])
            except Exception as exc:  # noqa: BLE001
                rule_candidates = {"error": str(exc)}
                rule_list = []

            task_summary = client.call_json("GET", f"/api/v1/tasks/{task_id}")
            verdict, verdict_reason = classify_result(case, identify)
            first_sheet = (snapshot.get("sheets") or [{}])[0]

            results.append(
                {
                    "caseIndex": index,
                    "fileName": case.file_name,
                    "caseType": case.case_type,
                    "description": case.description,
                    "expectedTemplate": case.expected_template,
                    "expectedScene": case.expected_scene,
                    "expectedCountry": case.expected_country,
                    "actualTemplate": identify.get("templateCode"),
                    "actualScene": identify.get("sceneCode"),
                    "actualCountry": identify.get("countryCode"),
                    "confidence": identify.get("confidence"),
                    "needUserConfirm": bool(identify.get("needUserConfirm")),
                    "verdict": verdict,
                    "verdictReason": verdict_reason,
                    "taskStatus": task_summary.get("status"),
                    "taskId": task_id,
                    "sheetName": first_sheet.get("sheetName", "-"),
                    "headerCount": len(first_sheet.get("headers", [])),
                    "headerPreview": " | ".join((first_sheet.get("headers") or [])[:15]),
                    "samplePreview": json.dumps((first_sheet.get("sampleRows") or [])[:1], ensure_ascii=False),
                    "ruleCandidateCount": len(rule_list),
                    "topRuleCode": (rule_list[0].get("ruleCode") or rule_list[0].get("code")) if rule_list else None,
                    "templateIdentification": identify,
                    "templateCandidates": template_candidates,
                    "ruleCandidates": rule_candidates,
                }
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                {
                    "caseIndex": index,
                    "fileName": case.file_name,
                    "caseType": case.case_type,
                    "description": case.description,
                    "expectedTemplate": case.expected_template,
                    "expectedScene": case.expected_scene,
                    "expectedCountry": case.expected_country,
                    "actualTemplate": None,
                    "actualScene": None,
                    "actualCountry": None,
                    "confidence": 0,
                    "needUserConfirm": False,
                    "verdict": "未通过",
                    "verdictReason": f"执行失败：{exc}",
                    "taskStatus": "FAILED",
                    "taskId": "-",
                    "sheetName": "-",
                    "headerCount": 0,
                    "headerPreview": "-",
                    "samplePreview": "-",
                    "ruleCandidateCount": 0,
                    "topRuleCode": None,
                    "templateIdentification": {"error": str(exc)},
                    "templateCandidates": {},
                    "ruleCandidates": {},
                }
            )

    passed_count = sum(1 for item in results if item["verdict"] == "通过")
    unresolved_count = sum(1 for item in results if item["needUserConfirm"])
    avg_confidence = round(
        sum(float(item["confidence"] or 0) for item in results) / len(results),
        4,
    )
    ended_at = datetime.now(UTC)

    summary = {
        "label": config.label,
        "provider": config.provider,
        "modelName": config.model_name,
        "endpointUrl": config.endpoint_url,
        "timeoutSeconds": config.timeout_seconds,
        "totalCases": len(results),
        "passedCases": passed_count,
        "passRate": round(passed_count / len(results), 4),
        "averageConfidence": avg_confidence,
        "needUserConfirmCases": unresolved_count,
        "startedAt": started_at.isoformat(),
        "endedAt": ended_at.isoformat(),
    }
    return summary, results


def col_name(index: int) -> str:
    result = ""
    while index > 0:
        index, rem = divmod(index - 1, 26)
        result = chr(65 + rem) + result
    return result


def make_cell(ref: str, value: Any, style: int = 0) -> str:
    if value is None:
        value = ""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{ref}" s="{style}"><v>{value}</v></c>'
    return f'<c r="{ref}" t="inlineStr" s="{style}"><is><t>{escape(str(value))}</t></is></c>'


def sheet_xml(rows: list[list[Any]]) -> str:
    xml_rows: list[str] = []
    for row_idx, row in enumerate(rows, start=1):
        cells = []
        for col_idx, value in enumerate(row, start=1):
            style = 1 if row_idx == 1 else 0
            if row_idx > 1 and value in {"通过", "未通过"}:
                style = 2 if value == "通过" else 3
            if isinstance(value, str) and ("\n" in value or len(value) > 80):
                style = 4 if style == 0 else style
            cells.append(make_cell(f"{col_name(col_idx)}{row_idx}", value, style))
        xml_rows.append(f'<row r="{row_idx}">{"".join(cells)}</row>')

    max_col = max((len(r) for r in rows), default=1)
    dimension = f"A1:{col_name(max_col)}{max(len(rows), 1)}"
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="{dimension}"/>'
        '<sheetViews><sheetView workbookViewId="0"/></sheetViews>'
        '<sheetFormatPr defaultRowHeight="18"/>'
        '<sheetData>'
        f'{"".join(xml_rows)}'
        '</sheetData>'
        '</worksheet>'
    )


def styles_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2">
    <font><sz val="11"/><name val="Microsoft YaHei"/></font>
    <font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Microsoft YaHei"/></font>
  </fonts>
  <fills count="5">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF4B99E6"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFEAF7EE"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFFF0F4"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="1">
    <border><left/><right/><top/><bottom/><diagonal/></border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="5">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>
    <xf numFmtId="0" fontId="0" fillId="3" borderId="0" xfId="0" applyFill="1"/>
    <xf numFmtId="0" fontId="0" fillId="4" borderId="0" xfId="0" applyFill="1"/>
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1">
      <alignment wrapText="1" vertical="top"/>
    </xf>
  </cellXfs>
  <cellStyles count="1">
    <cellStyle name="Normal" xfId="0" builtinId="0"/>
  </cellStyles>
</styleSheet>"""


def safe_sheet_name(name: str) -> str:
    cleaned = name.replace("/", "_").replace("\\", "_").replace(":", "_").replace("*", "_").replace("?", "_")
    cleaned = cleaned.replace("[", "_").replace("]", "_")
    return cleaned[:31] or "Sheet"


def write_workbook(output_path: Path, sheets: list[tuple[str, list[list[Any]]]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        content_types = [
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>""",
            """<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">""",
            """  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>""",
            """  <Default Extension="xml" ContentType="application/xml"/>""",
            """  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>""",
            """  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>""",
            """  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>""",
            """  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>""",
        ]
        for idx in range(1, len(sheets) + 1):
            content_types.append(
                f"""  <Override PartName="/xl/worksheets/sheet{idx}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>"""
            )
        content_types.append("</Types>")
        zf.writestr("[Content_Types].xml", "\n".join(content_types))

        zf.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>""",
        )

        utc_now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        zf.writestr(
            "docProps/core.xml",
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>大模型对比测试报告</dc:title>
  <dc:creator>Codex</dc:creator>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{utc_now}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{utc_now}</dcterms:modified>
</cp:coreProperties>""",
        )
        zf.writestr(
            "docProps/app.xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex</Application>
</Properties>""",
        )

        workbook_sheets: list[str] = []
        workbook_rels: list[str] = []
        for idx, (name, rows) in enumerate(sheets, start=1):
            workbook_sheets.append(f'<sheet name="{escape(safe_sheet_name(name))}" sheetId="{idx}" r:id="rId{idx}"/>')
            workbook_rels.append(
                f'<Relationship Id="rId{idx}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{idx}.xml"/>'
            )
            zf.writestr(f"xl/worksheets/sheet{idx}.xml", sheet_xml(rows))

        zf.writestr(
            "xl/workbook.xml",
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>{''.join(workbook_sheets)}</sheets>
</workbook>""",
        )
        zf.writestr(
            "xl/_rels/workbook.xml.rels",
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  {''.join(workbook_rels)}
  <Relationship Id="rId{len(sheets) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>""",
        )
        zf.writestr("xl/styles.xml", styles_xml())


def build_intro_rows(base_url: str, models: list[ModelConfig], output_path: Path) -> list[list[Any]]:
    rows = [
        ["报告名称", "Excel 模板识别大模型对比测试报告"],
        ["生成时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ["服务地址", base_url],
        ["测试样例目录", str(INPUT_DIR)],
        ["输出文件", str(output_path)],
        ["测试总用例数", len(CASES)],
        ["判定口径", "非歧义样例要求模板、场景、国家全部命中；歧义样例要求 needUserConfirm=true 且不强行输出模板。"],
        ["说明", "本脚本聚焦模型选型，自动切换模型配置并重复跑完整 Excel 样例集。"],
        [],
        ["参与对比模型", ""],
    ]
    for model in models:
        rows.append([model.label, f"{model.provider} | {model.model_name} | timeout={model.timeout_seconds}s"])
    return rows


def build_summary_rows(model_summaries: list[dict[str, Any]]) -> list[list[Any]]:
    rows: list[list[Any]] = [[
        "模型标签",
        "提供方",
        "模型名称",
        "总用例数",
        "通过数",
        "通过率",
        "平均置信度",
        "需人工确认数",
        "开始时间",
        "结束时间",
        "接口地址",
    ]]
    for item in model_summaries:
        rows.append(
            [
                item["label"],
                item["provider"],
                item["modelName"],
                item["totalCases"],
                item["passedCases"],
                item["passRate"],
                item["averageConfidence"],
                item["needUserConfirmCases"],
                item["startedAt"],
                item["endedAt"],
                item["endpointUrl"],
            ]
        )
    return rows


def build_detail_rows(model_results: list[tuple[dict[str, Any], list[dict[str, Any]]]]) -> list[list[Any]]:
    rows: list[list[Any]] = [[
        "模型标签",
        "序号",
        "文件名",
        "测试类型",
        "预期模板",
        "实际模板",
        "预期场景",
        "实际场景",
        "预期国家",
        "实际国家",
        "置信度",
        "需要人工确认",
        "规则候选数",
        "首个规则编码",
        "结果判定",
        "结论说明",
    ]]
    for summary, items in model_results:
        for item in items:
            rows.append(
                [
                    summary["label"],
                    item["caseIndex"],
                    item["fileName"],
                    item["caseType"],
                    item["expectedTemplate"] or "应保持未解析",
                    item["actualTemplate"] or "-",
                    item["expectedScene"] or "-",
                    item["actualScene"] or "-",
                    item["expectedCountry"] or "-",
                    item["actualCountry"] or "-",
                    item["confidence"],
                    "是" if item["needUserConfirm"] else "否",
                    item["ruleCandidateCount"],
                    item["topRuleCode"] or "-",
                    item["verdict"],
                    item["verdictReason"],
                ]
            )
    return rows


def build_raw_rows(model_results: list[tuple[dict[str, Any], list[dict[str, Any]]]]) -> list[list[Any]]:
    rows: list[list[Any]] = [[
        "模型标签",
        "序号",
        "文件名",
        "任务 ID",
        "任务状态",
        "输入快照摘要",
        "模板识别原始结果",
        "模板候选原始结果",
        "规则候选原始结果",
    ]]
    for summary, items in model_results:
        for item in items:
            rows.append(
                [
                    summary["label"],
                    item["caseIndex"],
                    item["fileName"],
                    item["taskId"],
                    item["taskStatus"],
                    json.dumps(
                        {
                            "sheetName": item["sheetName"],
                            "headerCount": item["headerCount"],
                            "headerPreview": item["headerPreview"],
                            "samplePreview": item["samplePreview"],
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    json.dumps(item["templateIdentification"], ensure_ascii=False, indent=2),
                    json.dumps(item["templateCandidates"], ensure_ascii=False, indent=2),
                    json.dumps(item["ruleCandidates"], ensure_ascii=False, indent=2),
                ]
            )
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="批量切换大模型并生成 Excel 模板识别对比报告。")
    parser.add_argument("--config-file", help="多模型配置 JSON 文件路径。配置格式见 scripts/model_eval_config.example.json。")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="本地 PoC 服务地址，默认 http://127.0.0.1:8000")
    parser.add_argument("--provider", default="openai_compatible_chat", help="单模型模式下的 provider。")
    parser.add_argument("--endpoint-url", help="单模型模式下的模型接口地址。")
    parser.add_argument("--model-name", help="单模型模式下的模型名称。")
    parser.add_argument("--api-key", help="单模型模式下直接传入 API Key。")
    parser.add_argument("--api-key-env", help="单模型模式下从环境变量读取 API Key。")
    parser.add_argument("--timeout-seconds", type=int, default=60, help="单模型模式超时时间。")
    parser.add_argument("--label", help="单模型模式的展示名称。默认使用 model-name。")
    parser.add_argument("--output", help="输出 xlsx 路径。默认写入 reports/ 下。")
    args = parser.parse_args()

    if not args.config_file:
        missing = [name for name in ("endpoint_url", "model_name") if getattr(args, name) is None]
        if missing:
            raise RuntimeError("单模型模式下必须提供 --endpoint-url 和 --model-name。")
    return args


def main() -> None:
    args = parse_args()
    models = load_model_configs(args)
    client = ApiClient(args.base_url)
    model_results: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []

    for model in models:
        summary, results = evaluate_model(client, model)
        model_results.append((summary, results))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(args.output) if args.output else OUTPUT_DIR / f"model_comparison_report_{timestamp}.xlsx"
    sheets = [
        ("说明", build_intro_rows(args.base_url, models, output_path)),
        ("模型汇总", build_summary_rows([item[0] for item in model_results])),
        ("逐例明细", build_detail_rows(model_results)),
        ("原始结果", build_raw_rows(model_results)),
    ]
    write_workbook(output_path, sheets)
    print(output_path)


if __name__ == "__main__":
    main()
