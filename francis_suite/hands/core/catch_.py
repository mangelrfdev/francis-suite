"""
hands/core/catch_.py

CatchHand implements the <catch> tag.
This hand is never executed directly — it is handled by TryHand.
It must be registered so the parser does not reject it as unknown.

Usage in XML:
    <try>
        <http-call url="https://example.com"/>
        <catch>
            <log>Something went wrong</log>
        </catch>
    </try>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="catch")
class CatchHand(AbstractHand):
    """
    Placeholder hand for the <catch> tag.
    Never executed directly — always handled by TryHand.
    """

    def execute(self) -> FVariable:
        # This should never be called directly
        raise RuntimeError(
            "<catch> cannot be used outside of a <try> block."
        )