"""Session cookie jar for <httpx-call auto-cookies="true"/>."""

import httpx
import respx

from francis_suite.core.parser import FParser
from francis_suite.core.runtime import FRuntime
from francis_suite.core.session import SessionStatus


def test_httpx_call_auto_cookies_carries_set_cookie():
    xml = """
    <francis-workflow>
        <httpx-call url="https://api.example.com/login" auto-cookies="true" method="POST"/>
        <httpx-call url="https://api.example.com/data" auto-cookies="true"/>
    </francis-workflow>
    """
    seen_cookie: list[str] = []

    def on_data(request: httpx.Request) -> httpx.Response:
        seen_cookie.append(request.headers.get("cookie") or request.headers.get("Cookie") or "")
        return httpx.Response(200, text="payload")

    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)

    with respx.mock:
        respx.post("https://api.example.com/login").mock(
            return_value=httpx.Response(
                200,
                text="ok",
                headers={"Set-Cookie": "sid=abc123; Path=/"},
            )
        )
        respx.get("https://api.example.com/data").mock(side_effect=on_data)
        session = runtime.run(root, workflow_name="test-auto-cookies")

    assert session.status == SessionStatus.COMPLETED
    assert seen_cookie
    c = seen_cookie[0].lower()
    assert "sid" in c and "abc123" in c


def test_httpx_call_without_auto_cookies_no_jar():
    """Two calls without auto-cookies: second request should not send first Set-Cookie."""
    xml = """
    <francis-workflow>
        <httpx-call url="https://api.example.com/login" method="POST"/>
        <httpx-call url="https://api.example.com/data"/>
    </francis-workflow>
    """
    seen_cookie: list[str] = []

    def on_data(request: httpx.Request) -> httpx.Response:
        seen_cookie.append(request.headers.get("cookie") or request.headers.get("Cookie") or "")
        return httpx.Response(200, text="payload")

    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)

    with respx.mock:
        respx.post("https://api.example.com/login").mock(
            return_value=httpx.Response(
                200,
                text="ok",
                headers={"Set-Cookie": "sid=abc123; Path=/"},
            )
        )
        respx.get("https://api.example.com/data").mock(side_effect=on_data)
        session = runtime.run(root, workflow_name="test-no-jar")

    assert session.status == SessionStatus.COMPLETED
    assert seen_cookie and seen_cookie[0] == ""
