"""hands/core/sleep_max.py"""
from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable
from francis_suite.hands.base import AbstractHand

@hand(tag="sleep-max")
class SleepMaxHand(AbstractHand):
    def execute(self) -> FVariable:
        raise RuntimeError("<sleep-max> cannot be used outside of a <sleep> block.")