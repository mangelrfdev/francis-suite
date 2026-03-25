"""httpx-close blocks httpx user hands until set-proxy completes again."""

import httpx
import respx

from francis_suite.core.parser import FParser
from francis_suite.core.runtime import FRuntime
from francis_suite.core.session import SessionStatus


def test_httpx_close_blocks_auto_cookies_until_set_proxy():
    xml = """
    <francis-workflow>
        <httpx-call url="https://api.example.com/login" auto-cookies="true" method="POST"/>
        <httpx-close/>
        <httpx-call url="https://api.example.com/data" auto-cookies="true"/>
    </francis-workflow>
    """
    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)

    with respx.mock:
        respx.post("https://api.example.com/login").mock(return_value=httpx.Response(200, text="ok"))
        respx.get("https://api.example.com/data").mock(return_value=httpx.Response(200, text="x"))
        session = runtime.run(root, workflow_name="test-close-block")

    assert session.status == SessionStatus.FAILED
    err = str(session.error).lower()
    assert "httpx-close" in err and "set-proxy" in err


def test_httpx_close_blocks_plain_httpx_call_until_set_proxy():
    xml = """
    <francis-workflow>
        <httpx-call url="https://api.example.com/login"/>
        <httpx-close/>
        <httpx-call url="https://api.example.com/data"/>
    </francis-workflow>
    """
    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)

    with respx.mock:
        respx.get("https://api.example.com/login").mock(return_value=httpx.Response(200, text="ok"))
        respx.get("https://api.example.com/data").mock(return_value=httpx.Response(200, text="x"))
        session = runtime.run(root, workflow_name="test-close-plain")

    assert session.status == SessionStatus.FAILED
    err = str(session.error).lower()
    assert "httpx-close" in err and "set-proxy" in err


def test_httpx_close_blocks_introspect_until_set_proxy():
    xml = """
    <francis-workflow>
        <httpx-call url="https://api.example.com/login"/>
        <httpx-close/>
        <box-def name="st"><httpx-last-status/></box-def>
    </francis-workflow>
    """
    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)

    with respx.mock:
        respx.get("https://api.example.com/login").mock(return_value=httpx.Response(200, text="ok"))
        session = runtime.run(root, workflow_name="test-close-introspect")

    assert session.status == SessionStatus.FAILED
    err = str(session.error).lower()
    assert "httpx-close" in err and "set-proxy" in err


def test_set_proxy_reopens_after_httpx_close():
    xml = """
    <francis-workflow>
        <httpx-call url="https://api.example.com/login" auto-cookies="true" method="POST"/>
        <httpx-close/>
        <set-proxy client="httpx" type="local">
            <proxy-param name="url">https://probe.test/p</proxy-param>
            <proxy-param name="match-regex">OK</proxy-param>
        </set-proxy>
        <httpx-call url="https://api.example.com/data" auto-cookies="true"/>
    </francis-workflow>
    """
    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)

    with respx.mock:
        respx.post("https://api.example.com/login").mock(return_value=httpx.Response(200, text="ok"))
        respx.get("https://probe.test/p").mock(return_value=httpx.Response(200, text="OK"))
        respx.get("https://api.example.com/data").mock(return_value=httpx.Response(200, text="ok"))
        session = runtime.run(root, workflow_name="test-setproxy-reopen")

    assert session.status == SessionStatus.COMPLETED
