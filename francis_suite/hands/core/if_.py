"""
hands/core/if_.py

IfHand implements the <if> tag.
Executes children only if the condition evaluates to true.

Usage in XML:
    <if condition="${precio} > 100">
        <log>Precio alto</log>
    </if>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="if")
class IfHand(AbstractHand):
    """
    Conditionally executes children based on a condition.

    Attributes:
        condition (required): expression that evaluates to true or false.

    Returns:
        Result of children if condition is true, FEmptyVariable otherwise.

    Example:
        <if condition="${value} > 0">
            <log>Positive</log>
        </if>
    """

    def execute(self) -> FVariable:
        condition = self.require_attr("condition")

        if self._evaluate(condition):
            return self.execute_children()

        return FEmptyVariable()

    def _evaluate(self, condition: str) -> bool:
        """
        Evaluate a condition string.
        Supports simple comparisons: ==, !=, >, <, >=, <=
        Also supports plain truthy string values.
        """
        condition = condition.strip()

        # Empty condition is always false
        if not condition:
            return False

        # Try evaluating as a Python expression safely
        try:
            result = eval(condition, {"__builtins__": {}}, {})
            return bool(result)
        except Exception:
            pass

        # Fallback: treat as truthy string
        return condition.lower() not in ("false", "0", "no", "none", "")