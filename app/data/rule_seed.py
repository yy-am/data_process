from __future__ import annotations

from app.repositories.rule_repository import (
    MappingRuleDefinition,
    RuleMappingItem,
)


RULE_SEED_DATA: list[MappingRuleDefinition] = [
    MappingRuleDefinition(
        rule_code="PAYMENT_INVOICE_US_STANDARD",
        rule_name="US payment invoice mapping",
        scene_code="PAYMENT",
        country_code="US",
        template_code="PAYMENT_INVOICE_V1",
        source_type="EXCEL",
        status="ACTIVE",
        priority=90,
        version=1,
        mapping_dsl={
            "version": 1,
            "mappings": [
                {"targetField": "invoice_no", "type": "direct", "sourceField": "Invoice No"},
                {"targetField": "invoice_date", "type": "to_date", "sourceField": "Invoice Date"},
                {"targetField": "buyer_name", "type": "direct", "sourceField": "Buyer Name"},
                {"targetField": "seller_name", "type": "direct", "sourceField": "Seller Name"},
                {"targetField": "currency", "type": "trim_upper", "sourceField": "Currency"},
                {"targetField": "amount", "type": "to_number", "sourceField": "Amount"},
            ],
        },
        rule_summary_text="Standard payment invoice mapping for US operations.",
        mapping_items=[
            RuleMappingItem(
                target_field_code="invoice_no",
                transform_type="direct",
                config={"sourceField": "Invoice No"},
                sort_order=1,
            ),
            RuleMappingItem(
                target_field_code="invoice_date",
                transform_type="to_date",
                config={"sourceField": "Invoice Date", "format": "YYYY-MM-DD"},
                sort_order=2,
            ),
            RuleMappingItem(
                target_field_code="buyer_name",
                transform_type="direct",
                config={"sourceField": "Buyer Name"},
                sort_order=3,
            ),
            RuleMappingItem(
                target_field_code="seller_name",
                transform_type="direct",
                config={"sourceField": "Seller Name"},
                sort_order=4,
            ),
            RuleMappingItem(
                target_field_code="currency",
                transform_type="trim_upper",
                config={"sourceField": "Currency"},
                sort_order=5,
            ),
            RuleMappingItem(
                target_field_code="amount",
                transform_type="to_number",
                config={"sourceField": "Amount"},
                sort_order=6,
            ),
        ],
        examples=[
            {
                "name": "US payment invoice sample",
                "source": {
                    "Invoice No": "INV-1001",
                    "Invoice Date": "2026-04-01",
                    "Buyer Name": "Acme LLC",
                    "Seller Name": "Global Supplies Ltd",
                    "Currency": "usd",
                    "Amount": "1200.50",
                },
                "target": {
                    "invoice_no": "INV-1001",
                    "invoice_date": "2026-04-01",
                    "buyer_name": "Acme LLC",
                    "seller_name": "Global Supplies Ltd",
                    "currency": "USD",
                    "amount": 1200.5,
                },
            }
        ],
    ),
    MappingRuleDefinition(
        rule_code="CUSTOMS_DECLARATION_CN_STANDARD",
        rule_name="CN customs declaration mapping",
        scene_code="CUSTOMS",
        country_code="CN",
        template_code="CUSTOMS_DECLARATION_V1",
        source_type="EXCEL",
        status="ACTIVE",
        priority=95,
        version=1,
        mapping_dsl={
            "version": 1,
            "mappings": [
                {"targetField": "declaration_no", "type": "direct", "sourceField": "Declaration No"},
                {"targetField": "declaration_date", "type": "to_date", "sourceField": "Declaration Date"},
                {"targetField": "exporter_name", "type": "direct", "sourceField": "Exporter"},
                {"targetField": "importer_name", "type": "direct", "sourceField": "Importer"},
                {"targetField": "hs_code", "type": "trim", "sourceField": "HS Code"},
                {"targetField": "declared_value", "type": "to_number", "sourceField": "Declared Value"},
            ],
        },
        rule_summary_text="Standard customs declaration mapping for CN operations.",
        mapping_items=[
            RuleMappingItem(
                target_field_code="declaration_no",
                transform_type="direct",
                config={"sourceField": "Declaration No"},
                sort_order=1,
            ),
            RuleMappingItem(
                target_field_code="declaration_date",
                transform_type="to_date",
                config={"sourceField": "Declaration Date", "format": "YYYY-MM-DD"},
                sort_order=2,
            ),
            RuleMappingItem(
                target_field_code="exporter_name",
                transform_type="direct",
                config={"sourceField": "Exporter"},
                sort_order=3,
            ),
            RuleMappingItem(
                target_field_code="importer_name",
                transform_type="direct",
                config={"sourceField": "Importer"},
                sort_order=4,
            ),
            RuleMappingItem(
                target_field_code="hs_code",
                transform_type="trim",
                config={"sourceField": "HS Code"},
                sort_order=5,
            ),
            RuleMappingItem(
                target_field_code="declared_value",
                transform_type="to_number",
                config={"sourceField": "Declared Value"},
                sort_order=6,
            ),
        ],
        examples=[
            {
                "name": "CN customs declaration sample",
                "source": {
                    "Declaration No": "CN-2026-0008",
                    "Declaration Date": "2026-04-12",
                    "Exporter": "Shenzhen Trading Co",
                    "Importer": "Shanghai Importer Ltd",
                    "HS Code": " 847130 ",
                    "Declared Value": "88000",
                },
                "target": {
                    "declaration_no": "CN-2026-0008",
                    "declaration_date": "2026-04-12",
                    "exporter_name": "Shenzhen Trading Co",
                    "importer_name": "Shanghai Importer Ltd",
                    "hs_code": "847130",
                    "declared_value": 88000,
                },
            }
        ],
    ),
]
