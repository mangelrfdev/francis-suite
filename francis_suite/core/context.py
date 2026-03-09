"""
core/context.py

FContext is the variable store for a single workflow execution.
It holds all variables defined during execution and supports
nested scopes (for loops, functions, try/catch blocks).
"""

from __future__ import annotations
from contextlib import contextmanager
from typing import Iterator
from francis_suite.core.variables import FVariable, FEmptyVariable


class FContext:
    """
    Scoped variable store for a workflow execution.

    Variables are stored in a stack of scopes. The global scope
    is always at the bottom. When entering a block (loop, function,
    try), a new scope is pushed. When exiting, it is popped and
    all variables defined in that scope are gone.

    Example:
        ctx = FContext()
        ctx.set("url", FNodeVariable("https://example.com"))
        ctx.get("url")  # FNodeVariable("https://example.com")

        with ctx.new_scope():
            ctx.set("item", FNodeVariable("temporal"))
            ctx.get("item")  # FNodeVariable("temporal")

        ctx.get("item")  # FEmptyVariable — gone after scope exit
    """

    def __init__(self) -> None:
        # Stack of scopes. Each scope is a dict of name -> FVariable.
        # Index 0 is the global scope, last is the innermost scope.
        self._scopes: list[dict[str, FVariable]] = [{}]

    def set(self, name: str, value: FVariable) -> None:
        """
        Set a variable in the current (innermost) scope.
        If the variable already exists in an outer scope,
        it is shadowed — the outer value is NOT modified.
        """
        self._scopes[-1][name] = value

    def get(self, name: str) -> FVariable:
        """
        Get a variable by name.
        Searches from innermost scope outward.
        Returns FEmptyVariable if not found.
        """
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return FEmptyVariable()

    def has(self, name: str) -> bool:
        """Return True if variable exists in any scope."""
        return not self.get(name).is_empty()

    def set_global(self, name: str, value: FVariable) -> None:
        """
        Set a variable directly in the global scope.
        Useful for workflow-level parameters.
        """
        self._scopes[0][name] = value

    def set_shared_box(self, name: str, value: FVariable) -> None:
        """
        Set a shared variable in the global scope.
        Used by <shared-box-def> — accessible across all workflows and functions.
        """
        self._scopes[0][name] = value

    def get_shared_box(self, name: str) -> FVariable:
        """
        Get a shared variable directly from the global scope.
        Used by <shared-box> — bypasses any local variables with the same name.
        Returns FEmptyVariable if not found.
        """
        return self._scopes[0].get(name, FEmptyVariable())

    @contextmanager
    def new_scope(self) -> Iterator[None]:
        """
        Context manager that pushes a new scope on entry
        and pops it on exit (even if an exception occurs).

        Usage:
            with ctx.new_scope():
                ctx.set("temp", some_value)
            # temp is gone here
        """
        self._scopes.append({})
        try:
            yield
        finally:
            self._scopes.pop()

    @property
    def depth(self) -> int:
        """Current scope depth. 1 = only global scope."""
        return len(self._scopes)

    @property
    def current_scope_vars(self) -> dict[str, FVariable]:
        """Variables defined in the current (innermost) scope only."""
        return dict(self._scopes[-1])

    def __repr__(self) -> str:
        total = sum(len(s) for s in self._scopes)
        return f"FContext(depth={self.depth}, total_vars={total})"