"""
hands/core/httpx_cookie_jar.py

Control the session-scoped httpx.Client used by <httpx-call auto-cookies="true"/>.
"""

from __future__ import annotations

from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="httpx-close")
class HttpxCloseHand(AbstractHand):
    """
    Close the session cookie-jar client and drop stored cookies.

    After this, <httpx-call>, <httpx-last-status>, <httpx-get-headers>, and
    <httpx-get-cookies> raise until <set-proxy> completes again (success or failure).
    """

    def execute(self) -> FVariable:
        self.session.apply_httpx_close()
        return FEmptyVariable()
