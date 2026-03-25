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
from francis_suite.core.records import FRecord, FRecordSchema, FRecordGroup, FRecordField
from francis_suite.core.expressions import FrancisExpression
from francis_suite.hands.base import AbstractHand


@hand(tag="record-create")
class RecordCreateHand(AbstractHand):
    """
    Defines a record schema and creates an empty FRecord in the global context.
    The record lives as a shared-box and is accessible by name everywhere.

    Attributes:
        name (required): name of the record collection.

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

        <record-export-attr name="...">value</record-export-attr> — optional; key/value for every record-save (body supports ${})
        <record-export-system name="session_id"/> — include session id at save time (same idea as xml-include-root-session-id)
        <record-export-system name="francis_suite_version"/> — framework version string
        <record-export-system name="exported_at"/> — UTC ISO timestamp at save time
        Legacy aliases: <xml-root-attr>, <xml-root-system> (same semantics; name is historical)

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

        def _mark_export_system(name_raw: str) -> None:
            key = engine.resolve(name_raw).strip().lower()
            if key in ("session_id", "session-id"):
                schema.export_want_session_id = True
            elif key in ("francis_suite_version", "francis-version", "francis_version"):
                schema.export_want_francis_version = True
            elif key in ("exported_at", "exported-at", "generated_at"):
                schema.export_want_exported_at = True

        for child in by_tag["record-export-attr"]:
            schema.export_custom_attrs.append((child.require_attr("name"), child.text or ""))
        for child in by_tag["xml-root-attr"]:
            schema.export_custom_attrs.append((child.require_attr("name"), child.text or ""))
        for child in by_tag["record-export-system"]:
            _mark_export_system(child.require_attr("name"))
        for child in by_tag["xml-root-system"]:
            _mark_export_system(child.require_attr("name"))

        record = FRecord(schema=schema)
        self.context.set_shared_box(name, record)

        meta_info = " with public metadata" if schema.has_public_metadata else ""
        key_info = f", record-key={len(schema.record_key_keys)} field(s)" if schema.record_key_keys else ""
        print(f"[RECORD] created '{name}' with {len(schema.groups)} group(s){meta_info}{key_info}")
        return FEmptyVariable()
