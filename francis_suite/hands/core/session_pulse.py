"""
hands/core/session_pulse.py

SessionPulseHand implements <session-pulse/>.
Resets the silence watchdog without completing another substantive hand.
"""

from __future__ import annotations

from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="session-pulse")
class SessionPulseHand(AbstractHand):
    """
    Marks progress for the silence watchdog (heartbeat-style).

    Use between long-running stretches where no hand completes yet
    (e.g. many internal steps) so silence-limit-ms does not fire incorrectly.

    No attributes.

    Returns:
        FEmptyVariable
    """

    def execute(self) -> FVariable:
        self._session.liveness.record_progress()
        return FEmptyVariable()
