"""
hands/core/httpx_call.py

HttpCallHand implements the <httpx-call> tag.
Makes an HTTP request and returns the response body.

Usage in XML:
    <httpx-call url="https://example.com"/>
    <httpx-call url="https://example.com" method="POST">
        <httpx-header name="Authorization">Bearer token</httpx-header>
        <httpx-param name="q">search term</httpx-param>
    </httpx-call>
"""

from __future__ import annotations
import httpx
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable
from francis_suite.hands.base import AbstractHand


VALID_METHODS = ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD")


@hand(tag="httpx-call")
class HttpCallHand(AbstractHand):
    """
    Makes an HTTP request and returns the response body.

    Attributes:
        url (required): the URL to request.
        method (optional): HTTP method. Default: GET.
        timeout (optional): seconds before timeout. Default: 30.
        charset (optional): response encoding. Default: auto-detect.

    Child tags:
        <httpx-header name="...">value</httpx-header>
        <httpx-param name="...">value</httpx-param>

    Returns:
        FNodeVariable with the response body as string.

    Example:
        <box-def var="page">
            <httpx-call url="https://example.com"/>
        </box-def>
    """

    def execute(self) -> FVariable:
        url     = self.require_attr("url")
        method  = self.attr("method", "GET").upper()
        timeout = float(self.attr("timeout", "30"))

        if method not in VALID_METHODS:
            raise ValueError(
                f"<httpx-call> invalid method '{method}'. "
                f"Valid options: {', '.join(VALID_METHODS)}"
            )

        headers, params = self._extract_children()

        response = httpx.request(
            method=method,
            url=url,
            headers=headers,
            params=params if method == "GET" else None,
            data=params if method != "GET" else None,
            timeout=timeout,
            follow_redirects=True,
        )

        response.raise_for_status()
        return FNodeVariable(response.text)

    def _extract_children(self) -> tuple[dict, dict]:
        """Extract httpx-header and httpx-param child nodes."""
        headers: dict[str, str] = {}
        params:  dict[str, str] = {}

        for child in self._node.children:
            if child.tag == "httpx-header":
                name = child.get_attr("name", "")
                value = child.text or ""
                if name:
                    headers[name] = value

            elif child.tag == "httpx-param":
                name = child.get_attr("name", "")
                value = child.text or ""
                if name:
                    params[name] = value

        return headers, params