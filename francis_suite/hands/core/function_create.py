"""
hands/core/function_create.py

FunctionCreateHand implements the <function-create> tag.
Defines a reusable function that can be called with <function-call>.

Usage in XML:
    <function-create name="mi-funcion">
        <function-return>
            <box name="resultado"/>
        </function-return>
    </function-create>

    <!-- replace="false" — no sobreescribe si ya existe -->
    <function-create name="mi-funcion" replace="false">
        ...
    </function-create>

    <!-- replace="true" — siempre sobreescribe -->
    <function-create name="mi-funcion" replace="true">
        ...
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
        replace (optional): whether to replace if already exists. Default: true.
            replace="true"  — always overwrite.
            replace="false" — only create if it does not exist yet.

    Returns:
        FEmptyVariable — definition produces no output.
    """

    def execute(self) -> FVariable:
        name = self.require_attr("name")
        replace = self.attr("replace", "true").lower() == "true"

        if not hasattr(self.session, "_functions"):
            self.session._functions = {}

        if not replace and name in self.session._functions:
            return FEmptyVariable()

        self.session._functions[name] = self._node
        return FEmptyVariable()