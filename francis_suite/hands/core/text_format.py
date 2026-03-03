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
import re
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FEmptyVariable
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

    # Matches ${varname} expressions
    VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")

    def execute(self) -> FVariable:
        # Get template from body text or children
        if self.has_children():
            template = self.execute_children().to_string()
        else:
            template = self.get_body_text()

        if not template:
            return FEmptyVariable()

        result = self._interpolate(template)
        return FNodeVariable(result)

    def _interpolate(self, template: str) -> str:
        """Replace ${varname} with values from context."""
        def replace(match: re.Match) -> str:
            var_name = match.group(1).strip()
            value = self.context.get(var_name)
            if value.is_empty():
                return match.group(0)  # leave as-is if not found
            return value.to_string()

        return self.VAR_PATTERN.sub(replace, template)