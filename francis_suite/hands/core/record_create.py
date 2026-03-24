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
"""

from __future__ import annotations
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

    Notes:
        - <record-metadata> and <record-set-group> can appear in any order
        - Public metadata only appears in output when include-metadata="true" in record-save
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

        for child in self.node.children:

            # --- public metadata ---
            if child.tag == "record-metadata":
                for meta_node in child.children:

                    if meta_node.tag == "metadata-field":
                        field_name  = meta_node.require_attr("name")
                        field_value = meta_node.text.strip() if meta_node.text and meta_node.text.strip() else None
                        # resolve variables if present
                        if field_value:
                            field_value = engine.resolve(field_value)
                        schema.add_public_metadata_field(name=field_name, value=field_value)

                    elif meta_node.tag == "metadata-add-field":
                        field_name  = meta_node.require_attr("name")
                        field_value = engine.resolve(meta_node.text or "")
                        schema.add_public_metadata_field(name=field_name, value=field_value)

            # --- record groups ---
            elif child.tag == "record-set-group":
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

        record = FRecord(schema=schema)
        self.context.set_shared_box(name, record)

        meta_info = " with public metadata" if schema.has_public_metadata else ""
        print(f"[RECORD] created '{name}' with {len(schema.groups)} group(s){meta_info}")
        return FEmptyVariable()
