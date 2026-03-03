"""
hands/base.py

AbstractHand is the base class for all Francis Suite hands.
Every hand must inherit from this class and implement execute().

Example:
    @hand(tag="log")
    class LogHand(AbstractHand):
        def execute(self) -> FVariable:
            value = self.get_body()
            print(value.to_string())
            return value
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from francis_suite.core.nodes import FNode
from francis_suite.core.session import FrancisSession
from francis_suite.core.variables import FVariable, FEmptyVariable


class AbstractHand(ABC):
    """
    Base class for all Francis Suite hands.

    A hand is the Python implementation of an XML tag.
    When the runtime encounters <http-call>, it finds the
    HttpCallHand class and calls its execute() method.

    Each hand has access to:
        - self.node    — the FNode with tag, attrs, and children
        - self.session — the current FrancisSession
        - self.context — shortcut to session.context

    Subclasses must implement:
        - execute() — the hand's core logic
    """

    def __init__(self, node: FNode, session: FrancisSession) -> None:
        self._node = node
        self._session = session

    # --- Core ---

    @abstractmethod
    def execute(self) -> FVariable:
        """
        Execute the hand's logic and return a result.
        This is the only method subclasses must implement.
        """

    # --- Shortcuts ---

    @property
    def node(self) -> FNode:
        """The FNode that represents this hand in the XML tree."""
        return self._node

    @property
    def session(self) -> FrancisSession:
        """The current execution session."""
        return self._session

    @property
    def context(self):
        """Shortcut to session.context."""
        return self._session.context

    @property
    def tag(self) -> str:
        """The XML tag name of this hand."""
        return self._node.tag

    # --- Attribute helpers ---

    def attr(self, name: str, default: str | None = None) -> str | None:
        """Get an XML attribute value, with optional default."""
        return self._node.get_attr(name, default)

    def require_attr(self, name: str) -> str:
        """
        Get a required XML attribute value.
        Raises ValueError if the attribute is missing.
        """
        return self._node.require_attr(name)

    # --- Body execution ---

    def get_body_text(self) -> str:
        """
        Get the text content of this node.
        Returns the text between the opening and closing tags.

        Example:
            <log>Hello world</log>
            get_body_text() → "Hello world"
        """
        return self._node.text or ""

    def has_children(self) -> bool:
        """Return True if this node has child elements."""
        return self._node.has_children()

    # --- Representation ---

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(tag={self.tag!r})"