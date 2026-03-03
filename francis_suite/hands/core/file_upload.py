"""
hands/core/file_upload.py

FileUploadHand implements the <file-upload> tag.
Uploads a local file to a URL via HTTP POST (multipart).

Usage in XML:
    <file-upload url="https://api.ejemplo.com/upload" path="data/report.pdf"/>

    <file-upload
        url="https://api.ejemplo.com/upload"
        path="data/report.pdf"
        field="file"
        method="POST"/>
"""

from __future__ import annotations
from pathlib import Path
import httpx
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="file-upload")
class FileUploadHand(AbstractHand):
    """
    Uploads a local file to a URL via HTTP multipart POST.

    Attributes:
        url (required): URL to upload to.
        path (required): local path of the file to upload.
        field (optional): form field name. Default: "file".
        method (optional): HTTP method. Default: POST.
        timeout (optional): request timeout in seconds. Default: 30.

    Returns:
        FNodeVariable with the server response body.

    Example:
        <file-upload url="https://api.ejemplo.com/upload" path="data/report.pdf"/>
    """

    def execute(self) -> FVariable:
        url = self.require_attr("url")
        path_str = self.require_attr("path")
        field = self.attr("field", "file")
        method = self.attr("method", "POST").upper()
        timeout = float(self.attr("timeout", "30"))

        path = Path(path_str)

        if not path.exists():
            raise FileNotFoundError(
                f"<file-upload> cannot find file: '{path}'"
            )

        with httpx.Client(timeout=timeout) as client:
            with path.open("rb") as f:
                response = client.request(
                    method,
                    url,
                    files={field: (path.name, f)},
                )
            response.raise_for_status()
            return FNodeVariable(response.text)