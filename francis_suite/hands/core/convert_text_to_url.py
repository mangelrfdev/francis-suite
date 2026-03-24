"""
hands/core/convert_text_to_url.py

ConvertTextToUrlHand implements the <convert-text-to-url> tag.
Encodes a text string for safe use in URLs.
Spaces and special characters are converted to percent-encoded format.

Usage in XML:
    <box-def name="busqueda_url">
        <convert-text-to-url>departamento en santiago</convert-text-to-url>
    </box-def>
    <!-- resultado: departamento%20en%20santiago -->

    <box-def name="url">
        <compose>https://portal.cl/buscar?q=${busqueda_url}</compose>
    </box-def>
"""

from __future__ import annotations
from urllib.parse import quote
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="convert-text-to-url")
class ConvertTextToUrlHand(AbstractHand):
    """
    Encodes a text string for safe use in URLs.
    Converts spaces and special characters to percent-encoded format.

    Returns:
        FNodeVariable with the URL-encoded string.
        FEmptyVariable if input is empty.

    Examples:
        <box-def name="busqueda_url">
            <convert-text-to-url>${busqueda}</convert-text-to-url>
        </box-def>
        <!-- "departamento en santiago" → "departamento%20en%20santiago" -->
        <!-- "precio=100&tipo=casa" → "precio%3D100%26tipo%3Dcasa" -->
    """

    def execute(self) -> FVariable:
        if self.has_children():
            result = self.execute_children()
            if result.is_empty():
                return FEmptyVariable()
            text = result.to_string()
        else:
            text = self.resolve_body_text()
            if not text.strip():
                return FEmptyVariable()

        encoded = quote(text, safe="")
        return FNodeVariable(encoded)
