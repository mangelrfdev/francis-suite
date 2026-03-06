"""
hands/core/loop_body.py

LoopBodyHand implements the <loop-body> tag.
Defines the logic for each iteration inside <loop>.
Never executed directly — handled by LoopHand.
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="loop-body")
class LoopBodyHand(AbstractHand):
    """
    Placeholder for <loop-body> tag.
    Never executed directly — always handled by LoopHand.
    """

    def execute(self) -> FVariable:
        raise RuntimeError(
            "<loop-body> cannot be used outside of a <loop> block."
        )