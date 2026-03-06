"""
hands/core/while_.py

WhileHand implements the <while> tag.
Executes children repeatedly while a condition is true.

Usage in XML:
    <while condition="${counter} &lt; 5">
        <log>${counter}</log>
    </while>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.core.expressions import FrancisExpression
from francis_suite.hands.base import AbstractHand


MAX_ITERATIONS = 10_000


@hand(tag="while")
class WhileHand(AbstractHand):
    """
    Executes children repeatedly while a condition is true.

    Attributes:
        condition (required): expression evaluated before each iteration.
        max-loops (optional): maximum number of iterations. Default: 10_000.

    Returns:
        FEmptyVariable — while produces no direct output.
    """

    def execute(self) -> FVariable:
        condition = self.require_attr("condition")
        max_loops = self.attr("max-loops", None)
        max_loops = int(max_loops) if max_loops is not None else MAX_ITERATIONS

        engine = FrancisExpression(self.context)
        iterations = 0

        while self._evaluate(condition, engine):
            if iterations >= max_loops:
                raise RuntimeError(
                    f"<while> exceeded maximum iterations ({max_loops}). "
                    f"Possible infinite loop detected."
                )
            with self.context.new_scope():
                self.execute_children()
            iterations += 1

        return FEmptyVariable()

    def _evaluate(self, condition: str, engine: FrancisExpression) -> bool:
        condition = condition.strip()
        if not condition:
            return False
        try:
            result = engine.evaluate(condition)
            if isinstance(result, str):
                return result.lower() not in ("false", "0", "no", "none", "")
            return bool(result)
        except Exception:
            return False