"""
hands/core/sleep.py

SleepHand implements the <sleep> tag.
Pauses workflow execution for a fixed or randomized time in milliseconds.

Usage in XML:
    <!-- Fixed -->
    <sleep ms="1000"/>

    <!-- Random with human-like behavior -->
    <sleep>
        <sleep-min>1000</sleep-min>
        <sleep-avg>3000</sleep-avg>
        <sleep-max>10000</sleep-max>
    </sleep>
"""

from __future__ import annotations
import time
import random
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand
from francis_suite.core.expressions import FrancisExpression

@hand(tag="sleep")
class SleepHand(AbstractHand):
    """
    Pauses execution for a fixed or randomized duration in milliseconds.

    Attributes:
        ms (optional): fixed duration in milliseconds.

    Child tags (optional — for human-like random sleep):
        <sleep-min> — minimum duration in milliseconds (required if variable)
        <sleep-max> — maximum duration in milliseconds (required if variable)
        <sleep-avg> — average duration in milliseconds (optional, default: midpoint)

    Returns:
        FEmptyVariable — sleep produces no meaningful result.

    Examples:
        <!-- Fixed -->
        <sleep ms="1000"/>

        <!-- Random -->
        <sleep>
            <sleep-min>1000</sleep-min>
            <sleep-avg>3000</sleep-avg>
            <sleep-max>10000</sleep-max>
        </sleep>
    """

    def execute(self) -> FVariable:
        engine  = FrancisExpression(self.context)
        min_node = self._node.first_child_by_tag("sleep-min")
        max_node = self._node.first_child_by_tag("sleep-max")
        avg_node = self._node.first_child_by_tag("sleep-avg")

        if min_node is not None or max_node is not None:
            # Variable mode
            if min_node is None or max_node is None:
                raise ValueError(
                    "<sleep> variable mode requires both <sleep-min> and <sleep-max>."
                )

            ms_min = self._parse_ms(self.resolve_child_text(min_node), "sleep-min")
            ms_max = self._parse_ms(self.resolve_child_text(max_node), "sleep-max")

            if ms_min > ms_max:
                raise ValueError(
                    f"<sleep> sleep-min ({ms_min}) must be <= sleep-max ({ms_max})."
                )

            if avg_node is not None:
                ms_avg = self._parse_ms(self.resolve_child_text(avg_node), "sleep-avg")
                ms_avg = max(ms_min, min(ms_max, ms_avg))
            else:
                ms_avg = (ms_min + ms_max) / 2

            ms = self._random_gaussian(ms_min, ms_avg, ms_max)

        else:
            raw = engine.resolve(self.require_attr("ms"))
            ms = self._parse_ms(raw, "ms")

        time.sleep(ms / 1000)
        return FEmptyVariable()

    def _parse_ms(self, value: str, attr: str) -> float:
        try:
            ms = float(value)
        except ValueError:
            raise ValueError(
                f"<sleep> '{attr}' must be a number in milliseconds, got '{value}'"
            )
        if ms < 0:
            raise ValueError(
                f"<sleep> '{attr}' must be >= 0, got {ms}"
            )
        return ms

    def _random_gaussian(self, ms_min: float, ms_avg: float, ms_max: float) -> float:
        """
        Generate a random value centered around ms_avg using gaussian distribution,
        truncated between ms_min and ms_max.
        """
        sigma = (ms_max - ms_min) / 6  # 99.7% of values within range
        for _ in range(10):
            value = random.gauss(ms_avg, sigma)
            if ms_min <= value <= ms_max:
                return value
        return ms_avg  # fallback

    def resolve_child_text(self, node) -> str:
        """Resolve text content of a child node."""
        if node.has_children():
            return self.execute_child(node).to_string()
        from francis_suite.core.expressions import FrancisExpression
        engine = FrancisExpression(self.context)
        return engine.resolve(node.text or "")