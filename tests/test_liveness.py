"""
Tests for session deadline, session-pulse (liveness), and RSS limits.
"""

from unittest.mock import MagicMock, patch

from francis_suite.core.liveness import LivenessError, SessionRssLimitError
from francis_suite.core.parser import FParser
from francis_suite.core.runtime import FRuntime
from francis_suite.core.session import SessionStatus


def test_session_deadline_blocks_second_hand():
    """After session-deadline-ms, the next hand must not start."""
    xml = """
    <francis-workflow session-deadline-ms="25">
        <sleep ms="40"/>
        <log>too late</log>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-deadline")

    assert session.status == SessionStatus.FAILED
    assert session.error is not None
    assert isinstance(session.error, LivenessError)
    assert "deadline" in str(session.error).lower()


def test_session_deadline_allows_short_workflow():
    xml = """
    <francis-workflow session-deadline-ms="5000">
        <log>ok</log>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-deadline-ok")

    assert session.status == SessionStatus.COMPLETED


def test_session_pulse_smoke():
    xml = """
    <francis-workflow silence-limit-ms="5000">
        <session-pulse/>
        <log>ok</log>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-pulse")

    assert session.status == SessionStatus.COMPLETED


def test_silence_limit_aborts_long_single_hand():
    """If one hand blocks longer than silence-limit-ms without new pulses, session fails."""
    xml = """
    <francis-workflow silence-limit-ms="100">
        <sleep ms="400"/>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-silence-abort")

    assert session.status == SessionStatus.FAILED
    assert session.error is not None
    assert isinstance(session.error, LivenessError)
    assert "silence" in str(session.error).lower()


def test_automatic_pulse_prevents_silence_abort_across_hands():
    """Each hand starts with an automatic pulse; short sequential hands stay under silence limit."""
    xml = """
    <francis-workflow silence-limit-ms="500">
        <sleep ms="50"/>
        <sleep ms="50"/>
        <sleep ms="50"/>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-silence-ok")

    assert session.status == SessionStatus.COMPLETED


@patch("francis_suite.core.liveness.psutil.Process")
def test_session_rss_limit_fails(mock_process_class):
    """Mock high RSS so session-max-rss-mb trips before the second hand."""
    proc = MagicMock()
    proc.memory_info.return_value = MagicMock(rss=200 * 1024 * 1024)
    mock_process_class.return_value = proc

    xml = """
    <francis-workflow session-max-rss-mb="64">
        <log>first</log>
        <log>second</log>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-rss-limit")

    assert session.status == SessionStatus.FAILED
    assert session.error is not None
    assert isinstance(session.error, SessionRssLimitError)
    assert "rss limit exceeded" in str(session.error).lower()


@patch("francis_suite.core.liveness.psutil.Process")
def test_session_rss_warn_logs_once(mock_process_class, capsys):
    proc = MagicMock()
    proc.memory_info.return_value = MagicMock(rss=120 * 1024 * 1024)
    mock_process_class.return_value = proc

    xml = """
    <francis-workflow session-max-rss-mb="200" session-rss-warn-mb="100">
        <log>ok</log>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-rss-warn")

    assert session.status == SessionStatus.COMPLETED
    out = capsys.readouterr().out
    assert "RSS approaching limit" in out
    assert out.count("RSS approaching limit") == 1


@patch("francis_suite.core.liveness.psutil.Process")
def test_session_rss_warn_ignored_when_not_below_max(mock_process_class, capsys):
    proc = MagicMock()
    proc.memory_info.return_value = MagicMock(rss=10 * 1024 * 1024)
    mock_process_class.return_value = proc

    xml = """
    <francis-workflow session-max-rss-mb="100" session-rss-warn-mb="150">
        <log>ok</log>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-rss-warn-invalid")

    assert session.status == SessionStatus.COMPLETED
    assert "Ignoring session-rss-warn-mb" in capsys.readouterr().out


def test_session_rss_warn_without_max_is_ignored():
    """session-rss-warn-mb alone does not enable RSS watchdog."""
    xml = """
    <francis-workflow session-rss-warn-mb="10">
        <log>ok</log>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-rss-warn-only")

    assert session.status == SessionStatus.COMPLETED
