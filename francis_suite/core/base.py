"""
core/base.py

FVariable — the base class for all Francis Suite variables.
Lives here to avoid circular imports between variables.py and records.py.

Both variables.py and records.py import FVariable from this module.
This ensures there is only one FVariable class in the entire system.
"""

from __future__ import annotations
from abc import ABC, abstractmethod


class FVariable(ABC):
    """
    Base class for all Francis Suite variables.

    Every value that flows through the engine is an FVariable.
    Subclasses must implement all four abstract methods.

    Implementations:
        FNodeVariable  — a single value (string, bytes, number)
        FListVariable  — a list of FVariables
        FEmptyVariable — absence of a value (singleton)
        FRecord        — a structured collection of rows with schema
    """

    @abstractmethod
    def to_string(self) -> str:
        """
        Return the real string value.
        Used internally by the engine — never masked.
        """

    @abstractmethod
    def to_display(self) -> str:
        """
        Return the display string value.
        Used by logs and UI — sensitive values are masked here.
        """

    @abstractmethod
    def to_list(self) -> list:
        """Return list representation of the variable."""

    @abstractmethod
    def is_empty(self) -> bool:
        """Return True if variable has no meaningful value."""

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.to_string()!r})"
