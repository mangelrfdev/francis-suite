"""
hands/core/record_save.py

RecordSaveHand implements the <record-save> tag.
Persists a record collection to disk in the specified format.

Usage in XML:
    <!-- data only — default, no metadata -->
    <record-save from="propiedadesRecords" format="ndjson" path="output/propiedades.ndjson"/>

    <!-- data with public metadata — only if <record-metadata> was declared -->
    <record-save from="propiedadesRecords" format="json"
                 path="output/propiedades.json"
                 include-metadata="true"/>
"""

from __future__ import annotations
from datetime import datetime, timezone

from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.core.records import FRecord, FRANCIS_SUITE_VERSION
from francis_suite.core.expressions import FrancisExpression
from francis_suite.hands.base import AbstractHand


@hand(tag="record-save")
class RecordSaveHand(AbstractHand):
    """
    Persists a record collection to disk.

    Attributes:
        from             (required): name of the record collection.
        format           (required): json, csv, ndjson, xml, html, txt, excel, xlsx, parquet
        path             (required): output file path. Supports ${variables}.
        include-metadata (optional): include public metadata in output. Default: false.
        sheet-name       (optional): excel — main sheet name (default: Data)
        metadata-sheet-name (optional): excel — sheet for public metadata (default: Metadata)
        html-title       (optional): html — page title and main heading (default: workflow name)
        xml-include-root-workflow (optional): xml — attribute workflow on <Records>. Default: true
        xml-include-root-total-records (optional): xml — total_records (always row count). Default: true
        xml-include-record-workflow (optional): xml — attribute workflow on <record>. Default: true
        xml-include-record-key (optional): xml — attribute recordKey when record-key is set. Default: true
        xml-include-root-session-id (optional): xml — built-in session_id on <Records>. Default: false
        xml-include-root-francis-version (optional): xml — built-in francis_suite_version. Default: false
        xml-include-root-exported-at (optional): xml — built-in exported_at (UTC ISO). Default: false

    Child tags (all formats — embedded where the format supports extra export fields; otherwise ignored):
        <record-export-attr name="...">value</record-export-attr> — key/value for export (body supports ${})
        <record-export-system name="session_id"/> — engine session id (same as xml-include-root-session-id="true")
        <record-export-system name="francis_suite_version"/> — framework version from code
        <record-export-system name="exported_at"/> — ISO-8601 UTC timestamp at save time

    Legacy xml-only (same semantics as record-export-*):
        <xml-root-attr name="...">value</xml-root-attr>, <xml-root-system name="..."/>,
        <xml-record-attr name="...">value</xml-record-attr> — per-record attrs on <record> (xml only)

    Formats:
        json, csv, ndjson — as before
        xml     — <Records> / <record> attributes configurable; see attributes above
        html    — simple table report (UTF-8)
        txt     — tab-separated (TSV), header row
        excel   — .xlsx via openpyxl
        parquet — columnar; flattened rows

    Notes:
        - include-metadata only works if <record-metadata> was declared in record-create
        - Public metadata is only written when status=completed
        - For private/full metadata use <record-save-metadata>

    Returns:
        FEmptyVariable always.

    Examples:
        <!-- data only -->
        <record-save from="productosRecords" format="ndjson" path="output/productos.ndjson"/>

        <!-- data with public metadata -->
        <record-save from="productosRecords" format="json"
                     path="output/productos.json"
                     include-metadata="true"/>
    """

    def execute(self) -> FVariable:
        engine           = FrancisExpression(self.context)
        record_name      = engine.resolve(self.require_attr("from"))
        fmt              = engine.resolve(self.require_attr("format"))
        path             = engine.resolve(self.require_attr("path"))
        include_metadata = self.attr("include-metadata", "false").lower() == "true"
        sheet_name         = engine.resolve(self.attr("sheet-name", "Data"))
        metadata_sheet_name = engine.resolve(self.attr("metadata-sheet-name", "Metadata"))
        html_title_raw     = self.attr("html-title", "")
        html_title         = engine.resolve(html_title_raw) if html_title_raw.strip() else None

        record = self.context.get_shared_box(record_name)

        if not isinstance(record, FRecord):
            raise ValueError(
                f"[RECORD] record '{record_name}' not found. "
                f"Make sure <record-create name=\"{record_name}\"> runs first."
            )

        if record.is_empty():
            print(f"[RECORD] '{record_name}' is empty — skipping save to '{path}'")
            return FEmptyVariable()

        fmt_l = fmt.lower().strip()
        export_augmentation: dict[str, str] = {}
        xml_root_extra: dict[str, str] = {}
        xml_record_extra: dict[str, str] = {}
        sys_session_id = False
        sys_francis_ver = False
        sys_exported_at = False

        def _apply_system_tag(name_raw: str) -> None:
            nonlocal sys_session_id, sys_francis_ver, sys_exported_at
            key = name_raw.strip().lower()
            if key in ("session_id", "session-id"):
                sys_session_id = True
            elif key in ("francis_suite_version", "francis-version", "francis_version"):
                sys_francis_ver = True
            elif key in ("exported_at", "exported-at", "generated_at"):
                sys_exported_at = True

        for child in self._node.children:
            tag = child.tag
            if tag == "record-export-attr":
                an = engine.resolve(child.require_attr("name"))
                export_augmentation[an] = engine.resolve(child.text or "")
            elif tag == "record-export-system":
                _apply_system_tag(engine.resolve(child.require_attr("name")))
            elif tag == "xml-root-attr":
                an = engine.resolve(child.require_attr("name"))
                val = engine.resolve(child.text or "")
                xml_root_extra[an] = val
                export_augmentation[an] = val
            elif tag == "xml-root-system":
                _apply_system_tag(engine.resolve(child.require_attr("name")))
            elif tag == "xml-record-attr" and fmt_l == "xml":
                an = engine.resolve(child.require_attr("name"))
                xml_record_extra[an] = engine.resolve(child.text or "")

        def _flag_xml(name: str, default: bool) -> bool:
            v = self.attr(name, "true" if default else "false").strip().lower()
            return v in ("true", "1", "yes")

        want_session = _flag_xml("xml-include-root-session-id", False) or sys_session_id
        want_version = _flag_xml("xml-include-root-francis-version", False) or sys_francis_ver
        want_exported = _flag_xml("xml-include-root-exported-at", False) or sys_exported_at

        if want_session and "session_id" not in export_augmentation:
            sid = getattr(self.session, "id", None) if self.session else None
            export_augmentation["session_id"] = "" if sid is None else str(sid)
        if want_version and "francis_suite_version" not in export_augmentation:
            export_augmentation["francis_suite_version"] = FRANCIS_SUITE_VERSION
        if want_exported and "exported_at" not in export_augmentation:
            export_augmentation["exported_at"] = datetime.now(timezone.utc).isoformat()

        record.save(
            fmt,
            path,
            include_metadata=include_metadata,
            session=self.session,
            sheet_name=sheet_name,
            metadata_sheet_name=metadata_sheet_name,
            html_title=html_title,
            export_augmentation=export_augmentation or None,
            xml_include_root_workflow=_flag_xml("xml-include-root-workflow", True),
            xml_include_root_total_records=_flag_xml("xml-include-root-total-records", True),
            xml_include_root_session_id=want_session,
            xml_include_root_francis_version=want_version,
            xml_include_root_exported_at=want_exported,
            xml_include_record_workflow=_flag_xml("xml-include-record-workflow", True),
            xml_include_record_key=_flag_xml("xml-include-record-key", True),
            xml_root_extra_attrs=xml_root_extra,
            xml_record_extra_attrs=xml_record_extra,
        )
        return FEmptyVariable()
