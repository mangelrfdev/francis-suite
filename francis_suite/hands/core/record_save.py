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

Export key/value and system fields are declared under <record-create>
(<record-export-attr>, <record-export-system>, <record-export-root-attr>, …);
record-save only chooses format and path.
Formats that cannot embed those extras omit them — no error.
"""

from __future__ import annotations
from datetime import datetime, timezone

from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.core.records import (
    FRecord,
    FRANCIS_SUITE_VERSION,
    should_emit_export_show_attribute,
)
from francis_suite.core.expressions import FrancisExpression
from francis_suite.hands.base import AbstractHand


def _normalize_system_name(name: str) -> str:
    return name.strip().lower().replace("-", "_")


def _schema_has_flat_export_intent(schema) -> bool:
    """True if record-create declared anything that can populate JSON/CSV _export (not XML-only row/root)."""
    if schema.export_custom_specs or schema.export_system_specs:
        return True
    for r in schema.export_root_specs:
        if not r.xml_only:
            return True
    return False


def _apply_system_export(
    raw_name: str,
    record: FRecord,
    session,
    xa: dict[str, str],
    *,
    row_count_override: int | None = None,
) -> None:
    """Fill xa for known record-export-system names (canonical keys)."""
    key = _normalize_system_name(raw_name)
    if key in ("session_id",):
        sid = getattr(session, "id", None) if session else None
        xa["session_id"] = "" if sid is None else str(sid)
    elif key in ("francis_suite_version", "francis_version"):
        xa["francis_suite_version"] = FRANCIS_SUITE_VERSION
    elif key in ("exported_at", "generated_at"):
        xa["exported_at"] = datetime.now(timezone.utc).isoformat()
    elif key in ("total_records",):
        n = row_count_override if row_count_override is not None else record.count
        xa["total_records"] = str(n)
    elif key in ("status_process",):
        if session is None:
            xa["status_process"] = ""
        else:
            st = getattr(session, "status", None)
            val = getattr(st, "value", None) if st is not None else None
            if val == "running" and getattr(session, "_export_final_hand", False):
                xa["status_process"] = "completed"
            else:
                xa["status_process"] = "" if val is None else str(val)
    else:
        raise ValueError(
            f"[RECORD] unknown record-export-system name '{raw_name}'. "
            "Supported: session_id, francis_suite_version, exported_at, total_records, status_process"
        )


def _build_export_augmentation(
    record: FRecord,
    engine: FrancisExpression,
    session,
    flag_xml,
    *,
    row_count_override: int | None = None,
) -> dict[str, str]:
    """Merge export dict from record-create schema + optional xml-include-root-* flags on this save."""
    schema = record._schema
    xa: dict[str, str] = {}

    for spec in schema.export_custom_specs:
        if not should_emit_export_show_attribute(spec.show_attribute, session):
            continue
        k = engine.resolve(spec.name_raw)
        v = engine.resolve(spec.value_raw or "")
        if spec.required and not str(v).strip():
            raise ValueError(
                f"[RECORD] required record-export-attr '{k}' is empty at save time"
            )
        xa[k] = v

    for spec in schema.export_root_specs:
        if spec.xml_only:
            continue
        if not should_emit_export_show_attribute(spec.show_attribute, session):
            continue
        k = engine.resolve(spec.name_raw)
        v = engine.resolve(spec.value_raw or "")
        if spec.required and not str(v).strip():
            raise ValueError(
                f"[RECORD] required record-export-root-attr '{k}' is empty at save time"
            )
        xa[k] = v

    for spec in schema.export_system_specs:
        if not should_emit_export_show_attribute(spec.show_attribute, session):
            continue
        _apply_system_export(
            spec.name_raw,
            record,
            session,
            xa,
            row_count_override=row_count_override,
        )

    # record-save xml-include-root-* only when record-create did not declare that system field
    if flag_xml("xml-include-root-session-id", False) and "session_id" not in xa:
        sid = getattr(session, "id", None) if session else None
        xa["session_id"] = "" if sid is None else str(sid)
    if flag_xml("xml-include-root-francis-version", False) and "francis_suite_version" not in xa:
        xa["francis_suite_version"] = FRANCIS_SUITE_VERSION
    if flag_xml("xml-include-root-exported-at", False) and "exported_at" not in xa:
        xa["exported_at"] = datetime.now(timezone.utc).isoformat()

    if not xa and not _schema_has_flat_export_intent(schema):
        return None
    return xa


def _xml_inject_session_id(record: FRecord, session, flag: bool) -> bool:
    """If schema declares session_id system attr, follow its show-attribute; else use record-save flag."""
    for s in record._schema.export_system_specs:
        if _normalize_system_name(s.name_raw) == "session_id":
            return should_emit_export_show_attribute(s.show_attribute, session)
    return flag


def _xml_inject_francis_version(record: FRecord, session, flag: bool) -> bool:
    for s in record._schema.export_system_specs:
        if _normalize_system_name(s.name_raw) == "francis_suite_version":
            return should_emit_export_show_attribute(s.show_attribute, session)
    return flag


def _xml_inject_exported_at(record: FRecord, session, flag: bool) -> bool:
    for s in record._schema.export_system_specs:
        if _normalize_system_name(s.name_raw) == "exported_at":
            return should_emit_export_show_attribute(s.show_attribute, session)
    return flag


def _resolve_xml_only_root_attrs(
    record: FRecord,
    engine: FrancisExpression,
    session,
) -> dict[str, str]:
    """XML-only root attrs (legacy record-xml-root-attr: xml_only=True)."""
    out: dict[str, str] = {}
    for spec in record._schema.export_root_specs:
        if not spec.xml_only:
            continue
        if not should_emit_export_show_attribute(spec.show_attribute, session):
            continue
        k = engine.resolve(spec.name_raw)
        v = engine.resolve(spec.value_raw or "")
        if spec.required and not str(v).strip():
            raise ValueError(
                f"[RECORD] required record-xml-root-attr '{k}' is empty at save time"
            )
        out[k] = v
    return out


def _resolve_row_xml_attr_specs(
    record: FRecord,
    engine: FrancisExpression,
) -> list[dict]:
    schema = record._schema
    xml_record: list[dict] = []
    for spec in schema.export_row_specs:
        an = engine.resolve(spec.name_raw)
        if spec.from_field:
            xml_record.append(
                {
                    "name": an,
                    "from_field": spec.from_field,
                    "static": None,
                    "required": spec.required,
                    "show_attribute": spec.show_attribute,
                }
            )
        else:
            sv = engine.resolve(spec.value_raw or "")
            if spec.required and not str(sv).strip():
                raise ValueError(
                    f"[RECORD] required XML <record> attribute '{an}' has empty static value at save time"
                )
            xml_record.append(
                {
                    "name": an,
                    "from_field": None,
                    "static": sv,
                    "required": spec.required,
                    "show_attribute": spec.show_attribute,
                }
            )
    return xml_record


@hand(tag="record-save")
class RecordSaveHand(AbstractHand):
    """
    Persists a record collection to disk.

    Attributes:
        from             (required): name of the record collection.
        format           (required): json, csv, ndjson, xml, html, txt, excel, xlsx, parquet
        path             (required): output file path. Supports ${variables}.
        include-metadata (optional): include public metadata in output. Default: false.
            For duplicate-key rows only, use <record-save-duplicates> (no include-metadata="true").
        clean-data       (optional): if true, omit export/session framing and public metadata from
            the file (CSV comment lines, NDJSON export/metadata lines, JSON wrappers, etc.).
            Default: false. Takes precedence over include-metadata for what is written.
        allow-nested     (optional): if true, json/ndjson rows keep nested group objects; tabular
            formats use dotted keys (group.field). Default: false.
        allow-prefix     (optional): if true, flat keys keep the group prefix (e.g. listing.title).
            For json/ndjson, ignored when allow-nested is true. Default: false.
        allow-sufix      (optional): alias for allow-prefix (same behavior).
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
        clean_data = self.attr("clean-data", "false").lower() == "true"
        allow_nested = self.attr("allow-nested", "false").lower() == "true"
        raw_prefix = self.attr("allow-prefix", "").strip()
        raw_sufix_alias = self.attr("allow-sufix", "").strip()
        if raw_prefix:
            allow_prefix = raw_prefix.lower() in ("true", "1", "yes")
        elif raw_sufix_alias:
            allow_prefix = raw_sufix_alias.lower() in ("true", "1", "yes")
        else:
            allow_prefix = False
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

        want_session = _xml_inject_session_id(record, self.session, _flag_xml("xml-include-root-session-id", False))
        want_version = _xml_inject_francis_version(record, self.session, _flag_xml("xml-include-root-francis-version", False))
        want_exported = _xml_inject_exported_at(record, self.session, _flag_xml("xml-include-root-exported-at", False))

        xml_root_extra: dict[str, str] = {}
        xml_record_specs: list[dict] | None = None
        if fmt_l == "xml":
            xml_root_extra = _resolve_xml_only_root_attrs(record, engine, self.session)
            xml_record_specs = _resolve_row_xml_attr_specs(record, engine)

        record.save(
            fmt,
            path,
            include_metadata=include_metadata,
            clean_data=clean_data,
            allow_nested=allow_nested,
            allow_prefix=allow_prefix,
            session=self.session,
            sheet_name=sheet_name,
            metadata_sheet_name=metadata_sheet_name,
            html_title=html_title,
            export_augmentation=export_augmentation,
            xml_include_root_workflow=_flag_xml("xml-include-root-workflow", True),
            xml_include_root_total_records=_flag_xml("xml-include-root-total-records", True),
            xml_include_root_session_id=want_session,
            xml_include_root_francis_version=want_version,
            xml_include_root_exported_at=want_exported,
            xml_include_record_workflow=_flag_xml("xml-include-record-workflow", True),
            xml_include_record_key=_flag_xml("xml-include-record-key", True),
            xml_root_extra_attrs=xml_root_extra,
            xml_record_extra_attrs=xml_record_extra,
            xml_record_attr_specs_resolved=xml_record_specs,
        )
        return FEmptyVariable()
