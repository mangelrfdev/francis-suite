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
from typing import TYPE_CHECKING, Any

from francis_suite.core.context import FContext

if TYPE_CHECKING:
    from francis_suite.core.liveness import SessionLiveness


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

        from francis_suite.core.liveness import SessionLiveness

        self._liveness = SessionLiveness(self)

        # httpx: optional upstream proxy URL for httpx-call / set-proxy (ADR-004)
        self._httpx_proxy_url: str | None = None
        self._last_httpx_response: Any | None = None

        # httpx.Client with cookie jar — <httpx-call auto-cookies="true"/>
        self._httpx_cookie_client: Any | None = None
        self._httpx_cookie_client_proxy_key: str | None = None
        # After <httpx-close/>: block httpx-call / introspect until <set-proxy> finishes
        self._httpx_blocked_until_set_proxy: bool = False

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

    @property
    def liveness(self) -> SessionLiveness:
        """Session deadline, silence watchdog, optional RSS limit (see docs/roadmap)."""
        return self._liveness

    # --- HTTP (httpx) — shared with set-proxy and httpx-call ---

    def get_httpx_proxy_url(self) -> str | None:
        """Upstream proxy URL for httpx (http://user:pass@host:port), or None for direct."""
        return self._httpx_proxy_url

    def set_httpx_proxy_url(self, url: str | None) -> None:
        """Replace session proxy. None means direct connection (no upstream proxy)."""
        if url != self._httpx_proxy_url:
            self._close_httpx_cookie_client()
        self._httpx_proxy_url = url

    def record_httpx_response(self, response: Any | None) -> None:
        """Store last httpx.Response (or None if no response was obtained)."""
        self._last_httpx_response = response

    def get_last_httpx_response(self) -> Any | None:
        """Last response from httpx-call or set-proxy probe, if any."""
        return self._last_httpx_response

    def ensure_httpx_hands_allowed(self) -> None:
        """
        Raise if <httpx-close/> ran and <set-proxy> has not completed since then.
        Used by httpx-call and httpx introspection hands (not by set-proxy internals).
        """
        if self._httpx_blocked_until_set_proxy:
            raise ValueError(
                "<httpx-close/> was used: run <set-proxy> again before "
                "<httpx-call>, <httpx-last-status>, <httpx-get-headers>, or "
                "<httpx-get-cookies>."
            )

    def acquire_httpx_cookie_client(self, timeout: float) -> Any:
        """
        Return a session-scoped httpx.Client that keeps cookies between requests
        (browser-like). Recreated when the session proxy URL changes.
        """
        import httpx

        self.ensure_httpx_hands_allowed()

        cur_proxy = self._httpx_proxy_url
        if (
            self._httpx_cookie_client is not None
            and self._httpx_cookie_client_proxy_key == cur_proxy
        ):
            return self._httpx_cookie_client

        self._close_httpx_cookie_client()
        kw: dict[str, Any] = {"follow_redirects": True, "timeout": timeout}
        if cur_proxy:
            kw["proxy"] = cur_proxy
        self._httpx_cookie_client = httpx.Client(**kw)
        self._httpx_cookie_client_proxy_key = cur_proxy
        return self._httpx_cookie_client

    def _close_httpx_cookie_client(self) -> None:
        c = self._httpx_cookie_client
        if c is not None:
            try:
                c.close()
            except Exception:
                pass
        self._httpx_cookie_client = None
        self._httpx_cookie_client_proxy_key = None

    def close_http_resources(self) -> None:
        """Close httpx clients held by the session (call at end of run_session)."""
        self._close_httpx_cookie_client()
        self._httpx_blocked_until_set_proxy = False

    def apply_httpx_close(self) -> None:
        """Close cookie client and require <set-proxy> before more httpx user hands."""
        self._close_httpx_cookie_client()
        self._httpx_blocked_until_set_proxy = True

    def clear_httpx_block_after_set_proxy(self) -> None:
        """Call when <set-proxy> hand completes (success or failure)."""
        self._httpx_blocked_until_set_proxy = False

    # --- Representation ---

    def __repr__(self) -> str:
        return (
            f"FrancisSession("
            f"id={self._id[:8]}..., "
            f"workflow={self._workflow_name!r}, "
            f"status={self._status.value}"
            f")"
        )