from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol

from litellm.types.utils import ModelResponseStream


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
    TOOL_RESULT = "tool_result"
    USER_CANCELLED = "user_cancelled"
    CHAT_COMPRESSED = "chat_compressed"
    PROVIDER_SWITCHED = "provider_switched"
    TOKEN_COUNT = "token_count"


"""
@dataclass(frozen=True, slots=True)
class ServerStreamEvent(BaseStreamEvent):

    content: str | None = None
    chunk: ModelResponseStream | None = None
    tool_call: ToolCall | None = None
    tool_result: ToolResult | None = None
    error: str | None = None
    thought_subject: str | None = None 
"""


@dataclass(frozen=True, slots=True)
class StreamEvent:
    etype: StreamEventType
    data: ModelResponseStream | None = None
    error: str | None = None
    tool_result: list[dict] | None = None
    token_count: dict[str, Any] | None = None


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
