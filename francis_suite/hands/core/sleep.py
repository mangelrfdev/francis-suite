"""
hands/core/sleep.py

SleepHand implements the <sleep> tag.
Pauses workflow execution for a specified number of seconds.

Usage in XML:
    <sleep seconds="2"/>
    <sleep seconds="0.5"/>
"""

from __future__ import annotations
import time
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="sleep")
class SleepHand(AbstractHand):
    """
    Pauses execution for a given number of seconds.

    Attributes:
        seconds (required): how long to sleep. Accepts decimals.

    Returns:
        FEmptyVariable — sleep produces no meaningful result.

    Example:
        <sleep seconds="1.5"/>
    """

    def execute(self) -> FVariable:
        raw = self.require_attr("seconds")

        try:
            seconds = float(raw)
        except ValueError:
            raise ValueError(
                f"<sleep> attribute 'seconds' must be a number, got '{raw}'"
            )

        if seconds < 0:
            raise ValueError(
                f"<sleep> attribute 'seconds' must be >= 0, got {seconds}"
            )

        time.sleep(seconds)
        return FEmptyVariable()