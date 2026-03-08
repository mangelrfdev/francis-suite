"""
hands/core/file_read.py

FileReadHand implements the <file-read> tag.
Reads a file from disk and returns its content.

Usage in XML:
    <box-def name="contenido">
        <file-read path="data/config.txt"/>
    </box-def>

    <box-def name="imagen">
        <file-read path="images/logo.png" encoding="binary"/>
    </box-def>
"""

from __future__ import annotations
from pathlib import Path
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand
from francis_suite.core.expressions import FrancisExpression



@hand(tag="file-read")
class FileReadHand(AbstractHand):
    """
    Reads a file from disk and returns its content.

    Attributes:
        path (required): path to the file to read.
        encoding (optional): file encoding. Default: utf-8. Use "binary" for binary files.

    Returns:
        FNodeVariable with file content.
        FEmptyVariable if file is empty.

    Example:
        <file-read path="data/config.txt"/>
    """

    def execute(self) -> FVariable:
        engine = FrancisExpression(self.context)
        path_str = engine.resolve(self.require_attr("path"))
        encoding = engine.resolve(self.attr("encoding", "utf-8"))
        path = Path(path_str)

        if not path.exists():
            raise FileNotFoundError(
                f"<file-read> cannot find file: '{path}'"
            )

        if encoding == "binary":
            content = path.read_bytes()
        else:
            content = path.read_text(encoding=encoding)

        if not content:
            return FEmptyVariable()

        return FNodeVariable(content)