"""
hands/core/record_add.py

RecordAddHand implements the <record-add> tag.
Adds a row to an existing FRecord in the global context.

Usage in XML:
    <record-add to="propiedadesRecords">
        <record-add-group name="propiedad">
            <record-add-field name="titulo">${titulo}</record-add-field>
            <record-add-field name="precio">${precio}</record-add-field>
            <record-add-field name="comuna">${comuna}</record-add-field>
        </record-add-group>
    </record-add>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.core.records import FRecord
from francis_suite.core.expressions import FrancisExpression
from francis_suite.hands.base import AbstractHand


@hand(tag="record-add")
class RecordAddHand(AbstractHand):
    """
    Adds a normalized row to an existing FRecord.
    The record must have been created by <record-create> first.

    Attributes:
        to (required): name of the record collection to add to.

    Child tags:
        <record-add-group name="...">
            <record-add-field name="...">value or ${variable}</record-add-field>
        </record-add-group>

    Returns:
        FEmptyVariable always.

    Example:
        <record-add to="productosRecords">
            <record-add-group name="producto">
                <record-add-field name="nombre">${nombre}</record-add-field>
                <record-add-field name="precio">${precio}</record-add-field>
            </record-add-group>
        </record-add>
    """

    def execute(self) -> FVariable:
        engine      = FrancisExpression(self.context)
        record_name = engine.resolve(self.require_attr("to"))

        record = self.context.get_shared_box(record_name)

        if not isinstance(record, FRecord):
            raise ValueError(
                f"[RECORD] record '{record_name}' not found. "
                f"Make sure <record-create name=\"{record_name}\"> runs first."
            )

        # collect raw values from child tags
        raw_row: dict[str, str] = {}

        for group_node in self.node.children:
            if group_node.tag != "record-add-group":
                continue

            group_name = group_node.require_attr("name")

            for field_node in group_node.children:
                if field_node.tag != "record-add-field":
                    continue

                field_name = field_node.require_attr("name")
                raw_value  = engine.resolve(field_node.text or "")

                # store as "group.field" key
                raw_row[f"{group_name}.{field_name}"] = raw_value

        # normalize and add the row
        record.add_row(raw_row)

        return FEmptyVariable()
