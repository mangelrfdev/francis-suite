"""
hands/core/xpath_extract.py

XPathExtractHand implements the <xpath-extract> tag.
Applies an XPath expression to XML content and returns the results.

Usage in XML:
    <box-def var="titles">
        <xpath-extract expression="//h1/text()">
            <box-def var="xml-page">
                <convert-html-to-xml>
                    <httpx-call url="https://example.com"/>
                </convert-html-to-xml>
            </box-def>
        </xpath-extract>
    </box-def>
"""

from __future__ import annotations
from lxml import etree
from francis_suite.core.registry import hand
from francis_suite.core.variables import (
    FVariable,
    FNodeVariable,
    FListVariable,
    FEmptyVariable,
)
from francis_suite.hands.base import AbstractHand


@hand(tag="xpath-extract")
class XPathExtractHand(AbstractHand):
    """
    Applies an XPath expression to XML content.

    Attributes:
        expression (required): the XPath expression to apply.

    Returns:
        FListVariable if multiple results found.
        FNodeVariable if single result found.
        FEmptyVariable if no results found.

    Example:
        <xpath-extract expression="//h1/text()">
            <box var="xml-page"/>
        </xpath-extract>
    """

    def execute(self) -> FVariable:
        expression = self.require_attr("expression")

        # Get XML content from children or body text
        if self.has_children():
            result = self.execute_children()
            xml_content = result.to_string()
        else:
            xml_content = self.get_body_text()

        if not xml_content.strip():
            return FEmptyVariable()

        return self._apply_xpath(expression, xml_content)

    def _apply_xpath(self, expression: str, xml_content: str) -> FVariable:
        """Parse XML and apply XPath expression."""
        try:
            root = etree.fromstring(xml_content.encode("utf-8"))
        except etree.XMLSyntaxError as e:
            raise ValueError(
                f"<xpath-extract> received invalid XML: {e}"
            ) from e

        try:
            results = root.xpath(expression)
        except etree.XPathEvalError as e:
            raise ValueError(
                f"<xpath-extract> invalid XPath expression '{expression}': {e}"
            ) from e

        if not results:
            return FEmptyVariable()

        if len(results) == 1:
            return FNodeVariable(self._to_string(results[0]))

        items = [FNodeVariable(self._to_string(r)) for r in results]
        return FListVariable(items)

    def _to_string(self, value) -> str:
        """Convert an XPath result to string."""
        if isinstance(value, str):
            return value
        if isinstance(value, bytes):
            return value.decode("utf-8")
        if hasattr(value, "tag"):
            return etree.tostring(value, encoding="unicode", method="xml")
        return str(value)