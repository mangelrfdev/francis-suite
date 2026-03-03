"""
hands/core/box.py

BoxHand implements the <box> tag.
Retrieves a variable from the execution context.

Usage in XML:
    <box name="pagina"/>

    <xpath-extract expression="//h1/text()">
        <box name="xml-page"/>
    </xpath-extract>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="box")
class BoxHand(AbstractHand):
    """
    Retrieves a variable from the execution context by name.

    Attributes:
        name (required): name of the variable to retrieve.

    Returns:
        The FVariable stored under that name, or FEmptyVariable if not found.

    Example:
        <box name="pagina"/>
    """

    def execute(self) -> FVariable:
        var_name = self.require_attr("name")
        return self.context.get(var_name)