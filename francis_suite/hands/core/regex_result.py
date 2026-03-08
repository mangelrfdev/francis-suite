r"""
hands/core/regex_result.py

RegexResultHand implements the <regex-result> tag.
Defines the output template for regex matches inside <regex>.
Never executed directly — handled by RegexHand.

Usage in XML:
    <regex>
        <regex-pattern><![CDATA[(\d+)\.(\d{2})]]></regex-pattern>
        <regex-input>El precio es 19.99</regex-input>
        <regex-result>${_1}.${_2}</regex-result>
    </regex>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="regex-result")
class RegexResultHand(AbstractHand):
    """
    Placeholder for <regex-result> tag.
    Never executed directly — always handled by RegexHand.
    """

    def execute(self) -> FVariable:
        raise RuntimeError(
            "<regex-result> cannot be used outside of a <regex> block."
        )