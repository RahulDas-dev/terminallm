import logging

from lib.base_types import ServerStreamEvent, StreamEventType


# Convenience classes for common event handling patterns
class EventCollector:
    """Collects events for batch processing or analysis."""

    def __init__(self, max_events: int = 1000):
        self.events: list[ServerStreamEvent] = []
        self.max_events = max_events

    async def handle_event(self, event: ServerStreamEvent) -> None:
        """Handle an event by collecting it."""
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events.pop(0)

    def get_events(
        self,
        event_types: list[StreamEventType] | None = None,
    ) -> list[ServerStreamEvent]:
        """Get collected events, optionally filtered by type."""
        if event_types:
            return [e for e in self.events if e.type in event_types]
        return self.events.copy()

    def clear(self) -> None:
        """Clear collected events."""
        self.events.clear()


class EventLogger:
    """Logs events for debugging and monitoring."""

    def __init__(self, logger_name: str = "llm_events"):
        self.logger = logging.getLogger(logger_name)

    async def handle_event(self, event: ServerStreamEvent) -> None:
        """Handle an event by logging it."""
        self.logger.debug(f"Event: {event.type} from {event.provider} at {event.timestamp}")

        if event.content:
            self.logger.debug(f"Content: {event.content[:100]}...")

        if event.error:
            self.logger.error(f"Error: {event.error}")
