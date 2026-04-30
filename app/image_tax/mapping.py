from __future__ import annotations

from app.domain.enums import PreviewValidationStatus
from app.schemas.preview import PreviewRow, PreviewRowsPage, PreviewSummary


TAX_SCREENSHOT_TEMPLATE_CODE = "TAX_SCREENSHOT_CN_STANDARD"
TAX_SCREENSHOT_SCENE_CODE = "tax_screenshot"
TAX_SCREENSHOT_COUNTRY_CODE = "cn"
TAX_SCREENSHOT_RULE_CODE = "TAX_SCREENSHOT_CN_FIXED_MAPPING"

TAX_SCREENSHOT_TARGET_FIELDS = [
    "invoice_code",
    "invoice_no",
    "invoice_date",
    "buyer_name",
    "buyer_tax_no",
    "seller_name",
    "seller_tax_no",
    "amount_without_tax",
    "tax_amount",
    "total_amount_with_tax",
    "check_code",
    "invoice_status",
    "remarks",
]


def build_image_preview_from_mapped_record(mapped_record: dict[str, str | None]) -> tuple[PreviewSummary, PreviewRowsPage]:
    normalized_record = {field: mapped_record.get(field) for field in TAX_SCREENSHOT_TARGET_FIELDS}
    row = PreviewRow(
        rowNo=1,
        sourceRowRef={"imageSource": "tax-bureau-screenshot", "rowType": "single-record"},
        targetData=normalized_record,
        validationStatus=PreviewValidationStatus.SUCCESS,
        warningFlags=[],
    )
    summary = PreviewSummary(totalRows=1, successRows=1, warningRows=0, errorRows=0)
    page = PreviewRowsPage(items=[row], page=1, pageSize=20, total=1)
    return summary, page
