"""
hands/core/loop.py

LoopHand implements the <loop> tag.
Iterates over a list and executes loop-body for each item.

Usage in XML:
    <loop item="producto" index="i" max-loops="10">
        <loop-list>
            <box name="productos"/>
        </loop-list>
        <loop-body>
            <log>Procesando ${i}: ${producto}</log>
        </loop-body>
    </loop>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import (
    FVariable,
    FNodeVariable,
    FEmptyVariable,
)
from francis_suite.hands.base import AbstractHand


@hand(tag="loop")
class LoopHand(AbstractHand):
    """
    Iterates over a list and executes loop-body for each item.

    Attributes:
        item (required): name of the variable for the current item.
        index (optional): name of the counter variable. Starts at 1.
        max-loops (optional): maximum number of iterations.

    Child tags:
        <loop-list> — defines the list to iterate over (required)
        <loop-body> — defines the logic for each iteration (required)

    Returns:
        FEmptyVariable — loop produces no direct output.

    Notes:
        - item and index are set in the global context and updated each iteration.
        - box-def variables defined inside loop-body persist in the global context.
        - Variables are only updated when explicitly touched — if not touched, they keep their value.

    Example:
        <loop item="producto" index="i" max-loops="10">
            <loop-list>
                <box name="productos"/>
            </loop-list>
            <loop-body>
                <log>Procesando ${i}: ${producto}</log>
            </loop-body>
        </loop>
    """

    def execute(self) -> FVariable:
        item_name  = self.require_attr("item")
        index_name = self.attr("index", None)
        max_loops  = self.attr("max-loops", None)

        max_loops = int(max_loops) if max_loops is not None else None

        # Get loop-list and loop-body nodes
        list_node = self._node.first_child_by_tag("loop-list")
        body_node = self._node.first_child_by_tag("loop-body")

        if list_node is None:
            raise ValueError("<loop> requires a <loop-list> child tag.")
        if body_node is None:
            raise ValueError("<loop> requires a <loop-body> child tag.")

        # Resolve the list
        list_var = self._runtime._execute_children(list_node, self._session)

        if list_var.is_empty():
            return FEmptyVariable()

        items = list_var.to_list()

        for i, item in enumerate(items, start=1):
            if max_loops is not None and i > max_loops:
                break

            # item e index se actualizan en el contexto global cada iteración
            self.context.set(item_name, item)
            if index_name:
                self.context.set(index_name, FNodeVariable(str(i)))

            # ejecutar el body — las box-def adentro persisten globalmente
            self._runtime._execute_children(body_node, self._session)

        return FEmptyVariable()