"""
hands/core/convert_html_entities_to_text.py

ConvertHtmlEntitiesToTextHand implements the <convert-html-entities-to-text> tag.
Converts HTML entities in a string back to their original characters.

Usage in XML:
    <box-def name="titulo_limpio">
        <convert-html-entities-to-text>${titulo}</convert-html-entities-to-text>
    </box-def>
    <!-- "Casa &amp; Jardín &lt;100m&sup2;&gt;" → "Casa & Jardín <100m²>" -->

    <box-def name="descripcion_limpia">
        <convert-html-entities-to-text>
            <box name="descripcion"/>
        </convert-html-entities-to-text>
    </box-def>

Common entities handled:
    &amp;  → &
    &lt;   → <
    &gt;   → >
    &nbsp; → (space)
    &quot; → "
    &apos; → '
    &sup2; → ²
    &sup3; → ³
    &#39;  → '
    &#160; → (non-breaking space)
    and many more...
"""

from __future__ import annotations
from html import unescape
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="convert-html-entities-to-text")
class ConvertHtmlEntitiesToTextHand(AbstractHand):
    """
    Converts HTML entities in a string back to their original characters.
    Works on any text — not just HTML content.

    Returns:
        FNodeVariable with the decoded text string.
        FEmptyVariable if input is empty.

    Examples:
        <box-def name="titulo_limpio">
            <convert-html-entities-to-text>${titulo}</convert-html-entities-to-text>
        </box-def>
        <!-- "Casa &amp; Jardín" → "Casa & Jardín" -->
        <!-- "precio &lt; 100&nbsp;UF" → "precio < 100 UF" -->
        <!-- "100m&sup2;" → "100m²" -->
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

        decoded = unescape(text)
        return FNodeVariable(decoded)
