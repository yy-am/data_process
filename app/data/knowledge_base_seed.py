from __future__ import annotations

from app.repositories.knowledge_base_repository import (
    TemplateDefinition,
    TemplateField,
    TemplateHeaderAlias,
)


TEMPLATE_SEED_DATA: list[TemplateDefinition] = [
    TemplateDefinition(
        template_code="PAYMENT_INVOICE_V1",
        template_name="Payment Invoice",
        source_type="EXCEL",
        fields=[
            TemplateField(field_code="invoice_no", required=True),
            TemplateField(field_code="invoice_date", required=True),
            TemplateField(field_code="buyer_name", required=True),
            TemplateField(field_code="seller_name", required=False),
            TemplateField(field_code="currency", required=True),
            TemplateField(field_code="amount", required=True),
        ],
        header_aliases=[
            TemplateHeaderAlias(
                field_code="invoice_no",
                header_alias="Invoice No",
                normalized_alias="invoiceno",
                priority=100,
                confidence=0.99,
            ),
            TemplateHeaderAlias(
                field_code="invoice_no",
                header_alias="Invoice Number",
                normalized_alias="invoicenumber",
                priority=95,
                confidence=0.96,
            ),
            TemplateHeaderAlias(
                field_code="invoice_date",
                header_alias="Invoice Date",
                normalized_alias="invoicedate",
                priority=100,
                confidence=0.99,
            ),
            TemplateHeaderAlias(
                field_code="buyer_name",
                header_alias="Buyer Name",
                normalized_alias="buyername",
                priority=100,
                confidence=0.98,
            ),
            TemplateHeaderAlias(
                field_code="seller_name",
                header_alias="Seller Name",
                normalized_alias="sellername",
                priority=100,
                confidence=0.98,
            ),
            TemplateHeaderAlias(
                field_code="currency",
                header_alias="Currency",
                normalized_alias="currency",
                priority=100,
                confidence=0.99,
            ),
            TemplateHeaderAlias(
                field_code="amount",
                header_alias="Amount",
                normalized_alias="amount",
                priority=100,
                confidence=0.99,
            ),
        ],
    ),
    TemplateDefinition(
        template_code="CUSTOMS_DECLARATION_V1",
        template_name="Customs Declaration",
        source_type="EXCEL",
        fields=[
            TemplateField(field_code="declaration_no", required=True),
            TemplateField(field_code="declaration_date", required=True),
            TemplateField(field_code="exporter_name", required=True),
            TemplateField(field_code="importer_name", required=True),
            TemplateField(field_code="hs_code", required=True),
            TemplateField(field_code="declared_value", required=True),
        ],
        header_aliases=[
            TemplateHeaderAlias(
                field_code="declaration_no",
                header_alias="Declaration No",
                normalized_alias="declarationno",
                priority=100,
                confidence=0.99,
            ),
            TemplateHeaderAlias(
                field_code="declaration_date",
                header_alias="Declaration Date",
                normalized_alias="declarationdate",
                priority=100,
                confidence=0.99,
            ),
            TemplateHeaderAlias(
                field_code="exporter_name",
                header_alias="Exporter",
                normalized_alias="exporter",
                priority=100,
                confidence=0.97,
            ),
            TemplateHeaderAlias(
                field_code="importer_name",
                header_alias="Importer",
                normalized_alias="importer",
                priority=100,
                confidence=0.97,
            ),
            TemplateHeaderAlias(
                field_code="hs_code",
                header_alias="HS Code",
                normalized_alias="hscode",
                priority=100,
                confidence=0.99,
            ),
            TemplateHeaderAlias(
                field_code="declared_value",
                header_alias="Declared Value",
                normalized_alias="declaredvalue",
                priority=100,
                confidence=0.99,
            ),
        ],
    ),
]
