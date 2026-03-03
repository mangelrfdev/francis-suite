"""
hands/core/function_return.py

FunctionReturnHand implements the <function-return> tag.
Used inside <function-create> to define the return value.
Never executed directly — handled by FunctionCallHand.

Usage in XML:
    <function-create name="mi-funcion">
        <function-return>
            <box name="resultado"/>
        </function-return>
    </function-create>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="function-return")
class FunctionReturnHand(AbstractHand):
    """
    Placeholder for <function-return> tag.
    Never executed directly — always handled by FunctionCallHand.
    """

    def execute(self) -> FVariable:
        raise RuntimeError(
            "<function-return> cannot be used outside of a <function-create> block."
        )