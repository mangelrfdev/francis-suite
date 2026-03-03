"""
core/variables.py

Variable types used throughout the execution engine.
Every plugin receives and returns FVariable instances.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


class FVariable(ABC):
    """Base class for all Francis Suite variables."""

    @abstractmethod
    def to_string(self) -> str:
        """Return string representation of the variable."""

    @abstractmethod
    def to_list(self) -> list["FVariable"]:
        """Return list representation of the variable."""

    @abstractmethod
    def is_empty(self) -> bool:
        """Return True if variable has no meaningful value."""

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.to_string()!r})"


class FNodeVariable(FVariable):
    """
    Holds a single value: string, bytes, or parsed XML element.
    This is the most common variable type — most plugins return this.
    """

    def __init__(self, value: Any) -> None:
        self._value = value

    @property
    def value(self) -> Any:
        return self._value

    def to_string(self) -> str:
        if self._value is None:
            return ""
        return str(self._value)

    def to_list(self) -> list[FVariable]:
        return [self]

    def is_empty(self) -> bool:
        return self._value is None or self.to_string().strip() == ""


class FListVariable(FVariable):
    """
    Holds a list of FVariable instances.
    Returned by plugins like xpath-extract when multiple nodes match.
    """

    def __init__(self, items: list[FVariable] | None = None) -> None:
        self._items: list[FVariable] = items or []

    @property
    def items(self) -> list[FVariable]:
        return self._items

    def append(self, item: FVariable) -> None:
        self._items.append(item)

    def to_string(self) -> str:
        return "".join(item.to_string() for item in self._items)

    def to_list(self) -> list[FVariable]:
        return list(self._items)

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self):
        return iter(self._items)


class FEmptyVariable(FVariable):
    """
    Represents the absence of a value.
    Returned by plugins like <empty> or when execution produces nothing.
    """

    _instance: "FEmptyVariable | None" = None

    def __new__(cls) -> "FEmptyVariable":
        # Singleton — there's only one empty variable
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def to_string(self) -> str:
        return ""

    def to_list(self) -> list[FVariable]:
        return []

    def is_empty(self) -> bool:
        return True