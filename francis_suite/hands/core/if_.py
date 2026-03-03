from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.core.expressions import FrancisExpression
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
        engine = FrancisExpression(self.context)

        try:
            result = engine.evaluate(condition)
            if isinstance(result, str):
                if bool(result) and result.lower() not in ("false", "0", "no", "none", ""):
                    return self.execute_children()
            elif bool(result):
                return self.execute_children()
        except Exception:
            pass

        return FEmptyVariable()