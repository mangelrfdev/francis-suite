"""
hands/core/function_create.py

FunctionCreateHand implements the <function-create> tag.
Defines a reusable function that can be called with <function-call>.

Usage in XML:
    <function-create name="mi-funcion">
        <box-def name="resultado">
            <box name="param1"/>
        </box-def>
        <function-return>
            <box name="resultado"/>
        </function-return>
    </function-create>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="function-create")
class FunctionCreateHand(AbstractHand):
    """
    Defines a reusable function stored in the session.

    Attributes:
        name (required): name of the function.

    Returns:
        FEmptyVariable — definition produces no output.
    """

    def execute(self) -> FVariable:
        name = self.require_attr("name")
        if not hasattr(self.session, "_functions"):
            self.session._functions = {}
        self.session._functions[name] = self._node
        return FEmptyVariable()