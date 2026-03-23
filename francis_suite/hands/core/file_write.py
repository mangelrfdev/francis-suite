"""
hands/core/file_write.py

FileWriteHand implements the <file-write> tag.
Writes content to a file on disk.

Usage in XML:
    <file-write path="output/results.txt">
        ${contenido}
    </file-write>

    <file-write path="output/results.txt" append="true" newline="true">
        nueva linea
    </file-write>

    <!-- binary — PDF, Excel, images -->
    <file-write path="downloads/report.pdf" encoding="binary">
        <box name="reporte"/>
    </file-write>
"""

from __future__ import annotations
from pathlib import Path
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand
from francis_suite.core.expressions import FrancisExpression


@hand(tag="file-write")
class FileWriteHand(AbstractHand):
    """
    Writes content to a file on disk.

    Attributes:
        path (required): path to the file to write.
        encoding (optional): file encoding. Default: utf-8.
            Use "binary" for binary files (PDF, Excel, images, ZIP).
        append (optional): append to file instead of overwrite. Default: false.
            Not applicable when encoding="binary".
        newline (optional): add a newline character after content. Default: false.
            Not applicable when encoding="binary".
        mkdir (optional): create parent directories if missing. Default: true.

    Returns:
        FEmptyVariable always.

    Examples:
        <!-- text -->
        <file-write path="output/results.txt">
            ${contenido}
        </file-write>

        <!-- binary -->
        <file-write path="downloads/report.pdf" encoding="binary">
            <box name="reporte"/>
        </file-write>
    """

    def execute(self) -> FVariable:
        engine   = FrancisExpression(self.context)
        path_str = engine.resolve(self.require_attr("path"))
        encoding = engine.resolve(self.attr("encoding", "utf-8"))
        mkdir    = engine.resolve(self.attr("mkdir", "true")).lower() == "true"

        if self.has_children():
            result  = self.execute_children()
            content = result.value if encoding == "binary" else result.to_string()
        else:
            content = self.resolve_body_text()

        path = Path(path_str)

        if mkdir:
            path.parent.mkdir(parents=True, exist_ok=True)

        if encoding == "binary":
            with path.open("wb") as f:
                f.write(content if isinstance(content, bytes) else content.encode("utf-8"))
        else:
            append  = engine.resolve(self.attr("append", "false")).lower() == "true"
            newline = engine.resolve(self.attr("newline", "false")).lower() == "true"

            if newline:
                content = content + "\n"

            mode = "a" if append else "w"
            with path.open(mode, encoding=encoding) as f:
                f.write(content)

        return FEmptyVariable()
