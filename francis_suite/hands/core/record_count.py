"""
hands/core/record_count.py

RecordCountHand implements the <record-count> tag.
Returns the number of rows in a record collection.

Usage in XML:
    <box-def name="total">
        <record-count from="propiedadesRecords"/>
    </box-def>
    <log>Total propiedades: ${total}</log>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable
from francis_suite.core.records import FRecord
from francis_suite.core.expressions import FrancisExpression
from francis_suite.hands.base import AbstractHand


@hand(tag="record-count")
class RecordCountHand(AbstractHand):
    """
    Returns the number of rows in a record collection as a string.

    Attributes:
        from (required): name of the record collection.

    Returns:
        FNodeVariable with the count as string.

    Example:
        <box-def name="total">
            <record-count from="productosRecords"/>
        </box-def>
        <log>Total productos: ${total}</log>

        <!-- use in condition -->
        <if condition="${total.toInt()} > 0">
            <record-save from="productosRecords" format="json" path="output/productos.json"/>
        </if>
    """

    def execute(self) -> FVariable:
        engine      = FrancisExpression(self.context)
        record_name = engine.resolve(self.require_attr("from"))

        record = self.context.get_shared_box(record_name)

        if not isinstance(record, FRecord):
            raise ValueError(
                f"[RECORD] record '{record_name}' not found. "
                f"Make sure <record-create name=\"{record_name}\"> runs first."
            )

        count = record.count
        print(f"[RECORD] '{record_name}' — {count} rows")
        return FNodeVariable(str(count))
