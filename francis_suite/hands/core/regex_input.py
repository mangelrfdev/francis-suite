r"""
hands/core/regex_input.py

RegexInputHand implements the <regex-input> tag.
Provides the text to search in inside <regex>.
Never executed directly — handled by RegexHand.

Usage in XML:
    <regex>
        <regex-pattern><![CDATA[(\d+)]]></regex-pattern>
        <regex-input>Hay 42 productos</regex-input>
    </regex>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="regex-input")
class RegexInputHand(AbstractHand):
    """
    Placeholder for <regex-input> tag.
    Never executed directly — always handled by RegexHand.
    """

    def execute(self) -> FVariable:
        raise RuntimeError(
            "<regex-input> cannot be used outside of a <regex> block."
        )