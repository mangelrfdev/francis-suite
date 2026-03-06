"""
hands/core/build_list.py

BuildListHand implements the <build-list> tag.
Creates an explicit FListVariable from its children results.

Usage in XML:
    <box-def name="urls">
        <build-list>
            <log>https://ejemplo.com/page1</log>
            <log>https://ejemplo.com/page2</log>
            <log>https://ejemplo.com/page3</log>
        </build-list>
    </box-def>

    <loop item="url" list="${urls}">
        <httpx-call url="${url}"/>
    </loop>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FListVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="build-list")
class BuildListHand(AbstractHand):
    """
    Creates a list from its children results.

    Each child is executed and its result is added to the list.
    Empty results are excluded.

    Returns:
        FListVariable with results of all children.
        FEmptyVariable if no children or all children return empty.

    Example:
        <build-list>
            <log>item1</log>
            <log>item2</log>
            <log>item3</log>
        </build-list>
    """

    def execute(self) -> FVariable:
        items = []

        for child in self._node.children:
            result = self.execute_child(child)
            if not result.is_empty():
                items.append(result)

        if not items:
            return FEmptyVariable()

        return FListVariable(items)