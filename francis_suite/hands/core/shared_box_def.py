"""
hands/core/shared_box_def.py

SharedBoxDefHand implements the <shared-box-def> tag.
Stores a variable in the global scope, accessible across all
workflows and functions regardless of the current execution scope.

Usage in XML:
    <!-- solo crea si no existe -->
    <shared-box-def name="env" replace="false">production</shared-box-def>

    <!-- siempre sobreescribe -->
    <shared-box-def name="env" replace="true">staging</shared-box-def>

    <!-- usar como variable normal -->
    <if condition="${env} == 'production'">...</if>
    <log>${env}</log>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable, FNodeVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="shared-box-def")
class SharedBoxDefHand(AbstractHand):
    """
    Stores a variable in the global scope.

    Unlike <box-def> which stores in the current scope,
    <shared-box-def> always stores in the root global scope.
    Accessible everywhere — inside functions, loops, and across
    call-workflow calls.

    If a local <box-def> has the same name, the local variable
    takes precedence with ${variable} syntax. Use <shared-box>
    to read the global value explicitly.

    Attributes:
        name (required): name of the variable to store.
        replace (optional): whether to replace if already exists. Default: true.
            replace="true"  — always overwrite.
            replace="false" — only create if it does not exist yet.

    Returns:
        The stored value.

    Examples:
        <shared-box-def name="env" replace="false">production</shared-box-def>
        <shared-box-def name="env" replace="true">staging</shared-box-def>

        <if condition="${env} == 'production'">...</if>
        <while condition="${env.toBoolean()}">...</while>
        <log>${env}</log>
    """

    def execute(self) -> FVariable:
        name = self.require_attr("name")
        replace = self.attr("replace", "true").lower() == "true"

        # si replace=false y ya existe en global, no tocar
        existing = self.context.get_shared_box(name)
        if not replace and not existing.is_empty():
            return existing

        if self.has_children():
            result = self.execute_children()
        else:
            text = self.resolve_body_text()
            if text.strip():
                result = FNodeVariable(text)
            else:
                result = FEmptyVariable()

        self.context.set_shared_box(name, result)
        return result