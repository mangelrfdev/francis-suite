"""
hands/core/file_write.py

FileWriteHand implements the <file-write> tag.
Writes content to a file on disk.

Usage in XML:
    <file-write path="output/results.txt">
        ${contenido}
    </file-write>

    <file-write path="output/results.txt" append="true">
        nueva linea
    </file-write>
"""

from __future__ import annotations
from pathlib import Path
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="file-write")
class FileWriteHand(AbstractHand):
    """
    Writes content to a file on disk.

    Attributes:
        path (required): path to the file to write.
        encoding (optional): file encoding. Default: utf-8.
        append (optional): append to file instead of overwrite. Default: false.
        mkdir (optional): create parent directories if missing. Default: true.

    Returns:
        FEmptyVariable always.

    Example:
        <file-write path="output/results.txt">
            ${contenido}
        </file-write>
    """

    def execute(self) -> FVariable:
        path_str = self.require_attr("path")
        encoding = self.attr("encoding", "utf-8")
        append = self.attr("append", "false").lower() == "true"
        mkdir = self.attr("mkdir", "true").lower() == "true"

        if self.has_children():
            content = self.execute_children().to_string()
        else:
            content = self.resolve_body_text()

        path = Path(path_str)

        if mkdir:
            path.parent.mkdir(parents=True, exist_ok=True)

        mode = "a" if append else "w"
        path.open(mode, encoding=encoding).write(content)

        return FEmptyVariable()