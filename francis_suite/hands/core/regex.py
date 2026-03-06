r"""
hands/core/regex.py

RegexHand implements the <regex> tag.
Applies a regular expression to a text using child tags
regex-pattern, regex-input, and regex-results.

Usage in XML:
    <regex>
        <regex-pattern><![CDATA[(\d+)\.(\d{2})]]></regex-pattern>
        <regex-input>El precio es 19.99 euros</regex-input>
        <regex-results>${group1}.${group2}</regex-results>
    </regex>
"""

from __future__ import annotations
import re
from francis_suite.core.registry import hand
from francis_suite.core.variables import (
    FVariable,
    FNodeVariable,
    FListVariable,
    FEmptyVariable,
)
from francis_suite.hands.base import AbstractHand


@hand(tag="regex")
class RegexHand(AbstractHand):
    r"""
    Applies a regular expression to a text.

    Child tags:
        <regex-pattern> — the regular expression pattern (required)
        <regex-input>   — the text to search in (required)
        <regex-results> — output template with ${group0}, ${group1}, etc. (optional)

    Returns:
        FNodeVariable with formatted result if regex-results is defined.
        FNodeVariable with full match if no regex-results.
        FListVariable if multiple matches found.
        FEmptyVariable if no match found.

    Example:
        <regex>
            <regex-pattern><![CDATA[(\d+)]]></regex-pattern>
            <regex-input>Hay 42 productos</regex-input>
            <regex-results>${group1}</regex-results>
        </regex>
    """

    def execute(self) -> FVariable:
        pattern_node = self._node.first_child_by_tag("regex-pattern")
        input_node   = self._node.first_child_by_tag("regex-input")
        results_node = self._node.first_child_by_tag("regex-results")

        if pattern_node is None:
            raise ValueError("<regex> requires a <regex-pattern> child tag.")
        if input_node is None:
            raise ValueError("<regex> requires a <regex-input> child tag.")

        from francis_suite.core.expressions import FrancisExpression
        engine = FrancisExpression(self.context)

        if pattern_node.has_children():
            pattern = self.execute_child(pattern_node).to_string()
        else:
            pattern = engine.resolve(pattern_node.text or "")

        if input_node.has_children():
            source = self.execute_child(input_node).to_string()
        else:
            source = engine.resolve(input_node.text or "")

        results_template = None
        if results_node is not None:
            if results_node.has_children():
                results_template = self.execute_child(results_node).to_string()
            else:
                results_template = engine.resolve(results_node.text or "")

        if not source.strip():
            return FEmptyVariable()

        try:
            compiled = re.compile(pattern)
        except re.error as e:
            raise ValueError(
                f"<regex> invalid pattern '{pattern}': {e}"
            ) from e

        matches = list(compiled.finditer(source))

        if not matches:
            return FEmptyVariable()

        if results_template:
            results = []
            for match in matches:
                result = self._apply_template(results_template, match)
                results.append(FNodeVariable(result))
            if len(results) == 1:
                return results[0]
            return FListVariable(results)
        else:
            if len(matches) == 1:
                return FNodeVariable(matches[0].group(0))
            return FListVariable([FNodeVariable(m.group(0)) for m in matches])

    def _apply_template(self, template: str, match: re.Match) -> str:
        """Replace ${group0}, ${group1}, etc. with match groups."""
        result = template
        result = result.replace("${group0}", match.group(0))
        for i, group in enumerate(match.groups(), start=1):
            result = result.replace(f"${{group{i}}}", group or "")
        return result