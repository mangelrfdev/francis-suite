"""
hands/core/if_.py

IfHand implements the <if> tag.
Executes children only if the condition evaluates to true.
Stores result in context for <else> to read.

Usage in XML:
    <if condition="${precio} > 100">
        <log>Precio alto</log>
    </if>
    <else>
        <log>Precio normal</log>
    </else>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable, FNodeVariable
from francis_suite.core.expressions import FrancisExpression
from francis_suite.hands.base import AbstractHand

# Context key to communicate if result to else
_LAST_IF_KEY = "__last_if__"


@hand(tag="if")
class IfHand(AbstractHand):
    """
    Conditionally executes children based on a condition.
    Stores result in context so <else> can read it.

    Attributes:
        condition (required): expression that evaluates to true or false.

    Returns:
        Result of children if condition is true, FEmptyVariable otherwise.
    """

    def execute(self) -> FVariable:
        condition = self.require_attr("condition")
        engine = FrancisExpression(self.context)

        try:
            result = engine.evaluate(condition)
            if isinstance(result, str):
                condition_met = result.lower() not in ("false", "0", "no", "none", "")
            else:
                condition_met = bool(result)
        except Exception:
            condition_met = False

        # Store result for <else>
        self.context.set(_LAST_IF_KEY, FNodeVariable("true" if condition_met else "false"))

        if condition_met:
            return self.execute_children()

        return FEmptyVariable()