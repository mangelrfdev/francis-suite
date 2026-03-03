r"""
hands/core/regex_results.py

RegexResultsHand implements the <regex-results> tag.
Defines the output template for regex matches inside <regex>.
Never executed directly — handled by RegexHand.

Usage in XML:
    <regex>
        <regex-pattern><![CDATA[(\d+)\.(\d{2})]]></regex-pattern>
        <regex-input>El precio es 19.99</regex-input>
        <regex-results>${group1}.${group2}</regex-results>
    </regex>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="regex-results")
class RegexResultsHand(AbstractHand):
    """
    Placeholder for <regex-results> tag.
    Never executed directly — always handled by RegexHand.
    """

    def execute(self) -> FVariable:
        raise RuntimeError(
            "<regex-results> cannot be used outside of a <regex> block."
        )