"""
hands/core/record_create.py

RecordCreateHand implements the <record-create> tag.
Defines a record schema and creates an empty FRecord in the global context.

Usage in XML:
    <!-- without metadata -->
    <record-create name="propiedadesRecords">
        <record-set-group name="propiedad" required="true">
            <record-set-field name="titulo" type="string"  required="true"/>
            <record-set-field name="precio" type="integer" required="true"/>
        </record-set-group>
    </record-create>

    <!-- with public metadata — order does not matter -->
    <record-create name="propiedadesRecords">
        <record-metadata>
            <metadata-field name="fuente">Portal Inmobiliario</metadata-field>
            <metadata-field name="rows_completados"/>
            <metadata-add-field name="ciudad">${ciudad}</metadata-add-field>
        </record-metadata>
        <record-set-group name="propiedad" required="true">
            <record-set-field name="titulo" type="string"  required="true"/>
            <record-set-field name="precio" type="integer" required="true"/>
        </record-set-group>
    </record-create>

    <!-- optional duplicate detection — key fields must exist in a record-set-group -->
    <record-create name="propiedadesRecords">
        <record-key>
            <key-field name="codigo"/>
        </record-key>
        <record-set-group name="propiedad" required="true">
            <record-set-field name="codigo" type="string" required="true"/>
            <record-set-field name="titulo" type="string" required="true"/>
        </record-set-group>
    </record-create>
"""

from __future__ import annotations
from collections import defaultdict

from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.core.records import (
    FRecord,
    FRecordSchema,
    FRecordGroup,
    FRecordField,
    ExportCustomAttrSpec,
    ExportRootAttrSpec,
    ExportRowAttrSpec,
    ExportSystemAttrSpec,
)
from francis_suite.core.expressions import FrancisExpression
from francis_suite.hands.base import AbstractHand


