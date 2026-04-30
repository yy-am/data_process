from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from app.core.exceptions import DomainError
from app.domain.enums import InputType
from app.parsers.base import InputParser
from app.repositories.knowledge_base_repository import (
    CATALOG_ENTRY_PREFIX,
    CATALOG_HEADERS_SEPARATOR,
    KnowledgeBaseRepository,
    TemplateDefinition,
    TemplateField,
    TemplateHeaderAlias,
)
from app.repositories.rule_repository import RuleRepository
from app.schemas.knowledge_base import (
    KnowledgeBundleImportResult,
    TemplateImportResult,
    TemplateKnowledgeItem,
)
from app.services.file_storage_service import FileStorageService


@dataclass(slots=True)
class KnowledgeBaseService:
    file_storage_service: FileStorageService
    excel_parser: InputParser
    knowledge_base_repository: KnowledgeBaseRepository
    rule_repository: RuleRepository
    knowledge_base_root: Path

    async def import_template_excel(
        self,
        upload_file: UploadFile,
        template_code: str,
        template_name: str,
    ) -> TemplateImportResult:
        stored_filename, _ = await self.file_storage_service.save_upload(upload_file)
        parsed_snapshot = self.excel_parser.parse(Path(stored_filename))
        sheet = parsed_snapshot.sheets[0]
        fields = [
            TemplateField(field_code=self._field_code_from_header(header), required=True)
            for header in sheet.headers
            if header.strip()
        ]
        header_aliases = [
            TemplateHeaderAlias(
                field_code=self._field_code_from_header(header),
                header_alias=header,
                normalized_alias=normalized_header,
                priority=100,
                confidence=1.0,
            )
            for header, normalized_header in zip(sheet.headers, sheet.normalized_headers, strict=False)
            if header.strip()
        ]
        template = TemplateDefinition(
            template_code=template_code,
            template_name=template_name,
            source_type=InputType.EXCEL.value,
            fields=fields,
            header_aliases=header_aliases,
        )
        self.knowledge_base_repository.add_template(template)
        return TemplateImportResult(
            templateCode=template.template_code,
            templateName=template.template_name,
            sourceType=template.source_type,
            fieldCount=len(fields),
            headerAliasCount=len(header_aliases),
        )

    def list_templates(self) -> list[TemplateKnowledgeItem]:
        return [
            TemplateKnowledgeItem(
                templateCode=template.template_code,
                templateName=template.template_name,
                sourceType=template.source_type,
                fieldCount=len(template.fields),
                headerAliasCount=len(template.header_aliases),
                scene=template.scene,
                country=template.country,
                templatePath=template.template_path.as_posix() if template.template_path else None,
                sheetCount=len(template.sheet_names),
            )
            for template in self.knowledge_base_repository.list_all_templates()
        ]

    async def import_knowledge_bundle(
        self,
        *,
        scene: str,
        country: str,
        spec_file: UploadFile,
        instruction_text: str | None = None,
    ) -> KnowledgeBundleImportResult:
        normalized_scene = self._normalize_dir_name(scene)
        normalized_country = self._normalize_dir_name(country)
        target_dir = self.knowledge_base_root / normalized_scene / normalized_country
        target_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_base_root.mkdir(parents=True, exist_ok=True)

        spec_name = spec_file.filename or "mapping_spec.xlsx"
        if not spec_name.lower().endswith(".xlsx"):
            raise DomainError(
                code="UNSUPPORTED_FILE_TYPE",
                message="Knowledge spec file must be .xlsx.",
                status_code=400,
            )
        template_code = f"{normalized_scene}_{normalized_country}_template".upper()
        rule_target = target_dir / "rule.json"
        catalog_target = self.knowledge_base_root / "template_catalog.md"

        stored_spec, _ = await self.file_storage_service.save_upload(spec_file)
        target_headers, source_headers = self._extract_mapping_rows(Path(stored_spec))
        mappings = self._build_mappings(target_headers, source_headers)
        self._write_rule_json(
            rule_target=rule_target,
            template_code=template_code,
            scene_code=normalized_scene.upper(),
            country_code=normalized_country.upper(),
            mappings=mappings,
            instruction_text=instruction_text,
        )
        self._upsert_template_catalog(
            catalog_target=catalog_target,
            template_code=template_code,
            scene=normalized_scene,
            country=normalized_country,
            headers=source_headers,
        )

        self.rule_repository.refresh()
        return KnowledgeBundleImportResult(
            scene=normalized_scene,
            country=normalized_country,
            specFile=spec_name,
            templateCode=template_code,
            catalogPath=catalog_target.as_posix(),
            rulePath=rule_target.as_posix(),
            mappingCount=len(mappings),
            instructionText=instruction_text,
        )

    def _field_code_from_header(self, header: str) -> str:
        normalized = "".join(char.lower() if char.isalnum() else "_" for char in header.strip())
        compact = "_".join(part for part in normalized.split("_") if part)
        return compact

    def _normalize_dir_name(self, value: str) -> str:
        normalized = "".join(char.lower() if char.isalnum() or char in {"-", "_"} else "_" for char in value.strip())
        compact = "_".join(part for part in normalized.split("_") if part)
        if not compact:
            raise DomainError(
                code="INPUT_INVALID",
                message="Scene and country must not be empty.",
                status_code=400,
            )
        return compact

    def _extract_mapping_rows(self, spec_path: Path) -> tuple[list[str], list[str]]:
        parsed_snapshot = self.excel_parser.parse(spec_path)
        if not parsed_snapshot.sheets:
            raise DomainError(
                code="HEADER_NOT_DETECTED",
                message="Knowledge spec workbook does not contain a usable sheet.",
                status_code=400,
            )
        sheet = parsed_snapshot.sheets[0]
        if not sheet.sample_rows:
            raise DomainError(
                code="HEADER_NOT_DETECTED",
                message="Knowledge spec workbook must contain at least two rows: target row and template row.",
                status_code=400,
            )
        target_headers = [header.strip() for header in sheet.headers]
        source_row = sheet.sample_rows[0]
        source_headers = [str(source_row.get(header, "")).strip() for header in sheet.headers]
        if not any(target_headers) or not any(source_headers):
            raise DomainError(
                code="HEADER_NOT_DETECTED",
                message="Knowledge spec workbook must provide target headers in row 1 and template headers in row 2.",
                status_code=400,
            )
        return target_headers, source_headers

    def _build_mappings(self, target_headers: list[str], source_headers: list[str]) -> list[dict[str, object]]:
        mappings: list[dict[str, object]] = []
        for target_header, source_header in zip(target_headers, source_headers, strict=False):
            target_value = target_header.strip()
            source_value = source_header.strip()
            if not target_value and not source_value:
                continue
            if not target_value:
                continue
            if not source_value:
                continue
            mappings.append(
                {
                    "targetField": target_value,
                    "type": "direct",
                    "sourceField": source_value,
                }
            )
        if not mappings:
            raise DomainError(
                code="HEADER_NOT_DETECTED",
                message="Knowledge spec workbook did not produce any valid target/source mappings.",
                status_code=400,
            )
        return mappings

    def _write_rule_json(
        self,
        *,
        rule_target: Path,
        template_code: str,
        scene_code: str,
        country_code: str,
        mappings: list[dict[str, object]],
        instruction_text: str | None,
    ) -> None:
        mapping_items = []
        for index, mapping in enumerate(mappings, start=1):
            mapping_items.append(
                {
                    "targetField": mapping["targetField"],
                    "type": mapping["type"],
                    "sourceField": mapping["sourceField"],
                }
            )
        rule_payload = {
            "ruleCode": f"{scene_code}_{country_code}_{template_code}_AUTO",
            "ruleName": f"{scene_code} {country_code} auto generated mapping",
            "sceneCode": scene_code,
            "countryCode": country_code,
            "templateCode": template_code,
            "sourceType": "EXCEL",
            "status": "ACTIVE",
            "priority": 80,
            "version": 1,
            "ruleSummaryText": instruction_text or "Auto-generated from row1 target columns and row2 template columns.",
            "mappingDsl": {
                "version": 1,
                "mappings": mapping_items,
            },
            "examples": [],
            "instructionText": instruction_text or "",
        }
        rule_target.write_text(__import__("json").dumps(rule_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _upsert_template_catalog(
        self,
        *,
        catalog_target: Path,
        template_code: str,
        scene: str,
        country: str,
        headers: list[str],
    ) -> None:
        normalized_headers = [header.strip() for header in headers if header.strip()]
        if not normalized_headers:
            raise DomainError(
                code="HEADER_NOT_DETECTED",
                message="Template header row is empty after parsing the knowledge spec workbook.",
                status_code=400,
            )

        existing_lines: list[str] = []
        if catalog_target.is_file():
            existing_lines = catalog_target.read_text(encoding="utf-8").splitlines()
        else:
            try:
                existing_lines = self.knowledge_base_repository.get_catalog_markdown().splitlines()
            except Exception:
                existing_lines = []

        new_entry = (
            f"{CATALOG_ENTRY_PREFIX}"
            f"templateCode: {template_code} | "
            f"scene: {scene} | "
            f"country: {country} | "
            f"headers: {CATALOG_HEADERS_SEPARATOR.join(normalized_headers)}"
        )

        output_lines: list[str] = []
        replaced = False
        for line in existing_lines:
            stripped = line.strip()
            if stripped.startswith(f"{CATALOG_ENTRY_PREFIX}templateCode: {template_code} | "):
                output_lines.append(new_entry)
                replaced = True
            else:
                output_lines.append(line)

        if not output_lines:
            output_lines = [
                "# Template Catalog",
                "",
                "Each line below is one template entry used by the template-identification agent.",
                "The agent must choose only from this catalog.",
                "",
            ]

        if not replaced:
            if output_lines and output_lines[-1] != "":
                output_lines.append("")
            output_lines.append(new_entry)

        catalog_target.write_text("\n".join(output_lines).rstrip() + "\n", encoding="utf-8")
