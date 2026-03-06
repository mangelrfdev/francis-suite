"""
hands/core/log.py

LogHand implements the <log> tag.
Prints a message to the console during workflow execution.

Usage in XML:
    <log>Hello world</log>
    <log>${mi-variable}</log>
    <log level="error">Something went wrong</log>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable
from francis_suite.hands.base import AbstractHand


VALID_LEVELS = ("info", "debug", "warning", "error")


@hand(tag="log")
class LogHand(AbstractHand):
    """
    Prints a message to stdout during workflow execution.

    Attributes:
        level (optional): info | debug | warning | error. Default: info.

    Returns:
        FNodeVariable with the message that was logged.

    Example:
        <log>Scraping started</log>
        <log level="error">Something failed</log>
    """

    def execute(self) -> FVariable:
        level = self.attr("level", default="info").lower()

        if level not in VALID_LEVELS:
            raise ValueError(
                f"<log> invalid level '{level}'. "
                f"Valid options: {', '.join(VALID_LEVELS)}"
            )

        if self.has_children():
            message = self.execute_children().to_string()
        else:
            message = self.resolve_body_text()

        self._print(level, message)
        return FNodeVariable(message)

    def _print(self, level: str, message: str) -> None:
        prefix = {
            "info":    "[INFO]   ",
            "debug":   "[DEBUG]  ",
            "warning": "[WARNING]",
            "error":   "[ERROR]  ",
        }[level]
        print(f"{prefix} {message}")