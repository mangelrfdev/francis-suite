"""hands/core/sleep_min.py"""
from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable
from francis_suite.hands.base import AbstractHand

@hand(tag="sleep-min")
class SleepMinHand(AbstractHand):
    def execute(self) -> FVariable:
        raise RuntimeError("<sleep-min> cannot be used outside of a <sleep> block.")