"""
hands/core/text_format.py

TextFormatHand implements the <text-format> tag.
Interpolates variables from context into a text template.

Usage in XML:
    <box-def name="mensaje">
        <text-format>Hola ${nombre}, tienes ${edad} años</text-format>
    </box-def>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FEmptyVariable
from francis_suite.core.expressions import FrancisExpression
from francis_suite.hands.base import AbstractHand


@hand(tag="text-format")
class TextFormatHand(AbstractHand):
    """
    Interpolates context variables into a text template.

    Replaces ${varname} expressions with their values from context.
    If a variable is not found, the expression is left as-is.

    Returns:
        FNodeVariable with the interpolated text.

    Example:
        <text-format>Hello ${name}, you have ${count} messages</text-format>
    """

    def execute(self) -> FVariable:
        if self.has_children():
            template = self.execute_children().to_string()
        else:
            template = self.resolve_body_text()

        if not template:
            return FEmptyVariable()

        return FNodeVariable(template)