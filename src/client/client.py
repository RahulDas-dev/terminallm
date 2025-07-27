import logging
from collections.abc import AsyncIterator
from typing import Any

import litellm
from litellm.types.utils import ModelResponseStream

# from litellm.utils import token_counter
from src.config import Config
from src.event_sys import StreamEvent, StreamEventType, get_event_manager
from src.utils import get_litellm_model_params

logger = logging.getLogger(__name__)


class LlmClient:
    """
    A client for interacting with a large language model.
    """

    def __init__(self, target_dir: str, config: Config) -> None:
        """
        Initializes a new instance of the LLMClient class.

        Args:
            target_dir: The target directory for the client.
            config: The configuration for the application.
            tool_call_manager: The ToolCallManager instance to handle tool calls.
        """
        self.config = config
        self.target_dir = target_dir
        self.event_bus = get_event_manager()

    async def send_message_stream(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None
    ) -> AsyncIterator[ModelResponseStream]:
        """
        Sends a message to the language model and streams the response, yielding parsed events.
        handles model fallback and tool calls.
        """
        try:
            await self.event_bus.publish(
                StreamEvent(
                    etype=StreamEventType.STREAM_START,
                    data=None,
                )
            )
            model_params = get_litellm_model_params(self.config.model, self.config.provider)
            response = await litellm.acompletion(
                **model_params,
                messages=messages,
                stream=True,
                tools=tools,
                tool_choice="auto",
                n=1,
            )
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    await self.event_bus.publish(
                        StreamEvent(
                            etype=StreamEventType.STREAM_CONTENT,
                            data=chunk,
                        )
                    )
                elif chunk.choices[0].delta.tool_calls:
                    await self.event_bus.publish(
                        StreamEvent(
                            etype=StreamEventType.STREAM_TOOL_CALL,
                            data=chunk,
                        )
                    )
                else:
                    await self.event_bus.publish(
                        StreamEvent(
                            etype=StreamEventType.STREAM_CHUNK,
                            data=chunk,
                        )
                    )
                yield chunk
            await self.event_bus.publish(
                StreamEvent(
                    etype=StreamEventType.STREAM_COMPLETE,
                    data=None,
                )
            )
        except Exception as e:
            logger.error(f"Error sending message stream: {e}")
            # Publish error event
            await self.event_bus.publish(
                StreamEvent(
                    etype=StreamEventType.STREAM_ERROR,
                    data=None,
                    error=str(e),
                )
            )

            # Also publish completion event to ensure proper event sequence
            await self.event_bus.publish(
                StreamEvent(
                    etype=StreamEventType.STREAM_COMPLETE,
                    data=None,
                )
            )

            # Re-raise the exception to be handled by caller
            # This maintains the contract specified by the return type
            raise
