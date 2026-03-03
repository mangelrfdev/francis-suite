"""
hands/core/case_.py

CaseHand implements the <case> tag.
Executes the first matching <if> child, or <else> if none match.

Usage in XML:
    <case>
        <if condition="${tipo} == 'A'">
            <log>es tipo A</log>
        </if>
        <if condition="${tipo} == 'B'">
            <log>es tipo B</log>
        </if>
        <else>
            <log>tipo desconocido</log>
        </else>
    </case>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable, FNodeVariable
from francis_suite.core.expressions import FrancisExpression
from francis_suite.hands.base import AbstractHand

_LAST_IF_KEY = "__last_if__"


@hand(tag="case")
class CaseHand(AbstractHand):
    """
    Executes the first matching <if> child.
    If no <if> matches, executes <else> if present.

    Child tags:
        <if condition="..."> — condition to evaluate (one or more)
        <else>              — fallback if no condition matches (optional)

    Returns:
        Result of first matching <if>, or <else> if none match.
    """

    def execute(self) -> FVariable:
        engine = FrancisExpression(self.context)
        else_node = self._node.first_child_by_tag("else")
        matched = False
        result: FVariable = FEmptyVariable()

        for child in self._node.children:
            if child.tag == "else":
                continue

            if child.tag == "if":
                if matched:
                    continue

                condition = child.get_attr("condition", "")
                try:
                    evaluated = engine.evaluate(condition)
                    if isinstance(evaluated, str):
                        condition_met = evaluated.lower() not in ("false", "0", "no", "none", "")
                    else:
                        condition_met = bool(evaluated)
                except Exception:
                    condition_met = False

                if condition_met:
                    matched = True
                    result = self.execute_child(child)
            else:
                result = self.execute_child(child)

        # If nothing matched, execute else
        if not matched and else_node is not None:
            for child in else_node.children:
                result = self.execute_child(child)

        # Store last_if result for potential outer else
        self.context.set(
            _LAST_IF_KEY,
            FNodeVariable("true" if matched else "false")
        )

        return result