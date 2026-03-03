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
from francis_suite.hands.base import AbstractHand


MAX_ITERATIONS = 10_000  # safety limit to prevent infinite loops


@hand(tag="while")
class WhileHand(AbstractHand):
    """
    Executes children repeatedly while a condition is true.

    Attributes:
        condition (required): expression evaluated before each iteration.

    Returns:
        FEmptyVariable — while produces no direct output.

    Example:
        <while condition="${count} &lt; 3">
            <log>iterating</log>
        </while>
    """

    def execute(self) -> FVariable:
        condition = self.require_attr("condition")
        iterations = 0

        while self._evaluate(condition):
            if iterations >= MAX_ITERATIONS:
                raise RuntimeError(
                    f"<while> exceeded maximum iterations ({MAX_ITERATIONS}). "
                    f"Possible infinite loop detected."
                )
            with self.context.new_scope():
                self.execute_children()
            iterations += 1

        return FEmptyVariable()

    def _evaluate(self, condition: str) -> bool:
        """Evaluate a condition string safely."""
        condition = condition.strip()

        if not condition:
            return False

        try:
            result = eval(condition, {"__builtins__": {}}, {})
            return bool(result)
        except Exception:
            pass

        return condition.lower() not in ("false", "0", "no", "none", "")