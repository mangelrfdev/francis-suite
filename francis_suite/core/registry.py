"""
core/registry.py

HandRegistry maps XML tag names to their Hand classes.
Hands register themselves automatically via the @hand decorator.

Example:
    @hand(tag="http-call")
    class HttpCallHand(AbstractHand):
        ...

    registry = HandRegistry.instance()
    hand_class = registry.get("http-call")  # HttpCallHand
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from francis_suite.hands.base import AbstractHand


class HandRegistry:
    """
    Central registry that maps tag names to Hand classes.
    Implemented as a singleton — there is one registry per process.
    """

    _instance: "HandRegistry | None" = None

    def __init__(self) -> None:
        self._hands: dict[str, type] = {}

    @classmethod
    def instance(cls) -> "HandRegistry":
        """Return the global singleton registry."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """
        Reset the singleton. Used in tests only.
        Never call this in production code.
        """
        cls._instance = None

    def register(self, tag: str, hand_class: type) -> None:
        """
        Register a hand class under a tag name.
        Raises ValueError if the tag is already registered.
        """
        if tag in self._hands:
            existing = self._hands[tag].__name__
            raise ValueError(
                f"Tag '{tag}' is already registered by {existing}. "
                f"Cannot register {hand_class.__name__} for the same tag."
            )
        self._hands[tag] = hand_class

    def get(self, tag: str) -> type | None:
        """
        Return the hand class for a tag name.
        Returns None if the tag is not registered.
        """
        return self._hands.get(tag)

    def require(self, tag: str) -> type:
        """
        Return the hand class for a tag name.
        Raises ValueError if the tag is not registered.
        Use this in the runtime where unknown tags are errors.
        """
        hand_class = self._hands.get(tag)
        if hand_class is None:
            raise ValueError(
                f"Unknown tag <{tag}>. "
                f"No hand is registered for this tag name."
            )
        return hand_class

    def all_tags(self) -> list[str]:
        """Return all registered tag names."""
        return list(self._hands.keys())

    def __len__(self) -> int:
        return len(self._hands)

    def __repr__(self) -> str:
        return f"HandRegistry({len(self._hands)} hands: {self.all_tags()})"


def hand(tag: str):
    """
    Decorator that registers a Hand class in the global registry.

    Usage:
        @hand(tag="http-call")
        class HttpCallHand(AbstractHand):
            ...

    The class is registered automatically when the module is imported.
    """
    def decorator(cls: type) -> type:
        HandRegistry.instance().register(tag, cls)
        return cls
    return decorator