@hand(tag="record-create")
class RecordCreateHand(AbstractHand):
    """
    Defines a record schema and creates an empty FRecord in the global context.
    The record lives as a shared-box and is accessible by name everywhere.

    Attributes:
        name (required): name of the record collection.
        record-validation (optional): strict (default) — invalid row raises; collect-errors —
            skip invalid rows, store for record-save-validation-errors and metadata counts.

    Child tags:
        <record-metadata> — optional, declares public metadata fields
            <metadata-field name="...">fixed value</metadata-field>
            <metadata-field name="..."/>   — auto-computed field
            <metadata-add-field name="...">${variable}</metadata-add-field>

        <record-set-group name="..." required="true|false">
            <record-set-field name="..." type="..." required="true|false"
                              null-if-empty="true|false" precision="N"/>
        </record-set-group>

        <record-key> — optional, duplicate detection via stable hash of listed fields
            <key-field name="fieldName"/>  — bare name if unique across groups
            <key-field name="group.field"/> — qualified if ambiguous

        <record-export-attr name="..." required="false" show-attribute="true">value</record-export-attr>
        <record-export-root-attr name="..." required="false" show-attribute="true">value</record-export-root-attr>
            — merged into _export (json, etc.) and <Records> in XML
        <record-export-system name="session_id|francis_suite_version|exported_at|total_records|status_process"
                              show-attribute="true"/>
        <record-journal path="..." fsync="false"/> — append one NDJSON line per successful record-add

        Legacy aliases: <xml-root-attr> (same as record-export-attr), <xml-root-system> (export-system)

        XML-focused (legacy):
        <record-xml-root-attr name="...">value</record-xml-root-attr> — only <Records> attrs in XML, not JSON _export
        <record-xml-record-attr name="..." from-field="group.field"/> — per-row on <record>
        <record-export-row-attr> — alias for record-xml-record-attr semantics
        required defaults to false when omitted.

    Notes:
        - <record-metadata> and <record-set-group> can appear in any order
        - Public metadata only appears in output when include-metadata="true" in record-save
        - record-export-* is applied on every record-save; formats that cannot embed extras simply omit them
        - Private metadata is always generated automatically

    Auto-computed metadata fields (use without value):
        total_rows, rows_completados, rows_con_campos_vacios, rows_fallidos,
        porcentaje_completitud, duracion_segundos, rows_por_segundo,
        session_id, workflow_path, francis_suite_version, hostname,
        sistema_operativo, python_version, status, error, inicio, fin

    Field types:
        string, integer, decimal, boolean, date, datetime, url, email, uuid

    Returns:
        FEmptyVariable — the record lives in the global context as a shared-box.
    """

    def execute(self) -> FVariable:
        engine = FrancisExpression(self.context)
        name   = self.require_attr("name")
        schema = FRecordSchema(name=name)

        rv = (self.node.get_attr("record-validation", "strict") or "strict").strip().lower()
        if rv in ("strict", "collect-errors"):
            schema.record_validation_mode = rv
        else:
            raise ValueError(
                f"[RECORD] invalid record-validation '{rv}'. "
                "Use 'strict' (default) or 'collect-errors'."
            )

        by_tag: dict[str, list] = defaultdict(list)
        for child in self.node.children:
            by_tag[child.tag].append(child)

        # --- public metadata (any order in XML) ---
        for child in by_tag["record-metadata"]:
            for meta_node in child.children:

                if meta_node.tag == "metadata-field":
                    field_name  = meta_node.require_attr("name")
                    field_value = meta_node.text.strip() if meta_node.text and meta_node.text.strip() else None
                    if field_value:
                        field_value = engine.resolve(field_value)
                    schema.add_public_metadata_field(name=field_name, value=field_value)

                elif meta_node.tag == "metadata-add-field":
                    field_name  = meta_node.require_attr("name")
                    field_value = engine.resolve(meta_node.text or "")
                    schema.add_public_metadata_field(name=field_name, value=field_value)

        # --- record groups (must exist before <record-key> validation) ---
        for child in by_tag["record-set-group"]:
            group_name     = child.require_attr("name")
            group_required = child.get_attr("required", "true").lower() == "true"
            group          = FRecordGroup(name=group_name, required=group_required)

            for field_node in child.children:
                if field_node.tag != "record-set-field":
                    continue

                field_name     = field_node.require_attr("name")
                field_type     = field_node.require_attr("type")
                field_required = field_node.get_attr("required", "true").lower() == "true"
                null_if_empty  = field_node.get_attr("null-if-empty", "false").lower() == "true"
                precision      = field_node.get_attr("precision", None)

                field = FRecordField(
                    name          = field_name,
                    field_type    = field_type,
                    required      = field_required,
                    null_if_empty = null_if_empty,
                    precision     = precision,
                )
                group.add_field(field)

            schema.add_group(group)

        # --- record-key (optional) ---
        for child in by_tag["record-key"]:
            for key_node in child.children:
                if key_node.tag != "key-field":
                    continue
                schema.add_record_key_field(key_node.require_attr("name"))

        def _truthy_attr(node, name: str, default: str = "false") -> bool:
            v = (node.get_attr(name, default) or "").strip().lower()
            return v in ("true", "1", "yes")

        def _show_attribute(node) -> bool:
            v = (node.get_attr("show-attribute", "true") or "true").strip().lower()
            return v not in ("false", "0", "no")

        for child in by_tag.get("record-journal", []):
            schema.journal_path = engine.resolve(child.require_attr("path"))
            schema.journal_fsync = _truthy_attr(child, "fsync")
            break

        for child in by_tag["record-export-attr"]:
            schema.export_custom_specs.append(
                ExportCustomAttrSpec(
                    name_raw=child.require_attr("name"),
                    value_raw=child.text or "",
                    required=_truthy_attr(child, "required"),
                    show_attribute=_show_attribute(child),
                )
            )
        for child in by_tag["xml-root-attr"]:
            schema.export_custom_specs.append(
                ExportCustomAttrSpec(
                    name_raw=child.require_attr("name"),
                    value_raw=child.text or "",
                    required=_truthy_attr(child, "required"),
                    show_attribute=_show_attribute(child),
                )
            )

        for child in by_tag.get("record-export-root-attr", []):
            schema.export_root_specs.append(
                ExportRootAttrSpec(
                    name_raw=child.require_attr("name"),
                    value_raw=child.text or "",
                    required=_truthy_attr(child, "required"),
                    show_attribute=_show_attribute(child),
                    xml_only=False,
                )
            )

        for child in by_tag["record-xml-root-attr"]:
            schema.export_root_specs.append(
                ExportRootAttrSpec(
                    name_raw=child.require_attr("name"),
                    value_raw=child.text or "",
                    required=_truthy_attr(child, "required"),
                    show_attribute=_show_attribute(child),
                    xml_only=True,
                )
            )

        def _append_row_attr(child) -> None:
            req = _truthy_attr(child, "required")
            ff_raw = child.get_attr("from-field", "").strip() or None
            canonical_ff = schema.resolve_flat_field_path(ff_raw) if ff_raw else None
            body = child.text or ""
            if req and not canonical_ff and not body.strip():
                raise ValueError(
                    "[RECORD] record row attr: use from-field or a non-empty body when required=true"
                )
            schema.export_row_specs.append(
                ExportRowAttrSpec(
                    name_raw=child.require_attr("name"),
                    value_raw=body,
                    from_field=canonical_ff,
                    required=req,
                    show_attribute=_show_attribute(child),
                )
            )

        for child in by_tag.get("record-export-row-attr", []):
            _append_row_attr(child)
        for child in by_tag["record-xml-record-attr"]:
            _append_row_attr(child)

        for child in by_tag["record-export-system"]:
            schema.export_system_specs.append(
                ExportSystemAttrSpec(
                    name_raw=child.require_attr("name"),
                    show_attribute=_show_attribute(child),
                )
            )
        for child in by_tag["xml-root-system"]:
            schema.export_system_specs.append(
                ExportSystemAttrSpec(
                    name_raw=child.require_attr("name"),
                    show_attribute=_show_attribute(child),
                )
            )

        record = FRecord(schema=schema)
        self.context.set_shared_box(name, record)
        if schema.journal_path:
            record.write_journal_header_if_needed(self.session)

        meta_info = " with public metadata" if schema.has_public_metadata else ""
        key_info = f", record-key={len(schema.record_key_keys)} field(s)" if schema.record_key_keys else ""
        val_info = "" if schema.record_validation_mode == "strict" else f", validation={schema.record_validation_mode}"
        print(f"[RECORD] created '{name}' with {len(schema.groups)} group(s){meta_info}{key_info}{val_info}")
        return FEmptyVariable()
