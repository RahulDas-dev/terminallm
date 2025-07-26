import logging
from collections.abc import Callable
from typing import Any

from lib.base_types import ServerStreamEvent, StreamEventType

from .manager import EventManager

logger = logging.getLogger("event_manager")


class EventTransformationPipeline:
    """
    Transforms provider-specific events to standardized ServerStreamEvents.

    This handles the complexity of different provider event formats and
    normalizes them into a consistent interface.
    """

    def __init__(self, event_manager: EventManager):
        self.event_manager = event_manager
        self._transformers: dict[str, Callable] = {}
        self._register_default_transformers()

    def _register_default_transformers(self) -> None:
        """Register default event transformers for common providers."""
        self._transformers.update(
            {
                "openai": self._transform_openai_event,
                "anthropic": self._transform_anthropic_event,
                "google": self._transform_google_event,
                "azure_openai": self._transform_openai_event,  # Same as OpenAI
            }
        )

    def register_transformer(
        self,
        provider: str,
        transformer: Callable[[Any], ServerStreamEvent],
    ) -> None:
        """Register a custom event transformer for a provider."""
        self._transformers[provider] = transformer
        logger.debug(f"Registered event transformer for provider: {provider}")

    async def transform_and_publish(
        self,
        provider_event: Any,
        provider: str,
        event_type: StreamEventType,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Transform a provider event and publish it.

        Args:
            provider_event: Raw event from the provider
            provider: Provider name
            event_type: Type of event
            metadata: Additional metadata
        """
        try:
            if provider in self._transformers:
                event = self._transformers[provider](provider_event)
            else:
                # Fallback to generic transformation
                event = self._transform_generic_event(provider_event, provider, event_type)

            # Add metadata
            if metadata:
                event.metadata.update(metadata)

            await self.event_manager.publish(event)

        except Exception as e:
            logger.error(f"Error transforming event from {provider}: {e}")
            # Publish error event
            error_event = ServerStreamEvent(
                type=StreamEventType.ERROR,
                provider=provider,
                error=str(e),
                metadata=metadata or {},
            )
            await self.event_manager.publish(error_event)

    def _transform_openai_event(self, event: Any) -> ServerStreamEvent:
        """Transform OpenAI streaming event."""
        # Implementation for OpenAI delta events
        # This will be expanded based on actual OpenAI response format
        return ServerStreamEvent(
            type=StreamEventType.CONTENT,
            provider="openai",
            content=getattr(event, "content", ""),
            metadata={"raw_event": str(event)},
        )

    def _transform_anthropic_event(self, event: Any) -> ServerStreamEvent:
        """Transform Anthropic streaming event."""
        # Implementation for Anthropic message events
        return ServerStreamEvent(
            type=StreamEventType.CONTENT,
            provider="anthropic",
            content=getattr(event, "content", ""),
            metadata={"raw_event": str(event)},
        )

    def _transform_google_event(self, event: Any) -> ServerStreamEvent:
        """Transform Google streaming event."""
        # Implementation for Google response events
        return ServerStreamEvent(
            type=StreamEventType.CONTENT,
            provider="google",
            content=getattr(event, "content", ""),
            metadata={"raw_event": str(event)},
        )

    def _transform_generic_event(
        self,
        event: Any,
        provider: str,
        event_type: StreamEventType,
    ) -> ServerStreamEvent:
        """Generic event transformation fallback."""
        return ServerStreamEvent(
            type=event_type,
            provider=provider,
            content=str(event) if event else None,
            metadata={"raw_event": str(event)},
        )
