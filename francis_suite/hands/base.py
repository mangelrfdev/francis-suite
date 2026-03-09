"""
hands/base.py

AbstractHand is the base class for all Francis Suite hands.
Every hand must inherit from this class and implement execute().

Example:
    @hand(tag="log")
    class LogHand(AbstractHand):
        def execute(self) -> FVariable:
            text = self.get_body_text()
            print(text)
            return FNodeVariable(text)
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
        - self.runtime — the FRuntime instance

    Subclasses must implement:
        - execute() — the hand's core logic

    --- DEVELOPMENT RULES FOR HAND AUTHORS ---

    RULE 1 — Variable interpolation in attributes:
        Any attribute that the user could write as ${variable} MUST be
        resolved through engine.resolve() before use.

        Example:
            engine = FrancisExpression(self.context)
            url = engine.resolve(self.require_attr("url"))
            path = engine.resolve(self.attr("path", "output/"))

        Attributes that DO need resolve():
            - Paths and URLs: path, url, dest
            - Expressions: expression (XPath)
            - Times: ms, timeout
            - Dynamic names: name in <function-call>
            - Any value the user might want to parametrize

        Attributes that do NOT need resolve():
            - Boolean flags: append, mkdir, recursive, pretty
            - Fixed choices: level (info/debug/warning/error)
            - Internal variable names: name in <box-def>, <function-create>

    RULE 2 — Variable scoping ("if not touched, it does not change"):
        Variables in the context only change when something explicitly sets them.
        If a branch (if, else, case) does not execute, its variables are not touched.
        If a loop iteration does not execute a box-def, that variable keeps its previous value.

        This means:
            - <while> and <loop> do NOT use new_scope() — variables persist across iterations.
            - <function-call> DOES use new_scope() — function internals are always isolated.

        Example:
            Iteration 1: titulo = "Book A"   <- touched
            Iteration 1: extra = ""          <- not touched, stays empty
            Iteration 2: titulo = "Book B"   <- touched
            Iteration 2: extra = "found"     <- touched
            Iteration 3: titulo = "Book C"   <- touched
            Iteration 3: extra = "found"     <- NOT touched, keeps "found" from iteration 2
    """

    def __init__(self, node: FNode, session: FrancisSession, runtime) -> None:
        self._node = node
        self._session = session
        self._runtime = runtime

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
        """
        Get an XML attribute value, with optional default.

        NOTE: If this attribute can contain ${variables}, wrap with
        engine.resolve() before use. See RULE 1 in class docstring.
        """
        return self._node.get_attr(name, default)

    def require_attr(self, name: str) -> str:
        """
        Get a required XML attribute value.
        Raises ValueError if the attribute is missing.

        NOTE: If this attribute can contain ${variables}, wrap with
        engine.resolve() before use. See RULE 1 in class docstring.
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

    def resolve_body_text(self) -> str:
        """
        Get the text content of this node with variables resolved.
        Use this instead of get_body_text() when the body may contain ${variables}.

        Example:
            <log>${nombre}</log>
            resolve_body_text() → "Francis"
        """
        from francis_suite.core.expressions import FrancisExpression
        raw = self.get_body_text()
        if not raw:
            return ""
        engine = FrancisExpression(self.context)
        return engine.resolve(raw)

    def has_children(self) -> bool:
        """Return True if this node has child elements."""
        return self._node.has_children()

    def execute_children(self) -> FVariable:
        """
        Execute all child nodes and return the result of the last one.
        Used by hands like box-def, loop, if, try, etc.
        """
        return self._runtime._execute_children(self._node, self._session)

    def execute_child(self, node: FNode) -> FVariable:
        """Execute a single specific child node."""
        return self._runtime.execute_node(node, self._session)

    # --- Representation ---

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(tag={self.tag!r})"