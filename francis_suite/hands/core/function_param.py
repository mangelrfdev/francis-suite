"""
hands/core/function_param.py

FunctionParamHand implements the <function-param> tag.
Used inside <function-call> to pass values to a function.
Never executed directly — handled by FunctionCallHand.

Usage in XML:
    <function-call name="mi-funcion">
        <function-param name="url">
            <box name="mi-url"/>
        </function-param>
    </function-call>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="function-param")
class FunctionParamHand(AbstractHand):
    """
    Placeholder for <function-param> tag.
    Never executed directly — always handled by FunctionCallHand.
    """

    def execute(self) -> FVariable:
        raise RuntimeError(
            "<function-param> cannot be used outside of a <function-call> block."
        )