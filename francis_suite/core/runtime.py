"""
core/runtime.py

FRuntime is the execution engine of Francis Suite.
It takes an FNode tree and executes each node as a hand.

This is the final step in the pipeline:
    FNode tree → Runtime → FVariable results
"""

from __future__ import annotations
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
from francis_suite.core.variables import FVariable, FEmptyVariable
# Register all built-in hands
import francis_suite.hands  # noqa: F401


class FRuntime:
    """
    Executes a parsed workflow (FNode tree).

    Usage:
        runtime = FRuntime()
        session = runtime.run(root_node, workflow_name="my-workflow")
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
        Returns the session with final status and metrics.

        Always returns a session — never raises.
        Check session.status and session.error for results.
        """
        session = FrancisSession(workflow_name=workflow_name)
        session.start()

        self._bus.emit(SessionStartedEvent(
            session_id=session.id,
            workflow_name=workflow_name,
        ))

        try:
            self._execute_children(root, session)
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

        return session

    def execute_node(self, node: FNode, session: FrancisSession) -> FVariable:
        """
        Execute a single FNode as a hand.
        Emits HandStarted and HandCompleted/HandFailed events.
        """
        self._bus.emit(HandStartedEvent(
            session_id=session.id,
            tag=node.tag,
            source_line=node.source_line,
        ))

        try:
            hand_class = self._registry.require(node.tag)
            hand = hand_class(node, session, self)
            result = hand.execute()

            self._bus.emit(HandCompletedEvent(
                session_id=session.id,
                tag=node.tag,
            ))

            return result

        except Exception as e:
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
        for child in node.children:
            result = self.execute_node(child, session)
        return result