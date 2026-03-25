"""Tests for box-def / shared-box-def item index into FListVariable."""

from francis_suite.core.parser import FParser
from francis_suite.core.runtime import FRuntime
from francis_suite.core.session import SessionStatus
from francis_suite.core.variables import FNodeVariable


def test_box_def_item_extracts_from_list():
    xml = """
    <francis-workflow>
        <box-def name="lst">
            <build-list>
                <log>alpha</log>
                <log>beta</log>
                <log>gamma</log>
            </build-list>
        </box-def>
        <box-def name="second" item="2">
            <box name="lst"/>
        </box-def>
    </francis-workflow>
    """
    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-box-item")
    assert session.status == SessionStatus.COMPLETED
    v = session.context.get("second")
    assert isinstance(v, FNodeVariable)
    assert v.to_string() == "beta"


def test_shared_box_def_item_from_shared_list():
    xml = """
    <francis-workflow>
        <shared-box-def name="lst" replace="true">
            <build-list>
                <log>1</log>
                <log>2</log>
            </build-list>
        </shared-box-def>
        <shared-box-def name="last" replace="true" item="2">
            <shared-box name="lst"/>
        </shared-box-def>
    </francis-workflow>
    """
    parser = FParser()
    runtime = FRuntime()
    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-shared-item")
    assert session.status == SessionStatus.COMPLETED
    v = session.context.get_shared_box("last")
    assert v.to_string() == "2"
