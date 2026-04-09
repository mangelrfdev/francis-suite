"""
hands/core/record_save_validation_errors.py

RecordSaveValidationErrorsHand implements the <record-save-validation-errors> tag.
Exports rows that failed schema normalization when record-validation="collect-errors"
on <record-save>.

Each exported row is flat: validation_error (message) + raw_* (field keys from record-add).

Public metadata (include-metadata) is not supported — use <record-save> for that.
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


@hand(tag="record-save-validation-errors")
class RecordSaveValidationErrorsHand(AbstractHand):
    """
    Persist validation-rejected rows (collect-errors mode) to disk.

    If there are no such rows, skips writing.

    Attributes:
        from   (required): name of the record collection.
        format (required): json, csv, ndjson, xml, html, txt, excel, xlsx, parquet
        path   (required): output file path. Supports ${variables}.

    Does not support include-metadata=\"true\" — use <record-save> for public metadata.
    """

    def execute(self) -> FVariable:
        if self.attr("include-metadata", "false").lower() == "true":
            raise ValueError(
                "[RECORD] <record-save-validation-errors> does not support include-metadata=\"true\" — "
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
        allow_nested = self.attr("allow-nested", "false").lower() == "true"
        raw_prefix = self.attr("allow-prefix", "").strip()
        raw_sufix_alias = self.attr("allow-sufix", "").strip()
        if raw_prefix:
            allow_prefix = raw_prefix.lower() in ("true", "1", "yes")
        elif raw_sufix_alias:
            allow_prefix = raw_sufix_alias.lower() in ("true", "1", "yes")
        else:
            allow_prefix = False

        record = self.context.get_shared_box(record_name)

        if not isinstance(record, FRecord):
            raise ValueError(
                f"[RECORD] record '{record_name}' not found. "
                f"Make sure <record-create name=\"{record_name}\"> runs first."
            )

        err_rows = record.validation_error_export_rows()
        if not err_rows:
            print(
                f"[RECORD] no validation-error rows for '{record_name}' — "
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
            row_count_override=len(err_rows),
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
            data_rows=err_rows,
            include_metadata=False,
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
