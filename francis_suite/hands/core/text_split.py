"""
hands/core/text_split.py

TextSplitHand implements the <text-split> tag.
Splits text into a list of tokens using a delimiter.

Usage in XML:
    <box-def name="frutas">
        <text-split delimiter=",">manzana,pera,uva</text-split>
    </box-def>

    <loop item="fruta" list="${frutas}">
        <log>${fruta}</log>
    </loop>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import (
    FVariable,
    FNodeVariable,
    FListVariable,
    FEmptyVariable,
)
from francis_suite.hands.base import AbstractHand


@hand(tag="text-split")
class TextSplitHand(AbstractHand):
    """
    Splits text into a list of tokens.

    Attributes:
        delimiter (optional): character(s) to split on.
                              Default: whitespace (space, tab, newline).
        trim (optional): trim whitespace from each token. Default: true.
        allow-empty (optional): keep empty tokens. Default: false.

    Returns:
        FListVariable with the resulting tokens.
        FEmptyVariable if input is empty or produces no tokens.

    Example:
        <text-split delimiter=",">manzana,pera,uva</text-split>
    """

    def execute(self) -> FVariable:
        delimiter    = self.attr("delimiter")
        trim         = self.attr("trim", "true").lower() == "true"
        allow_empty  = self.attr("allow-empty", "false").lower() == "true"

        # Get text from children or body
        if self.has_children():
            text = self.execute_children().to_string()
        else:
            text = self.resolve_body_text()

        if not text.strip():
            return FEmptyVariable()

        # Split
        if delimiter is None:
            tokens = text.split()
        else:
            # Support escape sequences
            delimiter = delimiter.replace("\\n", "\n").replace("\\t", "\t")
            tokens = text.split(delimiter)

        # Process tokens
        if trim:
            tokens = [t.strip() for t in tokens]

        if not allow_empty:
            tokens = [t for t in tokens if t]

        if not tokens:
            return FEmptyVariable()

        if len(tokens) == 1:
            return FNodeVariable(tokens[0])

        return FListVariable([FNodeVariable(t) for t in tokens])