"""
core/liveness.py

Session liveness: optional wall-clock deadline, silence (inactivity) watchdog,
and optional process RSS (resident set size) limit.

  - session-deadline-ms — wall clock from session start.
  - silence-limit-ms — abort if no progress for this many ms (watchdog thread).
  - session-max-rss-mb — abort if process RSS exceeds this many MB (watchdog + hand boundaries).
  - session-rss-warn-mb — optional; one [SESSION] log when RSS reaches this (must be < max).
  - Automatic progress at each hand boundary (FRuntime.execute_node) + optional
    <session-pulse/> for extra pulses inside long stretches.

See docs/roadmap.md — Liveness, límites y operación.
"""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime, timezone

import psutil

from francis_suite.core.expressions import FrancisExpression
from francis_suite.core.nodes import FNode
from francis_suite.core.session import FrancisSession


class LivenessError(RuntimeError):
    """Raised when session deadline or silence limit is exceeded."""


class SessionRssLimitError(LivenessError):
    """Raised when session-max-rss-mb is exceeded."""


def _parse_positive_ms(raw: str | None, default: int | None) -> int | None:
    if raw is None or raw == "":
        return default
    try:
        v = int(raw)
    except ValueError:
        return default
    if v <= 0:
        return default
    return v


def _parse_positive_mb(raw: str | None) -> float | None:
    if raw is None or raw == "":
        return None
    try:
        v = float(raw)
    except ValueError:
        return None
    if v <= 0:
        return None
    return v


