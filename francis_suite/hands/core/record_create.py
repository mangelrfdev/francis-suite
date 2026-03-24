"""
hands/core/record_create.py

RecordCreateHand implements the <record-create> tag.
Defines a record schema and creates an empty FRecord in the global context.

Usage in XML:
    <record-create name="propiedadesRecords">
        <record-set-group name="propiedad" required="true">
            <record-set-field name="titulo"  type="string"  required="true"/>
            <record-set-field name="precio"  type="integer" required="true"/>
            <record-set-field name="comuna"  type="string"  required="false" null-if-empty="true"/>
            <record-set-field name="precio_m2" type="decimal" precision="2" required="false"/>
        </record-set-group>
    </record-create>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.core.records import FRecord, FRecordSchema, FRecordGroup, FRecordField
from francis_suite.hands.base import AbstractHand


@hand(tag="record-create")
class RecordCreateHand(AbstractHand):
    """
    Defines a record schema and creates an empty FRecord in the global context.
    The record lives as a shared-box and is accessible by name everywhere.

    Attributes:
        name (required): name of the record collection.

    Child tags:
        <record-set-group name="..." required="true|false">
            <record-set-field name="..." type="..." required="true|false"
                              null-if-empty="true|false" precision="N"/>
        </record-set-group>

    Field types:
        string, integer, decimal, boolean, date, datetime, url, email, uuid

    Returns:
        FEmptyVariable — the record lives in the global context as a shared-box.

    Example:
        <record-create name="productosRecords">
            <record-set-group name="producto" required="true">
                <record-set-field name="id"      type="uuid"    required="true"/>
                <record-set-field name="nombre"  type="string"  required="true"/>
                <record-set-field name="precio"  type="integer" required="true"/>
                <record-set-field name="marca"   type="string"  required="false" null-if-empty="true"/>
            </record-set-group>
        </record-create>
    """

    def execute(self) -> FVariable:
        name = self.require_attr("name")

        schema = FRecordSchema(name=name)

        for group_node in self.node.children:
            if group_node.tag != "record-set-group":
                continue

            group_name     = group_node.require_attr("name")
            group_required = group_node.get_attr("required", "true").lower() == "true"
            group          = FRecordGroup(name=group_name, required=group_required)

            for field_node in group_node.children:
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

        print(f"[RECORD] created '{name}' with {len(schema.groups)} group(s)")
        return FEmptyVariable()
