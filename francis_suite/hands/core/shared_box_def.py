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

    <!-- automatic sensitive — detected by name -->
    <shared-box-def name="api_key">secreto</shared-box-def>

    <!-- explicit sensitive -->
    <shared-box-def name="codigo_cliente" sensitive="true">abc123</shared-box-def>

    <!-- force not sensitive -->
    <shared-box-def name="token_count" sensitive="false">100</shared-box-def>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable, FNodeVariable, is_sensitive_name
from francis_suite.hands.base import AbstractHand


@hand(tag="shared-box-def")
class SharedBoxDefHand(AbstractHand):
    """
    Stores a variable in the global scope.

    Unlike <box-def> which stores in the current scope,
    <shared-box-def> always stores in the root global scope.
    Accessible everywhere — inside functions, loops, and across
    call-workflow calls.

    Attributes:
        name (required): name of the variable to store.
        replace (optional): whether to replace if already exists. Default: true.
            replace="true"  — always overwrite.
            replace="false" — only create if it does not exist yet.
        sensitive (optional): whether to mask the value in logs and UI.
            sensitive="true"  — always mask.
            sensitive="false" — never mask.
            Default: auto-detected by variable name.

    Auto-sensitive names: api_key, apikey, token, password, passwd,
    secret, credential, auth, private_key, access_key.

    Returns:
        The stored value.

    Examples:
        <shared-box-def name="env" replace="false">production</shared-box-def>
        <shared-box-def name="api_key">secreto</shared-box-def>
        <shared-box-def name="codigo_cliente" sensitive="true">abc123</shared-box-def>
        <shared-box-def name="token_count" sensitive="false">100</shared-box-def>
    """

    def execute(self) -> FVariable:
        name    = self.require_attr("name")
        replace = self.attr("replace", "true").lower() == "true"

        # si replace=false y ya existe en global, no tocar
        existing = self.context.get_shared_box(name)
        if not replace and not existing.is_empty():
            return existing

        # resolve sensitive flag
        sensitive_attr = self.attr("sensitive", None)
        if sensitive_attr is not None:
            sensitive = sensitive_attr.lower() == "true"
        else:
            sensitive = is_sensitive_name(name)

        if self.has_children():
            result = self.execute_children()
        else:
            text = self.resolve_body_text()
            if text.strip():
                result = FNodeVariable(text)
            else:
                result = FEmptyVariable()

        # wrap result as sensitive if needed
        if sensitive and isinstance(result, FNodeVariable):
            result = result.as_sensitive()

        self.context.set_shared_box(name, result)
        return result
