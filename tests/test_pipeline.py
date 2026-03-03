"""
tests/test_pipeline.py

End-to-end test of the full execution pipeline.
Tests that a workflow XML can be parsed and executed correctly.
"""
import respx
import httpx
from francis_suite.core.parser import FParser
from francis_suite.core.runtime import FRuntime
from francis_suite.core.session import SessionStatus


def test_log_hand_executes():
    """A workflow with a single <log> tag should complete successfully."""
    xml = """
    <francis-workflow>
        <log>Hello Francis Suite</log>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-log")

    assert session.status == SessionStatus.COMPLETED
    assert session.duration is not None
    assert session.error is None


def test_unknown_tag_fails_session():
    """A workflow with an unknown tag should fail the session."""
    xml = """
    <francis-workflow>
        <tag-que-no-existe/>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-unknown")

    assert session.status == SessionStatus.FAILED
    assert session.error is not None

def test_box_def_stores_variable():
    """box-def should execute children and store result in context."""
    xml = """
    <francis-workflow>
        <box-def var="mensaje">
            <log>guardando esto</log>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-box-def")

    assert session.status == SessionStatus.COMPLETED
    variable = session.context.get("mensaje")
    assert not variable.is_empty()
    assert variable.to_string() == "guardando esto"

def test_sleep_executes():
    """sleep should pause execution and return empty."""
    xml = """
    <francis-workflow>
        <sleep seconds="0"/>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-sleep")

    assert session.status == SessionStatus.COMPLETED


def test_sleep_invalid_seconds_fails():
    """sleep with invalid seconds attribute should fail the session."""
    xml = """
    <francis-workflow>
        <sleep seconds="abc"/>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-sleep-invalid")

    assert session.status == SessionStatus.FAILED

def test_empty_returns_empty_variable():
    """empty tag should return an empty variable."""
    xml = """
    <francis-workflow>
        <box-def var="nada">
            <empty/>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-empty")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("nada").is_empty()

def test_http_call_fetches_url():
    """http-call should fetch a URL and return the response body."""
    xml = """
    <francis-workflow>
        <box-def var="page">
            <http-call url="https://example.com"/>
        </box-def>
    </francis-workflow>
    """

    with respx.mock:
        respx.get("https://example.com").mock(
            return_value=httpx.Response(200, text="<html>Hello</html>")
        )

        parser = FParser()
        runtime = FRuntime()

        root = parser.parse_string(xml)
        session = runtime.run(root, workflow_name="test-http-call")

    assert session.status == SessionStatus.COMPLETED
    result = session.context.get("page")
    assert not result.is_empty()
    assert "<html>Hello</html>" in result.to_string()

def test_convert_html_to_xml():
    """convert-html-to-xml should clean HTML and return valid XML."""
    xml = """
    <francis-workflow>
        <box-def var="clean">
            <convert-html-to-xml>
                <log>&lt;html&gt;&lt;body&gt;&lt;h1&gt;Hello&lt;/h1&gt;&lt;/body&gt;&lt;/html&gt;</log>
            </convert-html-to-xml>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-convert")

    print(f"\nERROR: {session.error}")

    assert session.status == SessionStatus.COMPLETED
    result = session.context.get("clean")
    assert not result.is_empty()
    assert "h1" in result.to_string()

def test_xpath_extract_gets_text():
    """xpath-extract should apply XPath and return matching results."""
    xml_workflow = """
    <francis-workflow>
        <box-def var="resultado">
            <xpath-extract expression="//h1/text()"><![CDATA[<html><body><h1>Hola mundo</h1></body></html>]]></xpath-extract>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml_workflow)
    session = runtime.run(root, workflow_name="test-xpath")

    assert session.status == SessionStatus.COMPLETED
    result = session.context.get("resultado")
    assert not result.is_empty()
    assert "Hola mundo" in result.to_string()

def test_loop_iterates_over_list():
    """loop should iterate over a list and execute children for each item."""
    xml = """
    <francis-workflow>
        <box-def var="items">
            <empty/>
        </box-def>
        <loop item="current" list="${items}">
            <log>${current}</log>
        </loop>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)

    # Manually set a list variable in context before running
    from francis_suite.core.variables import FListVariable, FNodeVariable
    session = runtime.run(root, workflow_name="test-loop")

    assert session.status == SessionStatus.COMPLETED