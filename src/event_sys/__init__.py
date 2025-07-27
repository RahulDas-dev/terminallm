# ruff: noqa: PLW0603
from .manager import EventManager
from .types import CancellationToken, EventHandler, EventHandlerFunc, StreamEvent, StreamEventType

# Global event manager instance
_global_event_manager: EventManager | None = None


def get_event_manager() -> EventManager:
    """Get the global event manager instance."""
    global _global_event_manager
    if _global_event_manager is None:
        _global_event_manager = EventManager()
    return _global_event_manager


async def shutdown_event_manager() -> None:
    """Shutdown the global event manager."""
    global _global_event_manager
    if _global_event_manager:
        await _global_event_manager.shutdown()
        _global_event_manager = None


__all__ = (
    "CancellationToken",
    "EventHandler",
    "EventHandlerFunc",
    "EventManager",
    "StreamEvent",
    "StreamEventType",
    "get_event_manager",
    "shutdown_event_manager",
)
