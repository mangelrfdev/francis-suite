"""
hands/core/else_.py

ElseHand implements the <else> tag.
Executes children when the preceding <if> condition was false.

Usage in XML:
    <if condition="${stock} > 0">
        <box-def name="status">In Stock</box-def>
    </if>
    <else>
        <box-def name="status">Out of Stock</box-def>
    </else>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand

_LAST_IF_KEY = "__last_if__"


@hand(tag="else")
class ElseHand(AbstractHand):
    """
    Executes children when the preceding <if> condition was false.
    Must be used immediately after an <if> block.

    Returns:
        Result of children if preceding <if> was false,
        FEmptyVariable otherwise.
    """

    def execute(self) -> FVariable:
        last_if = self.context.get(_LAST_IF_KEY)

        if last_if.is_empty():
            raise RuntimeError(
                "<else> must be used immediately after an <if> block."
            )

        if last_if.to_string() == "false":
            # Clear the flag so it can't be triggered twice
            from francis_suite.core.variables import FEmptyVariable as FEV
            self.context.set(_LAST_IF_KEY, FEV())
            return self.execute_children()

        return FEmptyVariable()