"""
hands/core/loop_list.py

LoopListHand implements the <loop-list> tag.
Defines the list to iterate over inside <loop>.
Never executed directly — handled by LoopHand.
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="loop-list")
class LoopListHand(AbstractHand):
    """
    Placeholder for <loop-list> tag.
    Never executed directly — always handled by LoopHand.
    """

    def execute(self) -> FVariable:
        raise RuntimeError(
            "<loop-list> cannot be used outside of a <loop> block."
        )