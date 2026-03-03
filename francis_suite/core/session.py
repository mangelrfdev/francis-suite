"""
core/session.py

FrancisSession represents a single workflow execution.
Each execution gets its own session with a unique ID,
status tracking, metrics, and an isolated variable context.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from enum import Enum
from francis_suite.core.context import FContext


class SessionStatus(Enum):
    """Possible states of a workflow execution session."""
    CREATED   = "created"    # session exists but hasn't started yet
    RUNNING   = "running"    # workflow is executing
    COMPLETED = "completed"  # workflow finished successfully
    FAILED    = "failed"     # workflow finished with an error
    CANCELLED = "cancelled"  # workflow was manually stopped


class FrancisSession:
    """
    Represents a single workflow execution.

    Created by the Runtime when a workflow starts.
    Holds the execution context, status, and metrics.

    Usage:
        session = FrancisSession()
        session.start()
        # ... execution happens ...
        session.complete()

        print(session.id)        # UUID string
        print(session.duration)  # seconds as float
        print(session.status)    # SessionStatus.COMPLETED
    """

    def __init__(self, workflow_name: str = "unnamed") -> None:
        self._id = str(uuid.uuid4())
        self._workflow_name = workflow_name
        self._status = SessionStatus.CREATED
        self._context = FContext()

        self._created_at: datetime = datetime.now(timezone.utc)
        self._started_at: datetime | None = None
        self._finished_at: datetime | None = None
        self._error: Exception | None = None

    # --- Identity ---

    @property
    def id(self) -> str:
        """Unique identifier for this session."""
        return self._id

    @property
    def workflow_name(self) -> str:
        return self._workflow_name

    # --- Status ---

    @property
    def status(self) -> SessionStatus:
        return self._status

    def is_running(self) -> bool:
        return self._status == SessionStatus.RUNNING

    def is_finished(self) -> bool:
        return self._status in (
            SessionStatus.COMPLETED,
            SessionStatus.FAILED,
            SessionStatus.CANCELLED,
        )

    # --- Lifecycle ---

    def start(self) -> None:
        """Mark the session as started."""
        if self._status != SessionStatus.CREATED:
            raise RuntimeError(
                f"Cannot start session '{self._id}' "
                f"— current status is {self._status.value}"
            )
        self._status = SessionStatus.RUNNING
        self._started_at = datetime.now(timezone.utc)

    def complete(self) -> None:
        """Mark the session as successfully completed."""
        self._status = SessionStatus.COMPLETED
        self._finished_at = datetime.now(timezone.utc)

    def fail(self, error: Exception) -> None:
        """Mark the session as failed with an error."""
        self._status = SessionStatus.FAILED
        self._finished_at = datetime.now(timezone.utc)
        self._error = error

    def cancel(self) -> None:
        """Mark the session as cancelled."""
        self._status = SessionStatus.CANCELLED
        self._finished_at = datetime.now(timezone.utc)

    # --- Metrics ---

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def started_at(self) -> datetime | None:
        return self._started_at

    @property
    def finished_at(self) -> datetime | None:
        return self._finished_at

    @property
    def duration(self) -> float | None:
        """
        Execution duration in seconds.
        Returns None if the session hasn't started or finished yet.
        """
        if self._started_at is None or self._finished_at is None:
            return None
        delta = self._finished_at - self._started_at
        return delta.total_seconds()

    @property
    def error(self) -> Exception | None:
        """The error that caused the session to fail, if any."""
        return self._error

    # --- Context ---

    @property
    def context(self) -> FContext:
        """The variable context for this session."""
        return self._context

    # --- Representation ---

    def __repr__(self) -> str:
        return (
            f"FrancisSession("
            f"id={self._id[:8]}..., "
            f"workflow={self._workflow_name!r}, "
            f"status={self._status.value}"
            f")"
        )