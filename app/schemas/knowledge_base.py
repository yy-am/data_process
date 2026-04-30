from __future__ import annotations

from pydantic import Field

from app.schemas.common import APIModel


class TemplateImportResult(APIModel):
    template_code: str = Field(alias="templateCode")
    template_name: str = Field(alias="templateName")
    source_type: str = Field(alias="sourceType")
    field_count: int = Field(alias="fieldCount")
    header_alias_count: int = Field(alias="headerAliasCount")


class TemplateKnowledgeItem(APIModel):
    template_code: str = Field(alias="templateCode")
    template_name: str = Field(alias="templateName")
    source_type: str = Field(alias="sourceType")
    field_count: int = Field(alias="fieldCount")
    header_alias_count: int = Field(alias="headerAliasCount")
    scene: str | None = None
    country: str | None = None
    template_path: str | None = Field(default=None, alias="templatePath")
    sheet_count: int = Field(default=0, alias="sheetCount")


class KnowledgeBundleImportResult(APIModel):
    scene: str
    country: str
    spec_file: str = Field(alias="specFile")
    template_code: str = Field(alias="templateCode")
    catalog_path: str = Field(alias="catalogPath")
    rule_path: str = Field(alias="rulePath")
    mapping_count: int = Field(alias="mappingCount")
    instruction_text: str | None = Field(default=None, alias="instructionText")
