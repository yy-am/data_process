from __future__ import annotations

import json
import mimetypes
import os
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import error, request
from xml.sax.saxutils import escape


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = PROJECT_ROOT / "sample_excels" / "input_files"
OUTPUT_DIR = PROJECT_ROOT / "reports"
OUTPUT_PATH = OUTPUT_DIR / "excel_poc_test_report_20260430.xlsx"
BASE_URL = os.environ.get("POC_BASE_URL", "http://127.0.0.1:8000")


@dataclass(frozen=True)
class CaseSpec:
    file_name: str
    case_type: str
    expected_template: str | None
    expected_scene: str | None
    expected_country: str | None
    description: str


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


def call_json(method: str, path: str, payload: dict[str, Any] | None = None, timeout: int = 180) -> dict[str, Any]:
    url = f"{BASE_URL}{path}"
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url=url, method=method, data=data, headers=headers)
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            parsed = json.loads(resp.read().decode("utf-8"))
            return parsed["data"]
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed: {exc.code} {body}") from exc


def upload_excel(file_path: Path, input_type: str = "EXCEL", timeout: int = 180) -> dict[str, Any]:
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
        url=f"{BASE_URL}/api/v1/tasks/upload",
        method="POST",
        data=b"".join(parts),
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            parsed = json.loads(resp.read().decode("utf-8"))
            return parsed["data"]
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"upload {file_path.name} failed: {exc.code} {body}") from exc


def configure_template_model() -> None:
    api_key = os.environ.get("POC_TEMPLATE_API_KEY")
    if not api_key:
        raise RuntimeError("Environment variable POC_TEMPLATE_API_KEY is required.")

    payload = {
        "provider": "openai_compatible_chat",
        "model": os.environ.get("POC_TEMPLATE_MODEL", "deepseek-v3.1"),
        "endpointUrl": os.environ.get("POC_TEMPLATE_ENDPOINT", "https://jeniya.cn/v1/chat/completions"),
        "apiKey": api_key,
        "timeoutSeconds": int(os.environ.get("POC_TEMPLATE_TIMEOUT", "60")),
    }
    call_json("POST", "/api/v1/agents/template-identification/config", payload=payload)


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


def build_report_rows() -> tuple[list[list[Any]], list[list[Any]], list[list[Any]], list[list[Any]]]:
    summary_rows: list[list[Any]] = [[
        "序号",
        "文件名",
        "测试类型",
        "设计目标",
        "预期模板",
        "预期场景",
        "预期国家",
        "实际模板",
        "实际场景",
        "实际国家",
        "置信度",
        "需要人工确认",
        "规则候选数",
        "首个规则编码",
        "结果判定",
        "结论说明",
    ]]

    snapshot_rows: list[list[Any]] = [[
        "序号",
        "文件名",
        "Sheet 名称",
        "表头数量",
        "表头预览",
        "样本行预览",
        "任务状态",
        "任务 ID",
    ]]

    raw_rows: list[list[Any]] = [[
        "序号",
        "文件名",
        "模板识别原始结果",
        "模板与规则候选原始结果",
    ]]

    intro_rows: list[list[Any]] = [
        ["PoC 报告名称", "Excel 加工 PoC 测试结果汇总"],
        ["生成时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ["测试范围", "Excel 输入链路：上传 -> 输入快照 -> 模板目录识别 -> 规则候选"],
        ["当前真实能力", "已验证大模型模板识别；Excel 最终规则执行与导出尚未作为本轮验收项纳入。"],
        ["结果判定口径", "非歧义样例要求 templateCode/sceneCode/countryCode 与预期一致；歧义样例要求 needUserConfirm=true 且不强行输出模板。"],
        ["知识库来源", str(PROJECT_ROOT / "knowledge_base" / "template_catalog.md")],
        ["输入样例目录", str(INPUT_DIR)],
    ]

    for index, case in enumerate(CASES, start=1):
        file_path = INPUT_DIR / case.file_name
        upload_result = upload_excel(file_path)
        task = upload_result["task"]
        task_id = task["taskId"]

        snapshot = call_json("GET", f"/api/v1/tasks/{task_id}/input-snapshot")
        template_candidates = call_json("GET", f"/api/v1/tasks/{task_id}/template-candidates")
        identify = call_json("POST", f"/api/v1/agents/template-identification/tasks/{task_id}")

        try:
            rule_candidates = call_json("GET", f"/api/v1/tasks/{task_id}/rule-candidates")
            rule_list = rule_candidates.get("candidates", [])
        except Exception as exc:  # noqa: BLE001
            rule_candidates = {"error": str(exc)}
            rule_list = []

        task_summary = call_json("GET", f"/api/v1/tasks/{task_id}")
        verdict, verdict_reason = classify_result(case, identify)

        first_sheet = (snapshot.get("sheets") or [{}])[0]
        headers = first_sheet.get("headers", [])
        sample_rows = first_sheet.get("sampleRows", [])
        header_preview = " | ".join(headers[:15])
        sample_preview = json.dumps(sample_rows[:1], ensure_ascii=False)
        top_rule_code = "-"
        if rule_list:
            top_rule_code = rule_list[0].get("ruleCode") or rule_list[0].get("code") or "-"

        summary_rows.append(
            [
                index,
                case.file_name,
                case.case_type,
                case.description,
                case.expected_template or "应保持未解析",
                case.expected_scene or "-",
                case.expected_country or "-",
                identify.get("templateCode") or "-",
                identify.get("sceneCode") or "-",
                identify.get("countryCode") or "-",
                identify.get("confidence"),
                "是" if identify.get("needUserConfirm") else "否",
                len(rule_list),
                top_rule_code,
                verdict,
                verdict_reason,
            ]
        )

        snapshot_rows.append(
            [
                index,
                case.file_name,
                first_sheet.get("sheetName", "-"),
                len(headers),
                header_preview,
                sample_preview,
                task_summary.get("status", "-"),
                task_id,
            ]
        )

        raw_rows.append(
            [
                index,
                case.file_name,
                json.dumps(identify, ensure_ascii=False, indent=2),
                json.dumps(
                    {
                        "templateCandidates": template_candidates,
                        "ruleCandidates": rule_candidates,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            ]
        )

    return intro_rows, summary_rows, snapshot_rows, raw_rows


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
            if row_idx > 1 and col_idx == len(row) - 1 and value in {"通过", "未通过"}:
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


def write_workbook(sheets: list[tuple[str, list[list[Any]]]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet3.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet4.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>""",
        )
        zf.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>""",
        )
        utc_now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        zf.writestr(
            "docProps/core.xml",
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Excel 加工 PoC 测试报告</dc:title>
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
            workbook_sheets.append(f'<sheet name="{escape(name)}" sheetId="{idx}" r:id="rId{idx}"/>')
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


def main() -> None:
    configure_template_model()
    intro_rows, summary_rows, snapshot_rows, raw_rows = build_report_rows()
    write_workbook(
        [
            ("PoC说明", intro_rows),
            ("测试结论", summary_rows),
            ("输入快照", snapshot_rows),
            ("原始结果", raw_rows),
        ]
    )
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
