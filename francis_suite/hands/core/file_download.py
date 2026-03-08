"""
hands/core/file_download.py

FileDownloadHand implements the <file-download> tag.
Downloads a file from a URL and saves it to disk.

Usage in XML:
    <file-download url="https://ejemplo.com/image.png" path="downloads/image.png"/>

    <file-download
        url="https://ejemplo.com/report.pdf"
        path="downloads/report.pdf"
        mkdir="true"/>
"""

from __future__ import annotations
from pathlib import Path
import httpx
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand
from francis_suite.core.expressions import FrancisExpression


@hand(tag="file-download")
class FileDownloadHand(AbstractHand):
    """
    Downloads a file from a URL and saves it to disk.

    Attributes:
        url (required): URL to download from.
        path (required): local path to save the file.
        mkdir (optional): create parent directories if missing. Default: true.
        timeout (optional): request timeout in seconds. Default: 30.

    Returns:
        FNodeVariable with the local path where file was saved.

    Example:
        <file-download url="https://ejemplo.com/image.png" path="downloads/image.png"/>
    """

    def execute(self) -> FVariable:
        engine = FrancisExpression(self.context)
        url = engine.resolve(self.require_attr("url"))
        path_str = engine.resolve(self.require_attr("path"))
        mkdir = engine.resolve(self.attr("mkdir", "true")).lower() == "true"
        timeout = float(engine.resolve(self.attr("timeout", "30000"))) / 1000

        path = Path(path_str)

        if mkdir:
            path.parent.mkdir(parents=True, exist_ok=True)

        with httpx.stream("GET", url, timeout=timeout, follow_redirects=True) as response:
            response.raise_for_status()
            with path.open("wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)

        return FNodeVariable(str(path))