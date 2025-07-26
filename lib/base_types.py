from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol


class StreamEventType(str, Enum):
    """Event types for streaming responses."""

    CONTENT = "content"
    COMPLETION = "completion"
    TOOL_CALL_REQUEST = "tool_call_request"
    TOOL_CALL_RESPONSE = "tool_call_response"
    TOOL_CALL_CONFIRMATION = "tool_call_confirmation"
    TOOL_RESULT = "tool_result"
    USER_CANCELLED = "user_cancelled"
    ERROR = "error"
    CHAT_COMPRESSED = "chat_compressed"
    THOUGHT = "thought"
    PROVIDER_SWITCHED = "provider_switched"


class ToolCallStatus(str, Enum):
    """Status of tool call execution."""

    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class ToolCall:
    """Standardized tool call representation."""

    id: str
    name: str
    arguments: dict[str, Any]
    status: ToolCallStatus = ToolCallStatus.PENDING
    metadata: dict[str, Any] = field(default_factory=dict)
    type: str = "function"
    function: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ToolResult:
    """Result from tool execution."""

    tool_call_id: str
    content: str
    is_error: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: int | None = None


@dataclass(frozen=True, slots=True)
class StreamChunk:
    """Individual chunk in a streaming response."""

    content: str | None = None
    delta: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BaseStreamEvent:
    """Base class for all stream events."""

    type: StreamEventType
    provider: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ServerStreamEvent(BaseStreamEvent):
    """Main streaming event equivalent to TypeScript ServerStreamEvent."""

    content: str | None = None
    chunk: StreamChunk | None = None
    tool_call: ToolCall | None = None
    tool_result: ToolResult | None = None
    error: str | None = None
    thought_subject: str | None = None


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

    async def handle(self, event: ServerStreamEvent) -> None:
        """Handle a streaming event."""
        ...
