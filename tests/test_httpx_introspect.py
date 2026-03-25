"""Tests for httpx-last-status, httpx-get-headers, httpx-get-cookies."""

import httpx
import respx

from francis_suite.core.parser import FParser
from francis_suite.core.runtime import FRuntime
from francis_suite.core.session import SessionStatus


def test_httpx_last_status_and_headers():
    xml = """
    <francis-workflow>
        <httpx-call url="https://example.com/x"/>
        <box-def name="st"><httpx-last-status/></box-def>
        <box-def name="hx"><httpx-get-headers name="X-Test"/></box-def>
    </francis-workflow>
    """
    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)

    with respx.mock:
        respx.get("https://example.com/x").mock(
            return_value=httpx.Response(
                200,
                text="tea",
                headers={"X-Test": "yes"},
            )
        )
        session = runtime.run(root, workflow_name="test-introspect")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("st").to_string() == "200"
    assert session.context.get("hx").to_string() == "yes"


def test_httpx_introspect_without_request_fails():
    xml = """
    <francis-workflow>
        <box-def name="st"><httpx-last-status/></box-def>
    </francis-workflow>
    """
    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-no-req")
    assert session.status == SessionStatus.FAILED
    assert "No httpx response" in str(session.error)


def test_httpx_get_cookies_json():
    xml = """
    <francis-workflow>
        <httpx-call url="https://example.com/c"/>
        <box-def name="cj"><httpx-get-cookies/></box-def>
    </francis-workflow>
    """
    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)

    with respx.mock:
        respx.get("https://example.com/c").mock(
            return_value=httpx.Response(
                200,
                text="ok",
                headers={"Set-Cookie": "sid=abc; Path=/"},
            )
        )
        session = runtime.run(root, workflow_name="test-cookies")

    assert session.status == SessionStatus.COMPLETED
    s = session.context.get("cj").to_string()
    assert "sid" in s and "abc" in s
