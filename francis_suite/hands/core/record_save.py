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

Export key/value and system fields (session_id, etc.) are declared under <record-create>
(<record-export-attr>, <record-export-system>); record-save only chooses format and path.
Formats that cannot embed those extras omit them — no error.
"""

from __future__ import annotations
from datetime import datetime, timezone

from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.core.records import FRecord, FRANCIS_SUITE_VERSION
from francis_suite.core.expressions import FrancisExpression
from francis_suite.hands.base import AbstractHand


def _build_export_augmentation(
    record: FRecord,
    engine: FrancisExpression,
    session,
    flag_xml,
) -> dict[str, str]:
    """Merge export dict from record-create schema + optional xml-include-root-* flags on this save."""
    schema = record._schema
    xa: dict[str, str] = {}
    for name_raw, val_raw in schema.export_custom_attrs:
        k = engine.resolve(name_raw)
        xa[k] = engine.resolve(val_raw or "")

    want_sid = schema.export_want_session_id or flag_xml("xml-include-root-session-id", False)
    want_ver = schema.export_want_francis_version or flag_xml("xml-include-root-francis-version", False)
    want_at = schema.export_want_exported_at or flag_xml("xml-include-root-exported-at", False)

    if want_sid and "session_id" not in xa:
        sid = getattr(session, "id", None) if session else None
        xa["session_id"] = "" if sid is None else str(sid)
    if want_ver and "francis_suite_version" not in xa:
        xa["francis_suite_version"] = FRANCIS_SUITE_VERSION
    if want_at and "exported_at" not in xa:
        xa["exported_at"] = datetime.now(timezone.utc).isoformat()

    return xa


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
        xml-include-root-session-id (optional): extra switch for session_id (also from record-create export-system)
        xml-include-root-francis-version (optional): extra switch for francis_suite_version
        xml-include-root-exported-at (optional): extra switch for exported_at

    Child tags (record-save — xml serialization only):
        <xml-record-attr name="...">value</xml-record-attr> — same attribute on every <record> (format xml only)

    Export metadata (session_id, custom keys, etc.): under <record-create> as
    <record-export-attr> / <record-export-system> (aliases <xml-root-attr>, <xml-root-system>).

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
        xml_record_extra: dict[str, str] = {}

        for child in self._node.children:
            if child.tag == "xml-record-attr" and fmt_l == "xml":
                an = engine.resolve(child.require_attr("name"))
                xml_record_extra[an] = engine.resolve(child.text or "")

        def _flag_xml(name: str, default: bool) -> bool:
            v = self.attr(name, "true" if default else "false").strip().lower()
            return v in ("true", "1", "yes")

        export_augmentation = _build_export_augmentation(record, engine, self.session, _flag_xml)

        want_session = record._schema.export_want_session_id or _flag_xml("xml-include-root-session-id", False)
        want_version = record._schema.export_want_francis_version or _flag_xml("xml-include-root-francis-version", False)
        want_exported = record._schema.export_want_exported_at or _flag_xml("xml-include-root-exported-at", False)

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
            xml_root_extra_attrs={},
            xml_record_extra_attrs=xml_record_extra,
        )
        return FEmptyVariable()
