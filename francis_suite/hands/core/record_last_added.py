"""
hands/core/record_last_added.py

RecordLastAddedHand implements the <record-last-added> tag.
Shows the last row added to a record collection — useful for debugging.

Usage in XML:
    <record-last-added from="propiedadesRecords"/>
"""

from __future__ import annotations
import json
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.core.records import FRecord
from francis_suite.core.expressions import FrancisExpression
from francis_suite.hands.base import AbstractHand


@hand(tag="record-last-added")
class RecordLastAddedHand(AbstractHand):
    """
    Shows the last row added to a record collection.
    Useful for debugging inside loops — verify data before continuing.

    Attributes:
        from (required): name of the record collection.

    Returns:
        FEmptyVariable always.

    Example:
        <record-add to="productosRecords">...</record-add>
        <record-last-added from="productosRecords"/>
        <!-- prints the last added row as JSON -->
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

        if record.is_empty():
            print(f"[RECORD] '{record_name}' — no rows added yet")
            return FEmptyVariable()

        last = record.last_row
        print(f"[RECORD] '{record_name}' — last added row ({record.count} total):")
        print(json.dumps(last, ensure_ascii=False, indent=2, default=str))

        return FEmptyVariable()
