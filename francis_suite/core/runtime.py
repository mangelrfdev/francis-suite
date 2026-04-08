"""
core/runtime.py

FRuntime is the execution engine of Francis Suite.
It takes an FNode tree and executes each node as a hand.

This is the final step in the pipeline:
    FNode tree → Runtime → FVariable results
"""

from __future__ import annotations
import os
import re
from pathlib import Path

from francis_suite.core.nodes import FNode
from francis_suite.core.session import FrancisSession
from francis_suite.core.registry import HandRegistry
from francis_suite.core.events import (
    EventBus,
    SessionStartedEvent,
    SessionCompletedEvent,
    SessionFailedEvent,
    HandStartedEvent,
    HandCompletedEvent,
    HandFailedEvent,
)
from francis_suite.core.expressions import FrancisExpression
from francis_suite.core.variables import FVariable, FEmptyVariable, FNodeVariable
from francis_suite.hands.core.exit_ import ExitWorkflow
# Register all built-in hands
import francis_suite.hands  # noqa: F401


# Internal child tags — never executed directly by the runtime
_INTERNAL_TAGS = {
    # loop
    "loop-list", "loop-body",

    # regex
    "regex-pattern", "regex-input", "regex-result",

    # httpx
    "httpx-header", "httpx-param",

    # functions
    "function-param",

    # sleep
    "sleep-min", "sleep-avg", "sleep-max",
}


