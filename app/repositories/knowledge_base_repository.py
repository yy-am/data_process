from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from app.core.exceptions import DomainError
from app.domain.enums import InputType
from app.parsers.base import InputParser


CATALOG_ENTRY_PREFIX = "- "
CATALOG_HEADERS_SEPARATOR = " || "


@dataclass(slots=True)
class TemplateField:
    field_code: str
    required: bool


@dataclass(slots=True)
class TemplateHeaderAlias:
    field_code: str
    header_alias: str
    normalized_alias: str
    priority: int
    confidence: float


@dataclass(slots=True)
class TemplateDefinition:
    template_code: str
    template_name: str
    source_type: str
    fields: list[TemplateField]
    header_aliases: list[TemplateHeaderAlias]
    scene: str | None = None
    country: str | None = None
    template_path: Path | None = None
    sheet_names: list[str] = field(default_factory=list)


class KnowledgeBaseRepository(ABC):
    @abstractmethod
    def list_templates(self, source_type: str) -> list[TemplateDefinition]:
        raise NotImplementedError

    @abstractmethod
    def add_template(self, template: TemplateDefinition) -> TemplateDefinition:
        raise NotImplementedError

    @abstractmethod
    def list_all_templates(self) -> list[TemplateDefinition]:
        raise NotImplementedError

    @abstractmethod
    def get_catalog_markdown(self) -> str:
        raise NotImplementedError


class InMemoryKnowledgeBaseRepository(KnowledgeBaseRepository):
    def __init__(self, templates: list[TemplateDefinition] | None = None) -> None:
        self._templates = templates or []

    @classmethod
    def from_seed_data(cls, templates: list[TemplateDefinition]) -> "InMemoryKnowledgeBaseRepository":
        return cls(templates=list(templates))

    def list_templates(self, source_type: str) -> list[TemplateDefinition]:
        return [template for template in self._templates if template.source_type == source_type]

    def add_template(self, template: TemplateDefinition) -> TemplateDefinition:
        self._templates = [item for item in self._templates if item.template_code != template.template_code]
        self._templates.append(template)
        return template

    def list_all_templates(self) -> list[TemplateDefinition]:
        return list(self._templates)

    def get_catalog_markdown(self) -> str:
        entries = [
            _format_catalog_entry(
                template_code=template.template_code,
                scene=template.scene or "",
                country=template.country or "",
                headers=[alias.header_alias for alias in template.header_aliases],
            )
            for template in self._templates
        ]
        return _build_catalog_markdown(entries)