class SessionLiveness:
    """
    Configured from <francis-workflow> attributes; driven by FRuntime.
    """

    def __init__(self, session: FrancisSession) -> None:
        self._session = session
        self._deadline_ms: int | None = None
        self._silence_ms: int | None = None
        self._max_rss_mb: float | None = None
        self._warn_rss_mb: float | None = None

        self._last_progress_monotonic: float | None = None

        self._pending_error: Exception | None = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

        self._rss_warn_logged: bool = False
        self._rss_unavailable_logged: bool = False

    @property
    def enabled(self) -> bool:
        return (
            self._deadline_ms is not None
            or self._silence_ms is not None
            or self._max_rss_mb is not None
        )

    def configure_from_root(self, root: FNode) -> None:
        """Read liveness and RSS limit attributes from the workflow root."""
        attrs = root.attrs
        self._deadline_ms = _parse_positive_ms(
            attrs.get("session-deadline-ms"), None
        )
        self._silence_ms = _parse_positive_ms(
            attrs.get("silence-limit-ms"), None
        )

        max_mb = _parse_positive_mb(attrs.get("session-max-rss-mb"))
        warn_mb = _parse_positive_mb(attrs.get("session-rss-warn-mb"))
        if max_mb is None:
            warn_mb = None
        elif warn_mb is not None and warn_mb >= max_mb:
            print(
                "[SESSION] Ignoring session-rss-warn-mb: must be less than "
                "session-max-rss-mb."
            )
            warn_mb = None
        self._max_rss_mb = max_mb
        self._warn_rss_mb = warn_mb

    def on_session_start(self) -> None:
        """Call once after session.start() when liveness is active."""
        if not self.enabled:
            return
        with self._lock:
            self._last_progress_monotonic = None
            self._rss_warn_logged = False
            self._rss_unavailable_logged = False

    def start_watch_thread(self) -> None:
        if (
            self._deadline_ms is None
            and self._silence_ms is None
            and self._max_rss_mb is None
        ):
            return
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._watch_loop,
            name="francis-liveness",
            daemon=True,
        )
        self._thread.start()

    def stop_watch_thread(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def raise_if_violation(self) -> None:
        """Call from the main thread before starting a hand."""
        with self._lock:
            err = self._pending_error
            self._pending_error = None
        if err is not None:
            raise err

    def record_progress(self) -> None:
        """Mark progress for future silence-limit-ms (e.g. <session-pulse/>)."""
        if not self.enabled:
            return
        with self._lock:
            self._last_progress_monotonic = time.monotonic()

    def before_hand(self, node: FNode, engine: FrancisExpression) -> None:
        if not self.enabled:
            return
        self.raise_if_violation()
        self._check_session_deadline_sync()
        self._check_session_rss_sync()

    def after_hand(self, success: bool) -> None:
        if not self.enabled:
            return
        if success:
            # Successful hand completion counts as progress (tightens gap between hands).
            with self._lock:
                self._last_progress_monotonic = time.monotonic()

    # --- internals ---

    def _check_session_deadline_sync(self) -> None:
        if self._deadline_ms is None:
            return
        started = self._session.started_at
        if started is None:
            return
        now = datetime.now(timezone.utc)
        elapsed_ms = (now - started).total_seconds() * 1000.0
        if elapsed_ms > self._deadline_ms:
            raise LivenessError(
                f"Session deadline exceeded: limit {self._deadline_ms} ms, "
                f"elapsed {elapsed_ms:.0f} ms."
            )

    def _get_rss_mb(self) -> float | None:
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            return None

    def _apply_rss_limits(self) -> None:
        """Warn once and/or raise if RSS exceeds session-max-rss-mb."""
        if self._max_rss_mb is None:
            return
        rss_mb = self._get_rss_mb()
        if rss_mb is None:
            with self._lock:
                if not self._rss_unavailable_logged:
                    print(
                        "[SESSION] session-max-rss-mb is set but RSS sampling failed "
                        "(psutil error); limit not enforced."
                    )
                    self._rss_unavailable_logged = True
            return

        if rss_mb >= self._max_rss_mb:
            raise SessionRssLimitError(
                f"Session RSS limit exceeded: current {rss_mb:.1f} MB, "
                f"limit {self._max_rss_mb} MB."
            )

        with self._lock:
            if (
                self._warn_rss_mb is not None
                and rss_mb >= self._warn_rss_mb
                and not self._rss_warn_logged
            ):
                print(
                    f"[SESSION] RSS approaching limit: current {rss_mb:.1f} MB, "
                    f"warn at {self._warn_rss_mb} MB, hard limit {self._max_rss_mb} MB"
                )
                self._rss_warn_logged = True

    def _check_session_rss_sync(self) -> None:
        if self._max_rss_mb is None:
            return
        self._apply_rss_limits()

    def _watch_loop(self) -> None:
        interval = 0.25
        if self._silence_ms is not None:
            interval = min(interval, max(0.05, self._silence_ms / 2000.0))
        if self._deadline_ms is not None:
            interval = min(interval, max(0.05, self._deadline_ms / 4000.0))
        while not self._stop.wait(interval):
            try:
                self._tick()
            except Exception as e:
                with self._lock:
                    if self._pending_error is None:
                        self._pending_error = e
                return

    def _tick(self) -> None:
        with self._lock:
            if self._session.is_finished():
                return

            now_m = time.monotonic()
            now_wall = datetime.now(timezone.utc)

            if self._deadline_ms is not None:
                started = self._session.started_at
                if started is not None:
                    elapsed_ms = (now_wall - started).total_seconds() * 1000.0
                    if elapsed_ms > self._deadline_ms:
                        raise LivenessError(
                            f"Session deadline exceeded: limit {self._deadline_ms} ms, "
                            f"elapsed {elapsed_ms:.0f} ms."
                        )

            if self._silence_ms is not None:
                last = self._last_progress_monotonic
                if last is not None:
                    silence_ms = (now_m - last) * 1000.0
                    if silence_ms > self._silence_ms:
                        raise LivenessError(
                            f"Silence limit exceeded: no progress for {silence_ms:.0f} ms "
                            f"(limit {self._silence_ms} ms)."
                        )

        if self._max_rss_mb is not None:
            self._apply_rss_limits()
