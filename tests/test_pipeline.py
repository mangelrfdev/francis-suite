"""
tests/test_pipeline.py

End-to-end test of the full execution pipeline.
Tests that a workflow XML can be parsed and executed correctly.
"""

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