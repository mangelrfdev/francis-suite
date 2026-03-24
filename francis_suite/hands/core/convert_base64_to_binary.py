"""
hands/core/convert_base64_to_binary.py

ConvertBase64ToBinaryHand implements the <convert-base64-to-binary> tag.
Converts a base64 encoded string back to binary content (bytes).

Usage in XML:
    <box-def name="foto_bytes">
        <convert-base64-to-binary>
            <box name="foto_base64"/>
        </convert-base64-to-binary>
    </box-def>

    <!-- decode and save to disk -->
    <file-write path="downloads/foto.jpg" encoding="binary">
        <box name="foto_bytes"/>
    </file-write>
"""

from __future__ import annotations
import base64
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="convert-base64-to-binary")
class ConvertBase64ToBinaryHand(AbstractHand):
    """
    Converts a base64 encoded string back to binary content (bytes).

    Returns:
        FNodeVariable with the decoded bytes.
        FEmptyVariable if input is empty.

    Raises:
        ValueError if the input is not valid base64.

    Examples:
        <box-def name="foto_bytes">
            <convert-base64-to-binary>
                <box name="foto_base64"/>
            </convert-base64-to-binary>
        </box-def>
        <file-write path="downloads/foto.jpg" encoding="binary">
            <box name="foto_bytes"/>
        </file-write>
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

        # clean whitespace — base64 strings sometimes have newlines
        raw = raw.strip()

        try:
            decoded = base64.b64decode(raw)
        except Exception as e:
            raise ValueError(
                f"<convert-base64-to-binary> invalid base64 input: {e}"
            ) from e

        return FNodeVariable(decoded)
