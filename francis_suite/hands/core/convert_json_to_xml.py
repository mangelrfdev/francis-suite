"""
hands/core/convert_json_to_xml.py

ConvertJsonToXmlHand implements the <convert-json-to-xml> tag.
Converts a JSON string into an XML string.

Usage in XML:
    <box-def name="xml">
        <convert-json-to-xml>{"nombre": "Francis", "edad": 30}</convert-json-to-xml>
    </box-def>
"""

from __future__ import annotations
import json
import xmltodict
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="convert-json-to-xml")
class ConvertJsonToXmlHand(AbstractHand):
    """
    Converts a JSON string into an XML string.

    Attributes:
        root (optional): root element name. Default: "root".

    Returns:
        FNodeVariable with the resulting XML string.
        FEmptyVariable if input is empty.

    Example:
        <convert-json-to-xml>{"name": "Francis"}</convert-json-to-xml>
    """

    def execute(self) -> FVariable:
        root_name = self.attr("root", "root")

        if self.has_children():
            text = self.execute_children().to_string()
        else:
            text = self.get_body_text()

        if not text.strip():
            return FEmptyVariable()

        try:
            data = json.loads(text)
            xml_str = xmltodict.unparse({root_name: data}, pretty=True)
            return FNodeVariable(xml_str)
        except Exception as e:
            raise ValueError(f"<convert-json-to-xml> failed: {e}") from e