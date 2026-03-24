"""
hands/core/convert_binary_to_base64.py

ConvertBinaryToBase64Hand implements the <convert-binary-to-base64> tag.
Converts binary content (bytes) to a base64 encoded string.

Usage in XML:
    <box-def name="foto_base64">
        <convert-binary-to-base64>
            <box name="foto"/>
        </convert-binary-to-base64>
    </box-def>

    <!-- send to AI API -->
    <httpx-call url="https://api.ejemplo.com/analyze" method="POST">
        <httpx-param name="image">${foto_base64}</httpx-param>
    </httpx-call>

Note:
    Always download binary files with response="binary" before converting.
    Converting text-decoded content may produce corrupted base64.
"""

from __future__ import annotations
import base64
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="convert-binary-to-base64")
class ConvertBinaryToBase64Hand(AbstractHand):
    """
    Converts binary content (bytes) to a base64 encoded string.

    Returns:
        FNodeVariable with the base64 encoded string.
        FEmptyVariable if input is empty.

    Examples:
        <box-def name="foto_base64">
            <convert-binary-to-base64>
                <box name="foto"/>
            </convert-binary-to-base64>
        </box-def>
    """

    def execute(self) -> FVariable:
        if self.has_children():
            result = self.execute_children()
            if result.is_empty():
                return FEmptyVariable()
            raw = result.value if hasattr(result, "value") else result.to_string()
        else:
            raw = self.resolve_body_text()
            if not raw.strip():
                return FEmptyVariable()

        # convert to bytes if needed
        if isinstance(raw, bytes):
            data = raw
        else:
            data = str(raw).encode("utf-8")

        encoded = base64.b64encode(data).decode("utf-8")
        return FNodeVariable(encoded)
