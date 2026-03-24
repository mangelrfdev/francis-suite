"""
hands/core/convert_base64_to_text.py

ConvertBase64ToTextHand implements the <convert-base64-to-text> tag.
Converts a base64 encoded string back to plain text.

Usage in XML:
    <box-def name="texto">
        <convert-base64-to-text>
            <box name="texto_base64"/>
        </convert-base64-to-text>
    </box-def>

    <box-def name="texto">
        <convert-base64-to-text>${texto_base64}</convert-base64-to-text>
    </box-def>
"""

from __future__ import annotations
import base64
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="convert-base64-to-text")
class ConvertBase64ToTextHand(AbstractHand):
    """
    Converts a base64 encoded string back to plain text.
    Decodes the base64 bytes as UTF-8 text.

    Returns:
        FNodeVariable with the decoded text string.
        FEmptyVariable if input is empty.

    Raises:
        ValueError if the input is not valid base64.
        ValueError if the decoded bytes are not valid UTF-8 text.

    Examples:
        <box-def name="texto">
            <convert-base64-to-text>
                <box name="texto_base64"/>
            </convert-base64-to-text>
        </box-def>
    """

    def execute(self) -> FVariable:
        if self.has_children():
            result = self.execute_children()
            if result.is_empty():
                return FEmptyVariable()
            raw = result.to_string()
        else:
            raw = self.resolve_body_text()
            if not raw.strip():
                return FEmptyVariable()

        raw = raw.strip()

        try:
            decoded_bytes = base64.b64decode(raw)
        except Exception as e:
            raise ValueError(
                f"<convert-base64-to-text> invalid base64 input: {e}"
            ) from e

        try:
            text = decoded_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(
                f"<convert-base64-to-text> decoded bytes are not valid UTF-8 text. "
                f"Use <convert-base64-to-binary> instead: {e}"
            ) from e

        return FNodeVariable(text)