class MarkdownKnowledgeBaseRepository(KnowledgeBaseRepository):
    def __init__(self, knowledge_base_root: Path, excel_parser: InputParser) -> None:
        self._knowledge_base_root = Path(knowledge_base_root).resolve()
        self._excel_parser = excel_parser
        self._catalog_path = self._knowledge_base_root / "template_catalog.md"
        self._runtime_templates: list[TemplateDefinition] = []

    def list_templates(self, source_type: str) -> list[TemplateDefinition]:
        return [template for template in self.list_all_templates() if template.source_type == source_type]

    def add_template(self, template: TemplateDefinition) -> TemplateDefinition:
        self._runtime_templates = [
            item for item in self._runtime_templates if item.template_code != template.template_code
        ]
        self._runtime_templates.append(template)
        return template

    def list_all_templates(self) -> list[TemplateDefinition]:
        catalog_templates = self._load_catalog_templates()
        merged_templates = {template.template_code: template for template in catalog_templates}
        for template in self._runtime_templates:
            merged_templates[template.template_code] = template
        return list(merged_templates.values())

    def get_catalog_markdown(self) -> str:
        self._ensure_catalog_exists()
        return self._catalog_path.read_text(encoding="utf-8")

    def _load_catalog_templates(self) -> list[TemplateDefinition]:
        self._ensure_catalog_exists()
        lines = self._catalog_path.read_text(encoding="utf-8").splitlines()
        templates: list[TemplateDefinition] = []
        seen_codes: set[str] = set()
        for line in lines:
            stripped = line.strip()
            if not stripped.startswith(CATALOG_ENTRY_PREFIX):
                continue
            template = self._parse_catalog_entry(stripped)
            if template.template_code in seen_codes:
                raise DomainError(
                    code="KB_TEMPLATE_DUPLICATE",
                    message=f"Duplicate templateCode found in template catalog: {template.template_code}.",
                    status_code=409,
                )
            seen_codes.add(template.template_code)
            templates.append(template)
        return templates

    def _parse_catalog_entry(self, line: str) -> TemplateDefinition:
        content = line[len(CATALOG_ENTRY_PREFIX):]
        segments = [segment.strip() for segment in content.split(" | ")]
        values: dict[str, str] = {}
        for segment in segments:
            if ":" not in segment:
                continue
            key, raw_value = segment.split(":", 1)
            values[key.strip()] = raw_value.strip()

        template_code = values.get("templateCode", "")
        scene = values.get("scene", "")
        country = values.get("country", "")
        header_blob = values.get("headers", "")
        if not template_code or not scene or not country or not header_blob:
            raise DomainError(
                code="KB_TEMPLATE_INVALID",
                message="Each template_catalog.md entry must define templateCode, scene, country, and headers.",
                status_code=409,
            )

        headers = [item.strip() for item in header_blob.split(CATALOG_HEADERS_SEPARATOR) if item.strip()]
        fields_by_code: dict[str, TemplateField] = {}
        aliases: list[TemplateHeaderAlias] = []
        for header in headers:
            normalized_alias = _normalize_header_for_alias(header)
            if not normalized_alias:
                continue
            field_code = _field_code_from_header(header, normalized_alias)
            fields_by_code.setdefault(field_code, TemplateField(field_code=field_code, required=True))
            aliases.append(
                TemplateHeaderAlias(
                    field_code=field_code,
                    header_alias=header,
                    normalized_alias=normalized_alias,
                    priority=100,
                    confidence=1.0,
                )
            )

        return TemplateDefinition(
            template_code=template_code,
            template_name=template_code,
            source_type=InputType.EXCEL.value,
            fields=list(fields_by_code.values()),
            header_aliases=aliases,
            scene=scene,
            country=country,
            template_path=self._catalog_path,
            sheet_names=["catalog"],
        )

    def _ensure_catalog_exists(self) -> None:
        self._knowledge_base_root.mkdir(parents=True, exist_ok=True)
        if self._catalog_path.is_file():
            return

        migrated_entries = self._load_entries_from_legacy_template_excels()
        self._catalog_path.write_text(_build_catalog_markdown(migrated_entries), encoding="utf-8")

    def _load_entries_from_legacy_template_excels(self) -> list[str]:
        template_files = sorted(
            template_path
            for template_path in self._knowledge_base_root.glob("*/*/*.xlsx")
            if template_path.name.lower() != "mapping_spec.xlsx"
        )
        entries: list[str] = []
        for template_path in template_files:
            relative_path = template_path.relative_to(self._knowledge_base_root)
            scene, country = relative_path.parts[0], relative_path.parts[1]
            parsed_snapshot = self._excel_parser.parse(template_path)
            headers: list[str] = []
            for sheet in parsed_snapshot.sheets:
                for header in sheet.headers:
                    cleaned_header = header.strip()
                    if cleaned_header and cleaned_header not in headers:
                        headers.append(cleaned_header)
            if not headers:
                continue
            entries.append(
                _format_catalog_entry(
                    template_code=template_path.stem,
                    scene=scene,
                    country=country,
                    headers=headers,
                )
            )
        return entries


def _field_code_from_header(header: str, normalized_header: str) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "_" for char in header.strip())
    compact = "_".join(part for part in normalized.split("_") if part)
    return compact or normalized_header


def _normalize_header_for_alias(value: str) -> str:
    return "".join(char.lower() for char in value.strip() if not char.isspace())


def _format_catalog_entry(*, template_code: str, scene: str, country: str, headers: list[str]) -> str:
    header_blob = CATALOG_HEADERS_SEPARATOR.join(header.strip() for header in headers if header.strip())
    return (
        f"{CATALOG_ENTRY_PREFIX}"
        f"templateCode: {template_code} | "
        f"scene: {scene} | "
        f"country: {country} | "
        f"headers: {header_blob}"
    )


def _build_catalog_markdown(entries: list[str]) -> str:
    header_lines = [
        "# Template Catalog",
        "",
        "Each line below is one template entry used by the template-identification agent.",
        "The agent must choose only from this catalog.",
        "",
    ]
    if not entries:
        return "\n".join(header_lines + ["<!-- empty catalog -->", ""])
    return "\n".join(header_lines + entries + [""])
