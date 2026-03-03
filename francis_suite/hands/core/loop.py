"""
hands/core/loop.py

LoopHand implements the <loop> tag.
Iterates over a list and executes children for each item.

Usage in XML:
    <loop item="url" list="${urls}">
        <log>${url}</log>
    </loop>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import (
    FVariable,
    FNodeVariable,
    FListVariable,
    FEmptyVariable,
)
from francis_suite.hands.base import AbstractHand


@hand(tag="loop")
class LoopHand(AbstractHand):
    """
    Iterates over a list variable and executes children for each item.

    Attributes:
        item (required): name of the variable that holds the current item.
        list (required): expression that resolves to a list variable.

    Returns:
        FEmptyVariable — loop produces no direct output.

    Example:
        <loop item="url" list="${urls}">
            <log>${url}</log>
        </loop>
    """

    def execute(self) -> FVariable:
        item_name = self.require_attr("item")
        list_expr = self.require_attr("list")

        # Resolve the list variable from context
        list_var = self._resolve_list(list_expr)

        if list_var.is_empty():
            return FEmptyVariable()

        for item in list_var.to_list():
            with self.context.new_scope():
                self.context.set(item_name, item)
                self.execute_children()

        return FEmptyVariable()

    def _resolve_list(self, expr: str) -> FVariable:
        """
        Resolve a list expression from the context.
        Supports ${varname} syntax.
        """
        if expr.startswith("${") and expr.endswith("}"):
            var_name = expr[2:-1].strip()
            return self.context.get(var_name)

        # If it's a plain string, wrap it as a single-item list
        return FListVariable([FNodeVariable(expr)])