class FRuntime:
    """
    Executes a parsed workflow (FNode tree).

    Usage:
        runtime = FRuntime()

        # Simple run — creates a new session internally
        session = runtime.run(root_node, workflow_name="my-workflow")

        # Run with a pre-built session — useful for injecting variables before execution
        session = FrancisSession(workflow_name="my-workflow")
        session.context.set_shared_box("ciudad", FNodeVariable("santiago"))
        session = runtime.run_session(root_node, session)

        print(session.status)   # SessionStatus.COMPLETED
        print(session.duration) # 1.23
    """

    def __init__(
        self,
        registry: HandRegistry | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._registry = registry or HandRegistry.instance()
        self._bus = event_bus or EventBus()

    @property
    def event_bus(self) -> EventBus:
        """The EventBus used by this runtime."""
        return self._bus

    def run(
        self,
        root: FNode,
        workflow_name: str = "unnamed",
    ) -> FrancisSession:
        """
        Execute a workflow from its root FNode.
        Creates a new session internally.
        Returns the session with final status and metrics.

        Always returns a session — never raises.
        Check session.status and session.error for results.
        """
        session = FrancisSession(workflow_name=workflow_name)
        return self.run_session(root, session)

    def run_session(
        self,
        root: FNode,
        session: FrancisSession,
    ) -> FrancisSession:
        """
        Execute a workflow using a pre-built session.
        Useful when variables need to be injected before execution.

        Always returns the session — never raises.
        Check session.status and session.error for results.

        Usage:
            session = FrancisSession(workflow_name="my-workflow")
            session.context.set_shared_box("ciudad", FNodeVariable("santiago"))
            session = runtime.run_session(root, session)
        """
        session.start()

        # UTC timestamp when the run began (YYYY-MM-DDTHH:MM:SS), for workflows that need a real
        # clock without hardcoding. Available as ${francis_session_started_at_utc}. CLI --param
        # can still override names like scrapedAtTimestamp via shared-box-def replace="false".
        st = session.started_at
        if st is not None:
            session.context.set_shared_box(
                "francis_session_started_at_utc",
                FNodeVariable(st.strftime("%Y-%m-%dT%H:%M:%S")),
            )

        # Short unique folder token (no date): first 8 hex chars of session UUID. Use in compose as
        # ${francis_run_dir_suffix} e.g. SCRAPER_UPPERCASE_${francis_run_dir_suffix}
        rid = session.id.replace("-", "")
        session.context.set_shared_box(
            "francis_run_dir_suffix",
            FNodeVariable(rid[:8].upper()),
        )

        session.liveness.configure_from_root(root)
        session.liveness.on_session_start()
        session.liveness.start_watch_thread()

        self._bus.emit(SessionStartedEvent(
            session_id=session.id,
            workflow_name=session.workflow_name,
        ))

        try:
            self._execute_children(root, session)
            session.complete()
            self._bus.emit(SessionCompletedEvent(
                session_id=session.id,
                duration=session.duration or 0.0,
            ))
        except ExitWorkflow:
            session.complete()
            self._bus.emit(SessionCompletedEvent(
                session_id=session.id,
                duration=session.duration or 0.0,
            ))
        except Exception as e:
            session.fail(e)
            self._bus.emit(SessionFailedEvent(
                session_id=session.id,
                error=str(e),
            ))
        finally:
            self._finalize_record_journals(session)
            session.liveness.stop_watch_thread()
            session.close_http_resources()

        self._persist_private_record_metadata(session)

        return session

    def execute_node(self, node: FNode, session: FrancisSession) -> FVariable:
        """
        Execute a single FNode as a hand.
        Emits HandStarted and HandCompleted/HandFailed events.
        """
        # Internal child tags are never executed directly
        if node.tag in _INTERNAL_TAGS:
            return FEmptyVariable()

        # Automatic progress pulse so silence-limit-ms does not require <session-pulse/> on every step.
        session.liveness.record_progress()

        engine = FrancisExpression(session.context)
        session.liveness.before_hand(node, engine)

        self._bus.emit(HandStartedEvent(
            session_id=session.id,
            tag=node.tag,
            source_line=node.source_line,
        ))

        try:
            hand_class = self._registry.require(node.tag)
            hand = hand_class(node, session, self)
            result = hand.execute()
            session.liveness.raise_if_violation()

            self._bus.emit(HandCompletedEvent(
                session_id=session.id,
                tag=node.tag,
            ))

            session.liveness.after_hand(success=True)
            return result

        except ExitWorkflow:
            session.liveness.after_hand(success=True)
            raise
        except Exception as e:
            session.liveness.after_hand(success=False)
            self._bus.emit(HandFailedEvent(
                session_id=session.id,
                tag=node.tag,
                error=str(e),
            ))
            raise

    def _execute_children(
        self,
        node: FNode,
        session: FrancisSession,
    ) -> FVariable:
        """
        Execute all children of a node in order.
        Returns the result of the last child.
        """
        result: FVariable = FEmptyVariable()
        children = list(node.children)
        n = len(children)
        for i, child in enumerate(children):
            if node.tag == "francis-workflow":
                session._export_final_hand = i == n - 1
            else:
                session._export_final_hand = False
            result = self.execute_node(child, session)
        return result

    def _finalize_record_journals(self, session: FrancisSession) -> None:
        """Append journal process lines for each FRecord that uses record-journal."""
        from francis_suite.core.records import FRecord

        for _name, var in session.context.iter_shared_box_items():
            if not isinstance(var, FRecord):
                continue
            try:
                var.finalize_journal(session)
            except Exception as e:
                print(f"[RECORD] journal finalize failed: {e}")

    def _persist_private_record_metadata(self, session: FrancisSession) -> None:
        """
        After every run (success or failure), write private metadata JSON for each
        FRecord in the global context. Does not require <record-save-metadata> in XML.

        Disabled when env FRANCIS_AUTO_RECORD_METADATA is 0/false/no (e.g. tests).
        Output: sessions/<session_id>/<record_name>_private_metadata.json
        """
        flag = os.environ.get("FRANCIS_AUTO_RECORD_METADATA", "1").strip().lower()
        if flag in ("0", "false", "no"):
            return

        from francis_suite.core.records import FRecord

        base_dir = Path("sessions") / session.id
        for name, var in session.context.iter_shared_box_items():
            if not isinstance(var, FRecord):
                continue
            safe = re.sub(r"[^\w\-.]", "_", name).strip("._-") or "record"
            path = base_dir / f"{safe}_private_metadata.json"
            try:
                var.save_meta(str(path), session=session)
            except Exception as e:
                print(f"[RECORD] auto private metadata save failed for '{name}': {e}")
            custom = var.deferred_private_metadata_path
            if custom:
                try:
                    var.save_meta(custom, session=session)
                except Exception as e:
                    print(
                        f"[RECORD] deferred private metadata save failed for '{name}': {e}"
                    )
