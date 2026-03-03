"""
core/nodes.py

FNode represents a single XML element after parsing.
The parser builds a tree of FNodes from the workflow XML file.
The runtime walks this tree and executes each node as a plugin.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class FNode:
    """
    A single node in the parsed XML tree.

    Each FNode corresponds to one XML element in the workflow file.
    Example:
        <http-call url="https://example.com" method="GET"/>
    becomes:
        FNode(tag="http-call", attrs={"url": "...", "method": "GET"})
    """

    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list["FNode"] = field(default_factory=list)
    text: str | None = None
    source_line: int | None = None  # line number in original XML, for error messages

    def get_attr(self, name: str, default: str | None = None) -> str | None:
        """Get attribute value by name, with optional default."""
        return self.attrs.get(name, default)

    def require_attr(self, name: str) -> str:
        """
        Get attribute value by name.
        Raises ValueError if the attribute is missing.
        Use this for required attributes.
        """
        value = self.attrs.get(name)
        if value is None:
            raise ValueError(
                f"Plugin <{self.tag}> requires attribute '{name}' "
                f"(line {self.source_line})"
            )
        return value

    def has_children(self) -> bool:
        """Return True if this node has child elements."""
        return len(self.children) > 0

    def children_by_tag(self, tag: str) -> list["FNode"]:
        """Return all direct children with a specific tag name."""
        return [child for child in self.children if child.tag == tag]

    def first_child_by_tag(self, tag: str) -> "FNode | None":
        """Return first direct child with a specific tag name, or None."""
        for child in self.children:
            if child.tag == tag:
                return child
        return None

    def __repr__(self) -> str:
        attrs_str = ", ".join(f'{k}="{v}"' for k, v in self.attrs.items())
        return f"FNode(tag={self.tag!r}, attrs={{{attrs_str}}}, children={len(self.children)})"