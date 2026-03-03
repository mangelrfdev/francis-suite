"""
hands/core/exit_.py

ExitHand implements the <exit> tag.
Stops workflow execution immediately.

Usage in XML:
    <if condition="${error.isNotEmpty()}">
        <log>Error critico</log>
        <exit/>
    </if>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


class ExitWorkflow(Exception):
    """Raised by <exit> to stop workflow execution."""
    pass


@hand(tag="exit")
class ExitHand(AbstractHand):
    """
    Stops workflow execution immediately.
    No attributes required.

    Returns:
        Never returns — raises ExitWorkflow exception.

    Example:
        <exit/>
    """

    def execute(self) -> FVariable:
        raise ExitWorkflow("Workflow stopped by <exit>")