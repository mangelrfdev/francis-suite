"""
hands/core/httpx_introspect.py

Read last httpx response stored on the session (httpx-call or set-proxy probe).
"""

from __future__ import annotations

import json

from francis_suite.core.expressions import FrancisExpression
from francis_suite.core.registry import hand
from francis_suite.core.session import FrancisSession
from francis_suite.core.variables import FVariable, FNodeVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


def _require_last_response(session: FrancisSession):
    session.ensure_httpx_hands_allowed()
    r = session.get_last_httpx_response()
    if r is None:
        raise ValueError(
            "No httpx response recorded for this session yet. "
            "Run <httpx-call> or a <set-proxy> probe first."
        )
    return r


@hand(tag="httpx-last-status")
class HttpxLastStatusHand(AbstractHand):
    """
    Returns the HTTP status code of the last httpx response (string).

    Example:
        <box-def name="code"><httpx-last-status/></box-def>
    """

    def execute(self) -> FVariable:
        r = _require_last_response(self.session)
        return FNodeVariable(str(r.status_code))


@hand(tag="httpx-get-headers")
class HttpxGetHeadersHand(AbstractHand):
    """
    Returns response headers from the last httpx request.

    Without name: JSON object of all headers (string), easy to parse.
    With name: single header value (first match; header names are case-insensitive).

    Attributes:
        name (optional): header name to return only that value.
    """

    def execute(self) -> FVariable:
        r = _require_last_response(self.session)
        engine = FrancisExpression(self.context)
        name = (self.attr("name", "") or "").strip()
        if name:
            name = engine.resolve(name)
            val = r.headers.get(name)
            if val is None:
                return FEmptyVariable()
            return FNodeVariable(val)
        hdrs = {k: v for k, v in r.headers.items()}
        return FNodeVariable(json.dumps(hdrs, ensure_ascii=False))


@hand(tag="httpx-get-cookies")
class HttpxGetCookiesHand(AbstractHand):
    """
    Returns cookies from the last httpx response.

    Without name: JSON object mapping cookie name -> value (last wins if duplicates).
    With name: value for that cookie name, or empty if missing.

    Note: httpx exposes a flat name->value view on this response. Cookies that differ
    only by domain/path may collide; for precise jar inspection a future hand could
    add cookie-domain / cookie-path attributes.

    Attributes:
        name (optional): cookie name to return only that value.
    """

    def execute(self) -> FVariable:
        r = _require_last_response(self.session)
        engine = FrancisExpression(self.context)
        name = (self.attr("name", "") or "").strip()
        if name:
            name = engine.resolve(name)
            val = r.cookies.get(name)
            if val is None:
                return FEmptyVariable()
            return FNodeVariable(str(val))
        jar = dict(r.cookies)
        return FNodeVariable(json.dumps(jar, ensure_ascii=False))
