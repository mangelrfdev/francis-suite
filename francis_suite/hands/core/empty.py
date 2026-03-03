"""
hands/core/empty.py

EmptyHand implements the <empty> tag.
Returns an empty variable. Used to produce no output explicitly.

Usage in XML:
    <empty/>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="empty")
class EmptyHand(AbstractHand):
    """
    Returns FEmptyVariable. Produces no output.

    Example:
        <box-def var="nada">
            <empty/>
        </box-def>
    """

    def execute(self) -> FVariable:
        return FEmptyVariable()