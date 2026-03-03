"""
core/events.py

Simple publish/subscribe event system for Francis Suite.
The runtime emits events during execution. Any part of the
system can subscribe to these events and react accordingly.

Example:
    bus = EventBus()

    @bus.on(SessionStartedEvent)
    def handle_start(event):
        print(f"Session {event.session_id} started")

    bus.emit(SessionStartedEvent(session_id="abc-123"))
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Type, TypeVar

E = TypeVar("E", bound="FrancisEvent")


# ---------------------------------------------------------------------------
# Base event
# ---------------------------------------------------------------------------

@dataclass
class FrancisEvent:
    """Base class for all Francis Suite events."""
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ---------------------------------------------------------------------------
# Session events
# ---------------------------------------------------------------------------

@dataclass
class SessionStartedEvent(FrancisEvent):
    """Emitted when a session starts executing."""
    session_id: str = ""
    workflow_name: str = ""


@dataclass
class SessionCompletedEvent(FrancisEvent):
    """Emitted when a session finishes successfully."""
    session_id: str = ""
    duration: float = 0.0


@dataclass
class SessionFailedEvent(FrancisEvent):
    """Emitted when a session finishes with an error."""
    session_id: str = ""
    error: str = ""


@dataclass
class SessionCancelledEvent(FrancisEvent):
    """Emitted when a session is manually cancelled."""
    session_id: str = ""


# ---------------------------------------------------------------------------
# Hand events
# ---------------------------------------------------------------------------

@dataclass
class HandStartedEvent(FrancisEvent):
    """Emitted when a hand begins execution."""
    session_id: str = ""
    tag: str = ""
    source_line: int | None = None


@dataclass
class HandCompletedEvent(FrancisEvent):
    """Emitted when a hand finishes successfully."""
    session_id: str = ""
    tag: str = ""


@dataclass
class HandFailedEvent(FrancisEvent):
    """Emitted when a hand raises an exception."""
    session_id: str = ""
    tag: str = ""
    error: str = ""


# ---------------------------------------------------------------------------
# Event bus
# ---------------------------------------------------------------------------

class EventBus:
    """
    Central event dispatcher.
    Listeners subscribe to specific event types.
    The runtime emits events as execution progresses.

    Usage:
        bus = EventBus()

        @bus.on(SessionStartedEvent)
        def on_start(event):
            print(f"Started: {event.session_id}")

        bus.emit(SessionStartedEvent(session_id="abc"))
    """

    def __init__(self) -> None:
        self._listeners: dict[type, list[Callable]] = {}

    def on(self, event_type: Type[E]) -> Callable:
        """
        Decorator that registers a listener for an event type.

        Usage:
            @bus.on(SessionStartedEvent)
            def handle(event: SessionStartedEvent):
                ...
        """
        def decorator(fn: Callable) -> Callable:
            self._listeners.setdefault(event_type, []).append(fn)
            return fn
        return decorator

    def subscribe(self, event_type: Type[E], listener: Callable) -> None:
        """Register a listener without using the decorator."""
        self._listeners.setdefault(event_type, []).append(listener)

    def unsubscribe(self, event_type: Type[E], listener: Callable) -> None:
        """Remove a previously registered listener."""
        if event_type in self._listeners:
            self._listeners[event_type].remove(listener)

    def emit(self, event: FrancisEvent) -> None:
        """
        Emit an event. All listeners for this event type are called
        in the order they were registered.
        Exceptions in listeners are silently ignored to avoid
        breaking the execution pipeline.
        """
        listeners = self._listeners.get(type(event), [])
        for listener in listeners:
            try:
                listener(event)
            except Exception:
                pass

    def clear(self) -> None:
        """Remove all listeners. Useful in tests."""
        self._listeners.clear()

    def __repr__(self) -> str:
        total = sum(len(v) for v in self._listeners.values())
        return f"EventBus({len(self._listeners)} event types, {total} listeners)"