"""
hands/core/httpx_call.py

HttpCallHand implements the <httpx-call> tag.
Makes an HTTP request and returns the response body.

Usage in XML:
    <httpx-call url="https://example.com"/>
    <httpx-call url="https://example.com" method="POST" timeout="30000">
        <httpx-header name="Authorization">Bearer token</httpx-header>
        <httpx-param name="q">search term</httpx-param>
    </httpx-call>

    <!-- binary — PDF, Excel, images, ZIP -->
    <box-def name="reporte">
        <httpx-call url="https://example.com/report.pdf" response="binary"/>
    </box-def>
    <file-write path="downloads/report.pdf" encoding="binary">
        <box name="reporte"/>
    </file-write>

    <!-- stream — large files, video, audio (+50MB) -->
    <httpx-call url="https://example.com/video.mp4" response="stream" path="downloads/video.mp4"/>
"""

from __future__ import annotations
from pathlib import Path
import httpx
from francis_suite.core.expressions import FrancisExpression
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


VALID_METHODS = ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD")
VALID_RESPONSES = ("text", "binary", "stream")
STREAM_CHUNK_SIZE = 1024 * 1024  # 1MB chunks


@hand(tag="httpx-call")
class HttpCallHand(AbstractHand):
    """
    Makes an HTTP request and returns the response body.

    Attributes:
        url (required): the URL to request.
        method (optional): HTTP method. Default: GET.
        timeout (optional): timeout in milliseconds. Default: 30000.
        response (optional): response format. Default: text.
            text   — returns response as string. For HTML, XML, JSON, CSV.
            binary — returns response as bytes. For PDF, Excel, images, ZIP.
            stream — writes response directly to disk in chunks. For large files (+50MB).
        path (optional): destination path — required when response="stream".

    Child tags:
        <httpx-header name="...">value</httpx-header>
        <httpx-param name="...">value</httpx-param>

    Returns:
        response="text"   — FNodeVariable with response body as string.
        response="binary" — FNodeVariable with response body as bytes.
        response="stream" — FNodeVariable with the path where file was saved.

    Examples:
        <!-- text — default -->
        <box-def name="page">
            <httpx-call url="https://example.com"/>
        </box-def>

        <!-- binary — PDF, Excel, images -->
        <box-def name="reporte">
            <httpx-call url="https://example.com/report.pdf" response="binary"/>
        </box-def>
        <file-write path="downloads/report.pdf" encoding="binary">
            <box name="reporte"/>
        </file-write>

        <!-- stream — large files, video, audio -->
        <httpx-call url="https://example.com/video.mp4" response="stream" path="downloads/video.mp4"/>
    """

    def execute(self) -> FVariable:
        engine   = FrancisExpression(self.context)
        url      = engine.resolve(self.require_attr("url"))
        method   = engine.resolve(self.attr("method", "GET")).upper()
        timeout  = float(engine.resolve(self.attr("timeout", "30000"))) / 1000
        response = engine.resolve(self.attr("response", "text")).lower()

        if method not in VALID_METHODS:
            raise ValueError(
                f"<httpx-call> invalid method '{method}'. "
                f"Valid options: {', '.join(VALID_METHODS)}"
            )

        if response not in VALID_RESPONSES:
            raise ValueError(
                f"<httpx-call> invalid response '{response}'. "
                f"Valid options: {', '.join(VALID_RESPONSES)}"
            )

        headers, params = self._extract_children()

        if response == "stream":
            return self._execute_stream(engine, url, method, timeout, headers, params)

        http_response = httpx.request(
            method=method,
            url=url,
            headers=headers,
            params=params if method == "GET" else None,
            data=params if method != "GET" else None,
            timeout=timeout,
            follow_redirects=True,
        )

        http_response.raise_for_status()

        if response == "binary":
            return FNodeVariable(http_response.content)

        return FNodeVariable(http_response.text)

    def _execute_stream(
        self,
        engine: FrancisExpression,
        url: str,
        method: str,
        timeout: float,
        headers: dict,
        params: dict,
    ) -> FVariable:
        """
        Download a large file in chunks and write directly to disk.
        Uses a .tmp file during download to detect incomplete downloads.
        On success, renames .tmp to final path.
        On failure, .tmp remains on disk — final file is never created.
        """
        path_str = engine.resolve(self.require_attr("path"))
        path = Path(path_str)
        tmp_path = path.with_suffix(path.suffix + ".tmp")

        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with httpx.stream(
                method=method,
                url=url,
                headers=headers,
                params=params if method == "GET" else None,
                data=params if method != "GET" else None,
                timeout=timeout,
                follow_redirects=True,
            ) as http_response:
                http_response.raise_for_status()
                with tmp_path.open("wb") as f:
                    for chunk in http_response.iter_bytes(chunk_size=STREAM_CHUNK_SIZE):
                        f.write(chunk)

            # rename .tmp to final path only when download is complete
            tmp_path.rename(path)

        except Exception:
            # remove incomplete .tmp file if something went wrong
            if tmp_path.exists():
                tmp_path.unlink()
            raise

        return FNodeVariable(path.as_posix())

    def _extract_children(self) -> tuple[dict, dict]:
        """Extract httpx-header and httpx-param child nodes."""
        engine  = FrancisExpression(self.context)
        headers: dict[str, str] = {}
        params:  dict[str, str] = {}

        for child in self._node.children:
            if child.tag == "httpx-header":
                name  = child.get_attr("name", "")
                value = engine.resolve(child.text or "")
                if name:
                    headers[name] = value

            elif child.tag == "httpx-param":
                name  = child.get_attr("name", "")
                value = engine.resolve(child.text or "")
                if name:
                    params[name] = value

        return headers, params
