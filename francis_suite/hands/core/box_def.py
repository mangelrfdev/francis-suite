"""
hands/core/box_def.py

BoxDefHand implements the <box-def> tag.
Executes its children and stores the result in a context variable.

Usage in XML:
    <box-def name="pagina">
        <httpx-call url="https://ejemplo.com"/>
    </box-def>

    <log>${pagina}</log>

    <!-- explicit sensitive -->
    <box-def name="codigo_cliente" sensitive="true">abc123</box-def>

    <!-- automatic sensitive — detected by name -->
    <box-def name="api_key">secreto</box-def>

    <!-- force not sensitive -->
    <box-def name="token_count" sensitive="false">100</box-def>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FEmptyVariable, is_sensitive_name
from francis_suite.hands.base import AbstractHand


@hand(tag="box-def")
class BoxDefHand(AbstractHand):
    """
    Executes child hands and stores the result in a named variable.

    Attributes:
        name (required): name of the variable to store the result in.
        sensitive (optional): whether to mask the value in logs and UI.
            sensitive="true"  — always mask.
            sensitive="false" — never mask.
            Default: auto-detected by variable name.

    Auto-sensitive names: api_key, apikey, token, password, passwd,
    secret, credential, auth, private_key, access_key.

    Returns:
        The result of the last child hand.

    Examples:
        <box-def name="titulo">
            <httpx-call url="https://ejemplo.com"/>
        </box-def>

        <!-- automatic sensitive -->
        <box-def name="api_key">secreto</box-def>

        <!-- explicit sensitive -->
        <box-def name="codigo_cliente" sensitive="true">abc123</box-def>

        <!-- force not sensitive -->
        <box-def name="token_count" sensitive="false">100</box-def>
    """

    def execute(self) -> FVariable:
        var_name = self.require_attr("name")

        # resolve sensitive flag
        sensitive_attr = self.attr("sensitive", None)
        if sensitive_attr is not None:
            sensitive = sensitive_attr.lower() == "true"
        else:
            sensitive = is_sensitive_name(var_name)

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

        self.context.set(var_name, result)
        return result
