"""
hands/core/log.py

LogHand implements the <log> tag.
Prints a message to the console during workflow execution.
Sensitive variables are automatically masked in the output.

Usage in XML:
    <log>Hello world</log>
    <log>${ciudad}</log>
    <log>${api_key}</log>        — shows ***masked***
    <log level="error">Something went wrong</log>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable
from francis_suite.core.expressions import FrancisExpression
from francis_suite.hands.base import AbstractHand


VALID_LEVELS = ("info", "debug", "warning", "error")


@hand(tag="log")
class LogHand(AbstractHand):
    """
    Prints a message to stdout during workflow execution.
    Sensitive variables are automatically masked — shows *** instead of real value.

    Attributes:
        level (optional): info | debug | warning | error. Default: info.

    Returns:
        FNodeVariable with the real message (unmasked) — for pipeline use.
        The printed output uses masked values for sensitive variables.

    Examples:
        <log>Scraping started</log>
        <log>Ciudad: ${ciudad}</log>
        <log>API Key: ${api_key}</log>   — prints: API Key: *******xyz
        <log level="error">Something failed</log>
    """

    def execute(self) -> FVariable:
        level = self.attr("level", default="info").lower()

        if level not in VALID_LEVELS:
            raise ValueError(
                f"<log> invalid level '{level}'. "
                f"Valid options: {', '.join(VALID_LEVELS)}"
            )

        engine = FrancisExpression(self.context)

        if self.has_children():
            # execute children once — get both real and display values
            result          = self.execute_children()
            real_message    = result.to_string()
            display_message = result.to_display()
        else:
            raw = self.get_body_text()
            # resolve with real values for pipeline use
            real_message    = engine.resolve(raw) if raw else ""
            # resolve with display values for printing
            display_message = engine.resolve_display(raw) if raw else ""

        self._print(level, display_message)

        # return real value so pipeline can use it
        return FNodeVariable(real_message)

    def _print(self, level: str, message: str) -> None:
        prefix = {
            "info":    "[INFO]   ",
            "debug":   "[DEBUG]  ",
            "warning": "[WARNING]",
            "error":   "[ERROR]  ",
        }[level]
        print(f"{prefix} {message}")
