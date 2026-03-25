"""
Tests for set-proxy and session httpx proxy / last response.
"""

import json

import httpx
import respx

from francis_suite.core.parser import FParser
from francis_suite.core.runtime import FRuntime
from francis_suite.core.session import SessionStatus
from francis_suite.core.variables import FListVariable


def test_set_proxy_local_probe_hit():
    xml = """
    <francis-workflow>
        <set-proxy client="httpx" type="local">
            <proxy-param name="url">https://probe.test/status</proxy-param>
            <proxy-param name="match-regex">(?i)ok</proxy-param>
        </set-proxy>
    </francis-workflow>
    """
    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)

    with respx.mock:
        respx.get("https://probe.test/status").mock(
            return_value=httpx.Response(200, text="<html>all OK here</html>")
        )
        session = runtime.run(root, workflow_name="test-set-proxy-local")

    assert session.status == SessionStatus.COMPLETED
    assert session.get_httpx_proxy_url() is None
    r = session.get_last_httpx_response()
    assert r is not None
    assert r.status_code == 200


def test_set_proxy_result_in_box_def():
    xml = """
    <francis-workflow>
        <box-def name="proxyResult">
            <set-proxy client="httpx" type="local">
                <proxy-param name="url">https://probe.test/status</proxy-param>
                <proxy-param name="match-regex">HELLO</proxy-param>
            </set-proxy>
        </box-def>
    </francis-workflow>
    """
    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)

    with respx.mock:
        respx.get("https://probe.test/status").mock(
            return_value=httpx.Response(200, text="HELLO world")
        )
        session = runtime.run(root, workflow_name="test-set-proxy-box")

    assert session.status == SessionStatus.COMPLETED
    result = session.context.get("proxyResult")
    assert isinstance(result, FListVariable)
    assert len(result.items) == 3
    assert result.items[0].to_string() == "true"
    assert "HELLO" in result.items[1].to_string()


def test_set_proxy_local_probe_miss():
    xml = """
    <francis-workflow>
        <box-def name="proxyResult">
            <set-proxy client="httpx" type="local">
                <proxy-param name="url">https://probe.test/status</proxy-param>
                <proxy-param name="match-regex">NEVER_MATCH_THIS</proxy-param>
            </set-proxy>
        </box-def>
    </francis-workflow>
    """
    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)

    with respx.mock:
        respx.get("https://probe.test/status").mock(
            return_value=httpx.Response(200, text="something else")
        )
        session = runtime.run(root, workflow_name="test-set-proxy-miss")

    assert session.status == SessionStatus.COMPLETED
    result = session.context.get("proxyResult")
    assert isinstance(result, FListVariable)
    assert result.items[0].to_string() == "false"


def test_set_proxy_missing_match_fails():
    xml = """
    <francis-workflow>
        <set-proxy client="httpx" type="local">
            <proxy-param name="url">https://probe.test/x</proxy-param>
        </set-proxy>
    </francis-workflow>
    """
    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)

    with respx.mock:
        respx.get("https://probe.test/x").mock(return_value=httpx.Response(200, text="x"))
        session = runtime.run(root, workflow_name="test-set-proxy-no-match")

    assert session.status == SessionStatus.FAILED
    assert session.error is not None
    assert "match-regex" in str(session.error).lower() or "match-xpath" in str(
        session.error
    ).lower()


def test_set_proxy_db_not_implemented():
    xml = """
    <francis-workflow>
        <set-proxy client="httpx" type="db">
            <proxy-param name="datasource">x</proxy-param>
            <proxy-param name="url">https://probe.test/x</proxy-param>
            <proxy-param name="match-regex">.</proxy-param>
        </set-proxy>
    </francis-workflow>
    """
    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-set-proxy-db")
    assert session.status == SessionStatus.FAILED
    assert "not implemented" in str(session.error).lower()


def test_set_proxy_file_pool(tmp_path):
    proxies = [
        {"host": "127.0.0.1", "port": 1, "scheme": "http"},
    ]
    p = tmp_path / "proxies.json"
    p.write_text(json.dumps(proxies), encoding="utf-8")

    xml = f"""
    <francis-workflow>
        <box-def name="proxyResult">
            <set-proxy client="httpx" type="file" proxy-list-path="{p.as_posix()}">
                <proxy-param name="url">https://probe.test/page</proxy-param>
                <proxy-param name="match-regex">SUCCESS</proxy-param>
            </set-proxy>
        </box-def>
    </francis-workflow>
    """
    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)

    with respx.mock:
        respx.get("https://probe.test/page").mock(
            return_value=httpx.Response(200, text="SUCCESS")
        )
        session = runtime.run(root, workflow_name="test-set-proxy-file")

    assert session.status == SessionStatus.COMPLETED
    result = session.context.get("proxyResult")
    assert isinstance(result, FListVariable)
    assert result.items[0].to_string() == "true"
    assert session.get_httpx_proxy_url() is not None
    assert "127.0.0.1:1" in session.get_httpx_proxy_url()


def test_set_proxy_api_pool():
    pool_payload = [
        {"host": "10.0.0.1", "port": 8888, "scheme": "http"},
    ]
    xml = """
    <francis-workflow>
        <box-def name="proxyResult">
            <set-proxy client="httpx" type="api">
                <proxy-param name="proxy-list-url">https://pool.test/list</proxy-param>
                <proxy-param name="url">https://probe.test/page</proxy-param>
                <proxy-param name="match-regex">OK</proxy-param>
            </set-proxy>
        </box-def>
    </francis-workflow>
    """
    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)

    with respx.mock:
        respx.get("https://pool.test/list").mock(
            return_value=httpx.Response(200, json=pool_payload)
        )
        respx.get("https://probe.test/page").mock(
            return_value=httpx.Response(200, text="OK")
        )
        session = runtime.run(root, workflow_name="test-set-proxy-api")

    assert session.status == SessionStatus.COMPLETED
    result = session.context.get("proxyResult")
    assert result.items[0].to_string() == "true"
    assert "10.0.0.1:8888" in (session.get_httpx_proxy_url() or "")


def test_httpx_call_records_last_response():
    xml = """
    <francis-workflow>
        <box-def name="page">
            <httpx-call url="https://example.com/api"/>
        </box-def>
    </francis-workflow>
    """
    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)

    with respx.mock:
        respx.get("https://example.com/api").mock(
            return_value=httpx.Response(201, text="created")
        )
        session = runtime.run(root, workflow_name="test-httpx-record")

    assert session.status == SessionStatus.COMPLETED
    r = session.get_last_httpx_response()
    assert r is not None
    assert r.status_code == 201
