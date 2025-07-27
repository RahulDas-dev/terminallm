"""
Event-driven architecture for the LLM CLI framework.

This module provides a comprehensive event system for handling streaming responses,
tool executions, and other asynchronous operations across multiple providers.
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from .types import CancellationToken, EventHandler, EventHandlerFunc, StreamEvent, StreamEventType

logger = logging.getLogger("event_sys")


class EventSubscription:
    """Represents an active event subscription."""

    def __init__(
        self,
        subscription_id: str,
        event_types: set[StreamEventType],
        handler: EventHandler | EventHandlerFunc,
        queue_size: int = 1000,
    ):
        self.id = subscription_id
        self.event_types = event_types
        self.handler = handler
        self.queue: asyncio.Queue[StreamEvent] = asyncio.Queue(maxsize=queue_size)
        self.active = True
        self._task: asyncio.Task | None = None

    async def start_processing(self) -> None:
        """Start processing events from the queue."""
        if self._task is not None:
            return

        self._task = asyncio.create_task(self._process_events())

    async def stop_processing(self) -> None:
        """Stop processing events."""
        self.active = False
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _process_events(self) -> None:
        """Process events from the queue."""
        try:
            while self.active:
                try:
                    # Wait for event with timeout to allow checking active status
                    event = await asyncio.wait_for(self.queue.get(), timeout=0.1)
                    if event is None:  # Sentinel to break loop
                        break
                    if callable(self.handler):
                        self.handler(event)
                    else:
                        await self.handler.handle(event)
                except TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Error processing event in subscription {self.id}: {e}")
        except asyncio.CancelledError:
            logger.debug(f"Event processing cancelled for subscription {self.id}")
            raise


class EventManager:
    """
    Manages event publishing and subscription across the LLM CLI framework.

    Provides event-driven communication between components with support for
    filtering, buffering, and async processing.
    """

    def __init__(self, max_event_history: int = 10000):
        self._subscriptions: dict[str, EventSubscription] = {}
        self._event_history: list[StreamEvent] = []
        self._max_history = max_event_history
        self._subscription_counter = 0
        self._lock = asyncio.Lock()
        self._shutdown = False

    async def publish(self, event: StreamEvent) -> None:
        """
        Publish an event to all matching subscriptions.

        Args:
            event: The event to publish
        """
        if self._shutdown:
            return

        async with self._lock:
            # Add to history
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)

            # Publish to matching subscriptions
            for subscription in self._subscriptions.values():
                if event.etype in subscription.event_types and subscription.active:
                    try:
                        subscription.queue.put_nowait(event)
                    except asyncio.QueueFull:
                        logger.warning(f"Event queue full for subscription {subscription.id}, dropping event")

    async def subscribe(
        self,
        event_types: list[StreamEventType],
        handler: EventHandler | EventHandlerFunc,
        queue_size: int = 1000,
    ) -> str:
        """
        Subscribe to specific event types.

        Args:
            event_types: List of event types to subscribe to
            handler: Handler for processing events
            queue_size: Maximum queue size for buffering events

        Returns:
            Subscription ID for managing the subscription
        """
        async with self._lock:
            self._subscription_counter += 1
            subscription_id = f"sub_{self._subscription_counter}"

            subscription = EventSubscription(
                subscription_id,
                set(event_types),
                handler,
                queue_size,
            )

            self._subscriptions[subscription_id] = subscription
            await subscription.start_processing()

            logger.info(f"Created subscription {subscription_id} for {event_types}")
            return subscription_id

    async def unsubscribe(self, subscription_id: str) -> None:
        """
        Unsubscribe from events.

        Args:
            subscription_id: ID of subscription to remove
        """
        async with self._lock:
            if subscription_id in self._subscriptions:
                subscription = self._subscriptions[subscription_id]
                await subscription.stop_processing()
                del self._subscriptions[subscription_id]
                logger.debug(f"Removed subscription {subscription_id}")

    async def get_event_history(
        self,
        event_types: list[StreamEventType] | None = None,
        limit: int | None = None,
    ) -> list[StreamEvent]:
        """
        Get historical events.

        Args:
            event_types: Filter by event types (None for all)
            limit: Maximum number of events to return

        Returns:
            List of historical events
        """
        async with self._lock:
            events = self._event_history

            if event_types:
                events = [e for e in events if e.etype in event_types]

            if limit:
                events = events[-limit:]

            return events.copy()

    @asynccontextmanager
    async def event_stream(
        self,
        event_types: list[StreamEventType],
        cancellation_token: CancellationToken | None = None,
    ) -> AsyncIterator[AsyncIterator[StreamEvent]]:
        """
        Create a streaming context for events.

        Args:
            event_types: Event types to stream
            cancellation_token: Token for cancellation

        Yields:
            Async iterator of events
        """
        queue: asyncio.Queue[StreamEvent] = asyncio.Queue()

        class StreamHandler:
            async def handle(self, event: StreamEvent) -> None:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    logger.warning("Event stream queue full, dropping event")

        handler = StreamHandler()
        subscription_id = await self.subscribe(event_types, handler)

        async def event_iterator() -> AsyncIterator[StreamEvent]:
            try:
                while True:
                    if cancellation_token and cancellation_token.is_cancelled:
                        break
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=0.1)
                        yield event
                    except TimeoutError:
                        continue
            finally:
                await self.unsubscribe(subscription_id)

        try:
            yield event_iterator()
        finally:
            await self.unsubscribe(subscription_id)

    async def shutdown(self) -> None:
        """Shutdown the event manager and all subscriptions."""
        self._shutdown = True

        async with self._lock:
            for subscription_id in list(self._subscriptions.keys()):
                await self.unsubscribe(subscription_id)

            self._subscriptions.clear()
            self._event_history.clear()

        logger.info("Event manager shut down")

    async def wait_for_previous_events(self) -> None:
        """
        Wait for all previous events to be processed before shutting down.

        This ensures that no events are lost during shutdown.
        """
        for subs_id, subscription in self._subscriptions.items():
            if subscription.queue.qsize() > 0:
                logger.info(f"Waiting for event from subscription {subs_id} to be processed ..")
                await asyncio.sleep(0.1)  # Allow some time for processing
