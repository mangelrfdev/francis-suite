"""
hands/core/convert_html_to_xml.py

ConvertHtmlToXmlHand implements the <convert-html-to-xml> tag.
Converts raw HTML into a clean XML string that can be processed
by xpath-extract and other XML-based hands.

Usage in XML:
    <box-def var="xml-page">
        <convert-html-to-xml>
            <http-call url="https://example.com"/>
        </convert-html-to-xml>
    </box-def>
"""

from __future__ import annotations
from lxml import etree, html
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="convert-html-to-xml")
class ConvertHtmlToXmlHand(AbstractHand):
    """
    Converts HTML to clean XML.

    Executes its children to get the HTML input, then parses
    it with lxml's HTML parser and serializes it back as XML.

    Attributes:
        charset (optional): input encoding. Default: utf-8.

    Returns:
        FNodeVariable with the cleaned XML string.

    Example:
        <convert-html-to-xml>
            <http-call url="https://example.com"/>
        </convert-html-to-xml>
    """

    def execute(self) -> FVariable:
        # Get HTML from children or body text
        if self.has_children():
            result = self.execute_children()
            raw_html = result.to_string()
        else:
            raw_html = self.get_body_text()

        if not raw_html.strip():
            return FEmptyVariable()

        cleaned_xml = self._html_to_xml(raw_html)
        return FNodeVariable(cleaned_xml)

    def _html_to_xml(self, raw_html: str) -> str:
        """
        Parse HTML with lxml and serialize as XML string.
        lxml's HTML parser is tolerant of malformed HTML.
        """
        charset = self.attr("charset", "utf-8")

        # Parse the HTML — lxml handles malformed HTML gracefully
        doc = html.fromstring(raw_html.encode(charset))

        # Serialize back as XML string
        xml_bytes = etree.tostring(
            doc,
            pretty_print=True,
            encoding="unicode",
            method="xml",
        )

        return xml_bytes