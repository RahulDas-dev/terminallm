# ruff: noqa:  PLW0603
from collections.abc import Callable
from typing import Any


class EventEmitter:
    """Event emitter for publish/subscribe pattern."""

    def __init__(self):
        self._events: dict[str, list[Callable]] = {}

    def on(self, event_name: str, callback: Callable) -> None:
        """Subscribe to an event."""
        if event_name not in self._events:
            self._events[event_name] = []
        self._events[event_name].append(callback)

    def off(self, event_name: str, callback: Callable | None = None) -> None:
        """Unsubscribe from an event."""
        if event_name not in self._events:
            return

        if callback is None:
            self._events.pop(event_name, None)
        else:
            self._events[event_name] = [cb for cb in self._events[event_name] if cb != callback]

    def emit(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        """Emit an event with data."""
        if event_name not in self._events:
            return

        for callback in self._events[event_name]:
            callback(*args, **kwargs)


_global_event_emiter: EventEmitter | None = None


def get_event_emitter() -> EventEmitter:
    """
    Gets the global event emitter instance.
    If the emitter hasn't been initialized yet, this will return a new instance.
    """
    global _global_event_emiter

    if _global_event_emiter is None:
        _global_event_emiter = EventEmitter()

    return _global_event_emiter
