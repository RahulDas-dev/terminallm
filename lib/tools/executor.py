import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from lib.base_types import ServerStreamEvent, StreamEventType, ToolCall
from lib.event_system import EventManager, get_event_manager

from .base import ToolExecutionContext, ToolExecutionResult, ToolResult
from .registry import ToolRegistry

logger = logging.getLogger("tools")


class ToolExecutor:
    """Executes tools with middleware support and error handling."""

    def __init__(
        self,
        registry: ToolRegistry,
        event_manager: EventManager | None = None,
    ):
        self.registry = registry
        self.event_manager = event_manager or get_event_manager()
        self.execution_stats: dict[str, dict[str, Any]] = {}

    async def execute_tool(
        self,
        tool_call: ToolCall,
        context: ToolExecutionContext,
    ) -> ToolResult:
        """
        Execute a tool call with full middleware support.

        Args:
            tool_call: The tool call to execute
            context: Execution context

        Returns:
            Tool execution result
        """
        start_time = datetime.now(tz=timezone.utc)

        # Get tool
        tool = self.registry.get_tool(tool_call.name)
        if not tool:
            return ToolResult(
                tool_call_id=tool_call.id,
                content=f"Tool '{tool_call.name}' not found",
                is_error=True,
                execution_time_ms=0,
            )

        try:
            # Publish tool call request event
            await self._publish_event(
                StreamEventType.TOOL_CALL_REQUEST,
                metadata={
                    "tool_name": tool_call.name,
                    "tool_call_id": tool_call.id,
                    "parameters": tool_call.arguments,
                    "provider": context.provider,
                },
            )

            # Check if confirmation is needed
            if await tool.should_confirm_execute(tool_call.arguments, context):
                # In a real implementation, this would prompt the user
                # For now, we'll assume confirmation is granted
                pass

            # Apply global middleware before execution
            parameters = tool_call.arguments.copy()
            for middleware in self.registry.middleware:
                parameters = await middleware.before_execution(tool_call.name, parameters, context)

            # Apply tool-specific middleware
            for middleware in tool.middleware:
                parameters = await middleware.before_execution(tool_call.name, parameters, context)

            # Execute tool
            execution_result = await tool.execute(parameters, context)

            # Convert ToolExecutionResult to ToolResult for middleware
            if isinstance(execution_result, ToolExecutionResult):
                result = ToolResult(
                    tool_call_id=tool_call.id,
                    content=execution_result.content,
                    is_error=execution_result.is_error,
                    metadata=execution_result.metadata,
                    execution_time_ms=execution_result.execution_time_ms,
                )
            else:
                # Handle legacy ToolResult returns
                result = execution_result

            # Apply tool-specific middleware after execution
            for middleware in reversed(tool.middleware):
                result = await middleware.after_execution(tool_call.name, result, context)

            # Apply global middleware after execution
            for middleware in reversed(self.registry.middleware):
                result = await middleware.after_execution(tool_call.name, result, context)

            # Calculate execution time and create new result with timing
            execution_time = (datetime.now(tz=timezone.utc) - start_time).total_seconds() * 1000

            # Create new result with execution time since ToolResult is frozen
            result = ToolResult(
                tool_call_id=tool_call.id,
                content=result.content,
                is_error=result.is_error,
                metadata=result.metadata,
                execution_time_ms=int(execution_time),
            )

            # Update stats
            self._update_execution_stats(tool_call.name, execution_time, success=True)

            # Publish success event
            await self._publish_event(
                StreamEventType.TOOL_CALL_RESPONSE,
                content=result.content,
                metadata={
                    "tool_call_id": tool_call.id,
                    "tool_name": tool_call.name,
                    "execution_time_ms": result.execution_time_ms,
                    "success": not result.is_error,
                },
            )

            return result

        except Exception as e:
            execution_time = (datetime.now(tz=timezone.utc) - start_time).total_seconds() * 1000

            # Try middleware error handlers
            for middleware in tool.middleware + self.registry.middleware:
                try:
                    fallback_result = await middleware.on_error(tool_call.name, e, context)
                    if fallback_result:
                        return fallback_result
                except Exception:
                    continue  # Middleware error handler failed

            # Create error result
            error_result = ToolResult(
                tool_call_id=tool_call.id,
                content=f"Error executing tool '{tool_call.name}': {e!s}",
                is_error=True,
                execution_time_ms=int(execution_time),
            )

            # Update stats
            self._update_execution_stats(tool_call.name, execution_time, success=False)

            # Publish error event
            await self._publish_event(
                StreamEventType.ERROR,
                error=str(e),
                metadata={
                    "tool_call_id": tool_call.id,
                    "tool_name": tool_call.name,
                    "execution_time_ms": int(execution_time),
                },
            )

            logger.error(f"Tool execution failed: {tool_call.name} - {e}")
            return error_result

    async def execute_tools_parallel(
        self,
        tool_calls: list[ToolCall],
        context: ToolExecutionContext,
    ) -> list[ToolResult]:
        """Execute multiple tools in parallel."""
        if not tool_calls:
            return []

        # Create individual execution tasks
        tasks = [self.execute_tool(tool_call, context) for tool_call in tool_calls]

        # Execute all tools concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = ToolResult(
                    tool_call_id=tool_calls[i].id,
                    content=f"Tool execution failed: {result!s}",
                    is_error=True,
                    execution_time_ms=0,
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)

        return processed_results

    def _update_execution_stats(self, tool_name: str, execution_time: float, success: bool) -> None:
        """Update execution statistics."""
        if tool_name not in self.execution_stats:
            self.execution_stats[tool_name] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_time_ms": 0,
                "average_time_ms": 0,
            }

        stats = self.execution_stats[tool_name]
        stats["total_executions"] += 1
        stats["total_time_ms"] += execution_time
        stats["average_time_ms"] = stats["total_time_ms"] / stats["total_executions"]

        if success:
            stats["successful_executions"] += 1
        else:
            stats["failed_executions"] += 1

    async def _publish_event(
        self,
        event_type: StreamEventType,
        content: str | None = None,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish an event."""
        event = ServerStreamEvent(
            type=event_type,
            provider="tool_system",
            content=content,
            error=error,
            metadata=metadata or {},
        )
        await self.event_manager.publish(event)

    def get_execution_stats(self) -> dict[str, dict[str, Any]]:
        """Get execution statistics."""
        return self.execution_stats.copy()

    def reset_execution_stats(self) -> None:
        """Reset execution statistics."""
        self.execution_stats.clear()
