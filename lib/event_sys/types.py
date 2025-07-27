from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from litellm.types.utils import ChatCompletionMessageToolCall, ModelResponseStream


class StreamEventType(str, Enum):
    """Event types for streaming responses."""

    STREAM_START = "stream_start"
    STREAM_CONTENT = "stream_content"
    STREAM_TOOL_CALL = "stream_tool_call"
    STREAM_CHUNK = "stream_chunk"
    STREAM_ERROR = "stream_error"
    STREAM_COMPLETE = "stream_complete"
    AGENT_THINKING_START = "agent_thinking_start"
    AGENT_THINKING_CHUNK = "agent_thinking_chunk"
    AGENT_THINKING_END = "agent_thinking_end"
    TOOL_CALL_START = "tool_call_start"
    TOOL_ERROR = "tool_error"
    TOOL_RESULT = "tool_result"
    USER_CANCELLED = "user_cancelled"
    CHAT_COMPRESSED = "chat_compressed"
    PROVIDER_SWITCHED = "provider_switched"
    TOKEN_COUNT = "tokens_count"
    USER_INPUT = "user_input"


@dataclass(frozen=True, slots=True)
class StreamEvent:
    etype: StreamEventType
    data: ModelResponseStream | None = None
    error: str | None = None
    tool_call_data: list[ChatCompletionMessageToolCall] = field(default_factory=list)
    tool_result: dict = field(default_factory=dict)
    token_count: dict[str, Any] = field(default_factory=dict)
    user_input: str | None = field(default=None)


class CancellationToken:
    """Token for cancelling long-running operations."""

    def __init__(self, reason: str | None = None) -> None:
        self._cancelled = False
        self.reason = reason

    def cancel(self, reason: str | None = None) -> None:
        """Cancel the operation."""
        self._cancelled = True
        if reason:
            self.reason = reason

    @property
    def is_cancelled(self) -> bool:
        """Check if cancellation was requested."""
        return self._cancelled


# Protocol definitions for type checking
class EventHandler(Protocol):
    """Protocol for event handlers."""

    async def handle(self, event: StreamEvent) -> None:
        """Handle a streaming event."""
        ...


EventHandlerFunc = Callable[[StreamEvent], None]
