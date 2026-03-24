"""
hands/core/convert_text_to_base64.py

ConvertTextToBase64Hand implements the <convert-text-to-base64> tag.
Converts a text string to a base64 encoded string.

Usage in XML:
    <box-def name="texto_base64">
        <convert-text-to-base64>Hola mundo</convert-text-to-base64>
    </box-def>

    <box-def name="texto_base64">
        <convert-text-to-base64>${mensaje}</convert-text-to-base64>
    </box-def>
"""

from __future__ import annotations
import base64
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="convert-text-to-base64")
class ConvertTextToBase64Hand(AbstractHand):
    """
    Converts a text string to a base64 encoded string.
    Encodes the text as UTF-8 bytes before converting to base64.

    Returns:
        FNodeVariable with the base64 encoded string.
        FEmptyVariable if input is empty.

    Examples:
        <box-def name="texto_base64">
            <convert-text-to-base64>${mensaje}</convert-text-to-base64>
        </box-def>
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

        data    = text.encode("utf-8")
        encoded = base64.b64encode(data).decode("utf-8")
        return FNodeVariable(encoded)
