"""
hands/core/convert_xml_to_json.py

ConvertXmlToJsonHand implements the <convert-xml-to-json> tag.
Converts an XML string into a JSON string.

Usage in XML:
    <box-def name="json">
        <convert-xml-to-json><root><nombre>Francis</nombre></root></convert-xml-to-json>
    </box-def>
"""

from __future__ import annotations
import json
import xmltodict
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="convert-xml-to-json")
class ConvertXmlToJsonHand(AbstractHand):
    """
    Converts an XML string into a JSON string.

    Attributes:
        pretty (optional): pretty print JSON output. Default: true.

    Returns:
        FNodeVariable with the resulting JSON string.
        FEmptyVariable if input is empty.

    Example:
        <convert-xml-to-json><root><name>Francis</name></root></convert-xml-to-json>
    """

    def execute(self) -> FVariable:
        pretty = self.attr("pretty", "true").lower() == "true"

        if self.has_children():
            text = self.execute_children().to_string()
        else:
            text = self.get_body_text()

        if not text.strip():
            return FEmptyVariable()

        try:
            data = xmltodict.parse(text)
            indent = 2 if pretty else None
            json_str = json.dumps(data, indent=indent, ensure_ascii=False)
            return FNodeVariable(json_str)
        except Exception as e:
            raise ValueError(f"<convert-xml-to-json> failed: {e}") from e