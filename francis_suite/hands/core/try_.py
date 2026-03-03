"""
hands/core/try_.py

TryHand implements the <try> tag.
Executes children and catches errors via a nested <catch> tag.

Usage in XML:
    <try>
        <http-call url="https://example.com"/>
        <catch>
            <log>Something went wrong</log>
        </catch>
    </try>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable, FNodeVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="try")
class TryHand(AbstractHand):
    """
    Executes children safely, catching errors with <catch>.

    The <catch> tag must be a direct child of <try>.
    If an error occurs, the catch block executes.
    If no error occurs, the catch block is skipped.

    Returns:
        Result of the try block, or result of catch block if error occurred.

    Example:
        <try>
            <http-call url="https://example.com"/>
            <catch>
                <log>Request failed</log>
            </catch>
        </try>
    """

    def execute(self) -> FVariable:
        # Separate catch node from other children
        catch_node = self._node.first_child_by_tag("catch")
        try_children = [
            child for child in self._node.children
            if child.tag != "catch"
        ]

        try:
            result: FVariable = FEmptyVariable()
            for child in try_children:
                result = self.execute_child(child)
            return result

        except Exception as e:
            if catch_node is None:
                raise

            # Store error message in context for use inside catch
            self.context.set(
                "error",
                FNodeVariable(str(e))
            )

            # Execute catch block
            catch_result: FVariable = FEmptyVariable()
            for child in catch_node.children:
                catch_result = self.execute_child(child)
            return catch_result