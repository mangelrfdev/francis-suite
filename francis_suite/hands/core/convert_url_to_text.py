"""
hands/core/convert_url_to_text.py

ConvertUrlToTextHand implements the <convert-url-to-text> tag.
Decodes a percent-encoded URL string back to plain text.

Usage in XML:
    <box-def name="texto">
        <convert-url-to-text>${url_encoded}</convert-url-to-text>
    </box-def>
    <!-- "departamento%20en%20santiago" → "departamento en santiago" -->

    <box-def name="ruta_limpia">
        <convert-url-to-text>
            <box name="href_extraido"/>
        </convert-url-to-text>
    </box-def>
"""

from __future__ import annotations
from urllib.parse import unquote
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="convert-url-to-text")
class ConvertUrlToTextHand(AbstractHand):
    """
    Decodes a percent-encoded URL string back to plain text.

    Returns:
        FNodeVariable with the decoded text string.
        FEmptyVariable if input is empty.

    Examples:
        <box-def name="texto">
            <convert-url-to-text>${url_encoded}</convert-url-to-text>
        </box-def>
        <!-- "departamento%20en%20santiago" → "departamento en santiago" -->
        <!-- "/propiedad%20en%20venta/las%20condes" → "/propiedad en venta/las condes" -->
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

        decoded = unquote(text, encoding="utf-8")
        return FNodeVariable(decoded)
