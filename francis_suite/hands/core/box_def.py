"""
hands/core/box_def.py

BoxDefHand implements the <box-def> tag.
Executes its children and stores the result in a context variable.

Usage in XML:
    <box-def name="pagina">
        <http-call url="https://ejemplo.com"/>
    </box-def>

    <log>${pagina}</log>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="box-def")
class BoxDefHand(AbstractHand):
    """
    Executes child hands and stores the result in a named variable.

    Attributes:
        name (required): name of the variable to store the result in.

    Returns:
        The result of the last child hand.

    Example:
        <box-def name="titulo">
            <http-call url="https://ejemplo.com"/>
        </box-def>
    """

    def execute(self) -> FVariable:
        var_name = self.require_attr("name")

        if self.has_children():
            result = self.execute_children()
        else:
            result = FEmptyVariable()

        self.context.set(var_name, result)
        return result