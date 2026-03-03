r"""
hands/core/regex_pattern.py

RegexPatternHand implements the <regex-pattern> tag.
Defines the regular expression pattern inside <regex>.
Never executed directly — handled by RegexHand.

Usage in XML:
    <regex>
        <regex-pattern><![CDATA[(\d+)]]></regex-pattern>
        ...
    </regex>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="regex-pattern")
class RegexPatternHand(AbstractHand):
    """
    Placeholder for <regex-pattern> tag.
    Never executed directly — always handled by RegexHand.
    """

    def execute(self) -> FVariable:
        raise RuntimeError(
            "<regex-pattern> cannot be used outside of a <regex> block."
        )