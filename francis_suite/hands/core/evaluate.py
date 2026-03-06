"""
hands/core/evaluate.py

EvaluateHand implements the <evaluate> tag.
Evaluates an expression using the FrancisExpression engine
and returns the result. Always store the result in a box.

Usage in XML:
    <box-def name="estaVacio">
        <evaluate>${loro.isEmpty()}</evaluate>
    </box-def>

    <box-def name="total">
        <evaluate>${precio} * ${cantidad}</evaluate>
    </box-def>

    <box-def name="nombre">
        <evaluate>${nombre.toUpperCase()}</evaluate>
    </box-def>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FEmptyVariable
from francis_suite.core.expressions import FrancisExpression
from francis_suite.hands.base import AbstractHand


@hand(tag="evaluate")
class EvaluateHand(AbstractHand):
    """
    Evaluates an expression and returns the result.

    The expression is taken from the body text.
    Supports variable resolution, arithmetic, comparisons,
    logical operators, and method calls.

    Returns:
        FNodeVariable with the result of the expression.
        FEmptyVariable if the expression is empty.

    Example:
        <box-def name="estaVacio">
            <evaluate>${nombre.isEmpty()}</evaluate>
        </box-def>

        <box-def name="total">
            <evaluate>${precio} * ${cantidad}</evaluate>
        </box-def>
    """

    def execute(self) -> FVariable:
        expression = self.resolve_body_text().strip()

        if not expression:
            return FEmptyVariable()

        engine = FrancisExpression(self.context)

        try:
            result = engine.evaluate(expression)
            if result is None:
                return FEmptyVariable()
            return FNodeVariable(str(result))
        except Exception as e:
            raise ValueError(
                f"<evaluate> failed to evaluate '{expression}': {e}"
            ) from e