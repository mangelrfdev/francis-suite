"""
core/variables.py

Variable types used throughout the execution engine.
Every plugin receives and returns FVariable instances.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


# ---------------------------------------------------------------------------
# Sensitive value masking
# ---------------------------------------------------------------------------

# Variable names that are automatically treated as sensitive
_SENSITIVE_NAMES = {
    "api_key", "apikey", "token", "password", "passwd",
    "secret", "credential", "auth", "private_key", "access_key",
}


def is_sensitive_name(name: str) -> bool:
    """
    Return True if the variable name suggests a sensitive value.
    Checks if any sensitive keyword is contained in the name.

    Examples:
        is_sensitive_name("api_key")          → True
        is_sensitive_name("openai_api_key")   → True
        is_sensitive_name("my_token")         → True
        is_sensitive_name("token_count")      → True  (contains "token")
        is_sensitive_name("ciudad")           → False
    """
    name_lower = name.lower()
    return any(keyword in name_lower for keyword in _SENSITIVE_NAMES)


def mask_sensitive(value: str) -> str:
    """
    Mask a sensitive value for display in logs and UI.

    Rules:
        - Always shows exactly 7 asterisks as prefix
        - Shows last 3 characters if value is longer than 4 characters
        - Shows 10 asterisks if value is 4 characters or shorter
        - Never reveals the real length of the value

    Examples:
        mask_sensitive("ab")             → "**********"
        mask_sensitive("abcd")           → "**********"
        mask_sensitive("abcde")          → "*******cde"
        mask_sensitive("secreto")        → "*******eto"
        mask_sensitive("mi_api_key_123") → "*******123"
        mask_sensitive("sk-abc123xyz")   → "*******xyz"
    """
    if len(value) <= 4:
        return "**********"
    return "*******" + value[-3:]


# ---------------------------------------------------------------------------
# Base variable
# ---------------------------------------------------------------------------

class FVariable(ABC):
    """Base class for all Francis Suite variables."""

    @abstractmethod
    def to_string(self) -> str:
        """Return the real string value. Used internally by the engine."""

    @abstractmethod
    def to_display(self) -> str:
        """Return the display string value. Used by logs and UI."""

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


# ---------------------------------------------------------------------------
# FNodeVariable
# ---------------------------------------------------------------------------

class FNodeVariable(FVariable):
    """
    Holds a single value: string, bytes, or parsed XML element.
    This is the most common variable type — most plugins return this.

    If sensitive=True, to_display() returns a masked value.
    The engine always uses to_string() internally — never masked.
    """

    def __init__(self, value: Any, sensitive: bool = False) -> None:
        self._value     = value
        self._sensitive = sensitive

    @property
    def value(self) -> Any:
        return self._value

    @property
    def sensitive(self) -> bool:
        return self._sensitive

    def as_sensitive(self) -> "FNodeVariable":
        """Return a new FNodeVariable with sensitive=True."""
        return FNodeVariable(self._value, sensitive=True)

    def to_string(self) -> str:
        """Return the real value. Used internally by the engine."""
        if self._value is None:
            return ""
        return str(self._value)

    def to_display(self) -> str:
        """
        Return the display value. Used by logs and UI.
        If sensitive, returns a masked value.
        """
        if self._sensitive:
            return mask_sensitive(self.to_string())
        return self.to_string()

    def to_list(self) -> list[FVariable]:
        return [self]

    def is_empty(self) -> bool:
        return self._value is None or self.to_string().strip() == ""


# ---------------------------------------------------------------------------
# FListVariable
# ---------------------------------------------------------------------------

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

    def to_display(self) -> str:
        return "".join(item.to_display() for item in self._items)

    def to_list(self) -> list[FVariable]:
        return list(self._items)

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self):
        return iter(self._items)


# ---------------------------------------------------------------------------
# FEmptyVariable
# ---------------------------------------------------------------------------

class FEmptyVariable(FVariable):
    """
    Represents the absence of a value.
    Returned when execution produces nothing.
    """

    _instance: "FEmptyVariable | None" = None

    def __new__(cls) -> "FEmptyVariable":
        # Singleton — there's only one empty variable
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def to_string(self) -> str:
        return ""

    def to_display(self) -> str:
        return ""

    def to_list(self) -> list[FVariable]:
        return []

    def is_empty(self) -> bool:
        return True
