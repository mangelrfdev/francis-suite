"""
hands/core/record_save_duplicates.py

RecordSaveDuplicatesHand implements the <record-save-duplicates> tag.
Exports rows that were skipped as duplicate <record-key> occurrences (subsequent
rows with the same key as an earlier accepted row).

Public metadata (include-metadata) is not supported here — use <record-save> for
session/public metadata; duplicate counts can appear there via auto metadata when implemented.
"""

from __future__ import annotations

from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.core.records import FRecord
from francis_suite.core.expressions import FrancisExpression
from francis_suite.hands.base import AbstractHand
from francis_suite.hands.core.record_save import (
    _build_export_augmentation,
    _resolve_row_xml_attr_specs,
    _resolve_xml_only_root_attrs,
    _xml_inject_exported_at,
    _xml_inject_francis_version,
    _xml_inject_session_id,
)


@hand(tag="record-save-duplicates")
class RecordSaveDuplicatesHand(AbstractHand):
    """
    Persist duplicate-key rows (same schema as primary rows) to disk.

    Requires <record-key> on the record. If no duplicate rows were collected,
    skips writing (same pattern as empty primary save).

    Attributes:
        from   (required): name of the record collection.
        format (required): json, csv, ndjson, xml, html, txt, excel, xlsx, parquet
        path   (required): output file path. Supports ${variables}.

    Does not support include-metadata — use <record-save> for public metadata.

    Other attributes match <record-save> where applicable (sheet-name, html-title, xml-*, etc.).
    """

    def execute(self) -> FVariable:
        if self.attr("include-metadata", "false").lower() == "true":
            raise ValueError(
                "[RECORD] <record-save-duplicates> does not support include-metadata=\"true\" — "
                "use <record-save> for public metadata."
            )

        engine = FrancisExpression(self.context)
        record_name = engine.resolve(self.require_attr("from"))
        fmt = engine.resolve(self.require_attr("format"))
        path = engine.resolve(self.require_attr("path"))
        sheet_name = engine.resolve(self.attr("sheet-name", "Data"))
        metadata_sheet_name = engine.resolve(self.attr("metadata-sheet-name", "Metadata"))
        html_title_raw = self.attr("html-title", "")
        html_title = engine.resolve(html_title_raw) if html_title_raw.strip() else None
        clean_data = self.attr("clean-data", "false").lower() == "true"

        record = self.context.get_shared_box(record_name)

        if not isinstance(record, FRecord):
            raise ValueError(
                f"[RECORD] record '{record_name}' not found. "
                f"Make sure <record-create name=\"{record_name}\"> runs first."
            )

        if not record.has_record_key:
            raise ValueError(
                f"[RECORD] <record-save-duplicates> requires <record-key> on "
                f"<record-create name=\"{record_name}\">."
            )

        dup_rows = record.duplicate_rows
        if not dup_rows:
            print(
                f"[RECORD] no duplicate-key rows for '{record_name}' — "
                f"skipping save to '{path}'"
            )
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

        export_augmentation = _build_export_augmentation(
            record,
            engine,
            self.session,
            _flag_xml,
            row_count_override=len(dup_rows),
        )

        want_session = _xml_inject_session_id(
            record, self.session, _flag_xml("xml-include-root-session-id", False)
        )
        want_version = _xml_inject_francis_version(
            record, self.session, _flag_xml("xml-include-root-francis-version", False)
        )
        want_exported = _xml_inject_exported_at(
            record, self.session, _flag_xml("xml-include-root-exported-at", False)
        )

        xml_root_extra: dict[str, str] = {}
        xml_record_specs: list[dict] | None = None
        if fmt_l == "xml":
            xml_root_extra = _resolve_xml_only_root_attrs(record, engine, self.session)
            xml_record_specs = _resolve_row_xml_attr_specs(record, engine)

        record.save(
            fmt,
            path,
            data_rows=dup_rows,
            include_metadata=False,
            clean_data=clean_data,
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
