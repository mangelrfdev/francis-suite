"""
core/parser.py

FParser reads a workflow XML file and builds a tree of FNodes.
This is the first step in the execution pipeline.

Input:  workflow.xml (file path, string, or bytes)
Output: FNode tree (root node with children)
"""

from __future__ import annotations
from pathlib import Path
from lxml import etree
from francis_suite.core.nodes import FNode


class ParseError(Exception):
    """Raised when the workflow XML cannot be parsed."""


class FParser:
    """
    Parses a Francis Suite workflow XML file into an FNode tree.

    Usage:
        parser = FParser()
        root = parser.parse_file("workflow.xml")
        root = parser.parse_string("<francis-workflow>...</francis-workflow>")
    """

    # The root tag every workflow must start with
    ROOT_TAG = "francis-workflow"

    def parse_file(self, path: str | Path) -> FNode:
        """
        Parse a workflow XML file from disk.
        Raises ParseError if the file cannot be read or parsed.
        """
        path = Path(path)
        if not path.exists():
            raise ParseError(f"Workflow file not found: {path}")
        try:
            content = path.read_bytes()
            return self.parse_bytes(content, source=str(path))
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Cannot read workflow file '{path}': {e}") from e

    def parse_string(self, xml: str, source: str = "<string>") -> FNode:
        """
        Parse a workflow XML from a string.
        Useful for testing and dynamic workflows.
        """
        return self.parse_bytes(xml.encode("utf-8"), source=source)

    def parse_bytes(self, xml: bytes, source: str = "<bytes>") -> FNode:
        """
        Parse a workflow XML from bytes.
        This is the core parsing method — all others call this.
        """
        try:
            root_element = etree.fromstring(xml)
        except etree.XMLSyntaxError as e:
            raise ParseError(f"Invalid XML in '{source}': {e}") from e

        root_node = self._element_to_fnode(root_element, source=source)

        if root_node.tag != self.ROOT_TAG:
            raise ParseError(
                f"Workflow must start with <{self.ROOT_TAG}>, "
                f"got <{root_node.tag}> in '{source}'"
            )

        return root_node

    def _attrs_reject_empty(
        self,
        raw: dict,
        *,
        tag: str,
        line: int | None,
        source: str,
    ) -> dict[str, str]:
        """
        Fail if any attribute is present with a zero-length value (attr="").

        Values that are only spaces or other whitespace are allowed: spacing inside
        the quoted value is valid when the author intends it.
        """
        out: dict[str, str] = {}
        line_hint = f" (line {line})" if line else ""
        for k, v in raw.items():
            if v is None:
                raise ParseError(
                    f"Attribute '{k}' on <{tag}> has no value in '{source}'{line_hint}. "
                    f"Remove the attribute or set a value."
                )
            sv = str(v)
            if sv == "":
                raise ParseError(
                    f"Attribute '{k}' on <{tag}> cannot use an empty value (attr=\"\") in "
                    f"'{source}'{line_hint}. Remove the attribute or set a value."
                )
            out[k] = sv
        return out

    def _element_to_fnode(self, element: etree._Element, *, source: str) -> FNode:
        """
        Recursively convert an lxml element to an FNode.
        Strips XML namespace prefixes from tag names.
        """
        tag = self._clean_tag(element.tag)
        line = element.sourceline if hasattr(element, "sourceline") else None
        attrs = self._attrs_reject_empty(
            dict(element.attrib), tag=tag, line=line, source=source
        )
        text = element.text.strip() if element.text and element.text.strip() else None

        node = FNode(
            tag=tag,
            attrs=attrs,
            text=text,
            source_line=line,
        )

        for child in element:
            if callable(child.tag):  # Ignore Comments and Processing Instructions
                continue
            child_node = self._element_to_fnode(child, source=source)
            node.children.append(child_node)

        return node

    def _clean_tag(self, tag: str) -> str:
        """
        Remove XML namespace prefix from tag name.
        Example: '{http://francis-suite.org/schema}http-call' → 'http-call'
        """
        if tag.startswith("{"):
            return tag.split("}", 1)[1]
        return tag