from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from app.core.exceptions import DomainError
from app.parsers.base import InputParser
from app.schemas.snapshot import ParsedInputSnapshot, ParsedSheetSnapshot


SPREADSHEET_NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


@dataclass(slots=True)
class ExcelParser(InputParser):
    sample_row_limit: int = 5

    def parse(self, file_path: Path) -> ParsedInputSnapshot:
        try:
            with ZipFile(file_path) as archive:
                shared_strings = self._load_shared_strings(archive)
                workbook_root = self._read_xml(archive, "xl/workbook.xml")
                rel_root = self._read_xml(archive, "xl/_rels/workbook.xml.rels")
                sheet_targets = self._build_sheet_targets(rel_root)
                sheets = []

                for sheet_node in workbook_root.findall("main:sheets/main:sheet", SPREADSHEET_NS):
                    sheet_name = sheet_node.attrib.get("name", "")
                    relationship_id = sheet_node.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
                    if not relationship_id:
                        raise DomainError(
                            code="HEADER_NOT_DETECTED",
                            message=f"Workbook sheet {sheet_name or '<unknown>'} is missing relationship metadata.",
                            status_code=422,
                        )

                    target = sheet_targets.get(relationship_id)
                    if target is None:
                        raise DomainError(
                            code="HEADER_NOT_DETECTED",
                            message=f"Workbook sheet {sheet_name or '<unknown>'} cannot be resolved to a worksheet part.",
                            status_code=422,
                        )

                    sheet_path = f"xl/{target}"
                    rows = self._load_sheet_rows(archive, sheet_path, shared_strings)
                    sheets.append(self._build_sheet_snapshot(sheet_name=sheet_name, rows=rows))
        except BadZipFile as exc:
            raise DomainError(
                code="UNSUPPORTED_FILE_TYPE",
                message=f"Excel parser only supports .xlsx OpenXML workbooks. File {file_path.name} is not a valid .xlsx package.",
                status_code=422,
            ) from exc

        if not sheets:
            raise DomainError(
                code="HEADER_NOT_DETECTED",
                message=f"No worksheets were found in workbook {file_path.name}.",
                status_code=422,
            )

        return ParsedInputSnapshot(inputType="EXCEL", sheets=sheets)

    def _read_xml(self, archive: ZipFile, member_name: str) -> ElementTree.Element:
        try:
            with archive.open(member_name) as xml_file:
                return ElementTree.parse(xml_file).getroot()
        except KeyError as exc:
            raise DomainError(
                code="UNSUPPORTED_FILE_TYPE",
                message=f"Workbook package is missing required part {member_name}.",
                status_code=422,
            ) from exc

    def _load_shared_strings(self, archive: ZipFile) -> list[str]:
        try:
            root = self._read_xml(archive, "xl/sharedStrings.xml")
        except DomainError as exc:
            if exc.code == "UNSUPPORTED_FILE_TYPE":
                return []
            raise

        values: list[str] = []
        for string_item in root.findall("main:si", SPREADSHEET_NS):
            parts = [node.text or "" for node in string_item.findall(".//main:t", SPREADSHEET_NS)]
            values.append("".join(parts))
        return values

    def _build_sheet_targets(self, rel_root: ElementTree.Element) -> dict[str, str]:
        targets: dict[str, str] = {}
        for rel in rel_root.findall("pkgrel:Relationship", SPREADSHEET_NS):
            relationship_id = rel.attrib.get("Id")
            target = rel.attrib.get("Target")
            if relationship_id and target:
                targets[relationship_id] = target
        return targets

    def _load_sheet_rows(self, archive: ZipFile, sheet_path: str, shared_strings: list[str]) -> list[list[str]]:
        root = self._read_xml(archive, sheet_path)
        rows: list[list[str]] = []
        for row_node in root.findall("main:sheetData/main:row", SPREADSHEET_NS):
            cell_map: dict[int, str] = {}
            max_index = -1
            for cell in row_node.findall("main:c", SPREADSHEET_NS):
                reference = cell.attrib.get("r")
                if not reference:
                    continue
                column_index = self._column_index_from_reference(reference)
                cell_map[column_index] = self._read_cell_value(cell, shared_strings)
                max_index = max(max_index, column_index)

            if max_index < 0:
                continue

            row_values = [cell_map.get(index, "") for index in range(max_index + 1)]
            rows.append(row_values)
        return rows

    def _read_cell_value(self, cell: ElementTree.Element, shared_strings: list[str]) -> str:
        cell_type = cell.attrib.get("t")
        value_node = cell.find("main:v", SPREADSHEET_NS)
        inline_node = cell.find("main:is", SPREADSHEET_NS)
        if inline_node is not None:
            return "".join(node.text or "" for node in inline_node.findall(".//main:t", SPREADSHEET_NS)).strip()
        if value_node is None or value_node.text is None:
            return ""

        raw_value = value_node.text.strip()
        if cell_type == "s":
            index = int(raw_value)
            if index >= len(shared_strings):
                raise DomainError(
                    code="UNSUPPORTED_FILE_TYPE",
                    message="Workbook shared string index is out of range.",
                    status_code=422,
                )
            return shared_strings[index].strip()
        return raw_value

    def _build_sheet_snapshot(self, sheet_name: str, rows: list[list[str]]) -> ParsedSheetSnapshot:
        if not rows:
            raise DomainError(
                code="HEADER_NOT_DETECTED",
                message=f"Sheet {sheet_name or '<unknown>'} does not contain any rows.",
                status_code=422,
            )

        header_row = rows[0]
        headers = [header.strip() for header in header_row]
        if not any(headers):
            raise DomainError(
                code="HEADER_NOT_DETECTED",
                message=f"Sheet {sheet_name or '<unknown>'} does not contain a usable header row.",
                status_code=422,
            )

        normalized_headers = [self._normalize_header(header) for header in headers]
        sample_rows = [
            {headers[index]: row[index] if index < len(row) else "" for index in range(len(headers))}
            for row in rows[1 : 1 + self.sample_row_limit]
        ]
        column_stats = {
            headers[index]: {
                "nonEmptySampleCount": sum(1 for row in rows[1:] if index < len(row) and str(row[index]).strip()),
                "sampleValueCount": len(rows[1:]),
            }
            for index in range(len(headers))
            if headers[index]
        }
        header_confidence = {header: 1.0 for header in headers if header}

        return ParsedSheetSnapshot(
            sheetName=sheet_name or "Sheet1",
            headers=headers,
            normalizedHeaders=normalized_headers,
            sampleRows=sample_rows,
            columnStats=column_stats,
            headerConfidence=header_confidence,
        )

    def _column_index_from_reference(self, reference: str) -> int:
        letters = "".join(char for char in reference if char.isalpha()).upper()
        index = 0
        for char in letters:
            index = index * 26 + (ord(char) - ord("A") + 1)
        return index - 1

    def _normalize_header(self, header: str) -> str:
        return "".join(char.lower() for char in header.strip() if not char.isspace())
