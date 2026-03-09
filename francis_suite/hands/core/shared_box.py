"""
hands/core/shared_box.py

SharedBoxHand implements the <shared-box> tag.
Retrieves a shared variable directly from the global scope.

Usage in XML:
    <shared-box name="env"/>

    <box-def name="url">
        <text-format>https://${env}.ejemplo.com</text-format>
    </box-def>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="shared-box")
class SharedBoxHand(AbstractHand):
    """
    Retrieves a shared variable directly from the global scope.

    Unlike <box> which searches from the current scope outward,
    <shared-box> reads directly from the root global scope,
    bypassing any local variables with the same name.

    Attributes:
        name (required): name of the variable to retrieve.

    Returns:
        The FVariable stored in the global scope,
        or FEmptyVariable if not found.

    Example:
        <shared-box name="env"/>
    """

    def execute(self) -> FVariable:
        name = self.require_attr("name")
        return self.context.get_shared_box(name)