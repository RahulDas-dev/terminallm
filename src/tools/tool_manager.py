import json
import logging
from time import perf_counter
from typing import Any

from litellm import ChatCompletionMessageToolCall

from src.config import Config
from src.event_sys import get_event_manager
from src.event_sys.types import StreamEvent, StreamEventType

from .base import Tool
from .tool_registry import ToolRegistry

# Get a logger instance
logger = logging.getLogger(__name__)


class ToolCallManager:
    """
    A class for managing tool calls.
    """

    def __init__(self, config: Config, tool_registry: ToolRegistry) -> None:
        """
        Initializes a new instance of the ToolCallManager class.

        Args:
            config: The configuration for the application.
            tool_registry: The registry containing available tools.
        """
        self.config = config
        self.tool_registry = tool_registry
        self.tool_calls: list[dict[str, Any]] = []
        self.event_bus = get_event_manager()

    async def schedule(
        self, request: list[ChatCompletionMessageToolCall] | ChatCompletionMessageToolCall, signal: Any = None
    ) -> list[dict[str, Any]]:
        """
        Schedules a tool call for execution.

        Args:
            request: The tool call request.
            tool_params: The parameters to pass to the tool.
            signal: An optional signal that can be used to cancel the operation.

        Returns:
            The result of the tool call.
        """
        requests = [request] if not isinstance(request, list) else request

        results: list[dict[str, Any]] = []
        await self.event_bus.publish(
            StreamEvent(
                etype=StreamEventType.TOOL_CALL_START,
                tool_call_data=requests,
            )
        )
        for req in requests:
            if not req.function.name:
                results.append(
                    {
                        "tool_call_id": req.id,
                        "role": "tool",
                        "name": req.function.name,
                        "content": "Tool name is missing in the request.",
                    }
                )
                continue
            tool = self.tool_registry.get_tool(req.function.name)
            if not tool:
                results.append(
                    {
                        "tool_call_id": req.id,
                        "role": "tool",
                        "name": req.function.name,
                        "content": "Tool not found: " + req.function.name,
                    }
                )
                continue
            function_args = json.loads(req.function.arguments)
            if self.config.approval_mode == "yolo":
                result = await self._execute_tool(tool, function_args)
                results.append(
                    {
                        "tool_call_id": req.id,
                        "role": "tool",
                        "name": req.function.name,
                        "content": result,
                    }
                )
            else:
                confirm_details = await tool.should_confirm_execute(function_args, signal)
                if confirm_details:
                    confirm_result = await self._confirm_tool_execution(tool, function_args, confirm_details)
                    if confirm_result["confirmed"]:
                        result = await self._execute_tool(tool, function_args)
                        results.append(
                            {
                                "tool_call_id": req.id,
                                "role": "tool",
                                "name": req.function.name,
                                "content": result,
                            }
                        )
                    else:
                        results.append(
                            {
                                "tool_call_id": req.id,
                                "role": "tool",
                                "name": req.function.name,
                                "content": "Tool execution cancelled by user.",
                            }
                        )
                else:
                    result = await self._execute_tool(tool, function_args)
                    results.append(
                        {
                            "tool_call_id": req.id,
                            "role": "tool",
                            "name": req.function.name,
                            "content": result,
                        }
                    )

        return results

    async def _confirm_tool_execution(
        self, tool: Tool, function_args: dict[str, Any], confirm_details: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Confirms with the user whether to execute a tool call.

        Args:
            tool: The tool to execute.
            request: The tool call request.
            confirm_details: The details for the confirmation.

        Returns:
            A dictionary with the result of the confirmation.
        """
        logger.info("[TOOL CONFIRMATION]")
        logger.info(f"Tool: {tool.display_name}")
        logger.info(f"Action: {confirm_details.get('message', 'Execute tool?')}")
        logger.info("[Auto-confirming for demonstration]")
        return {"confirmed": True}

    async def _execute_tool(self, tool: Tool, function_args: dict[str, Any]) -> str:
        """
        Executes a tool call.

        Args:
            tool: The tool to execute.
            request: The tool call request.

        Returns:
            The result of the tool call.
        """
        try:
            start_time = perf_counter()
            result = await tool.execute(function_args)
            await self.event_bus.publish(
                StreamEvent(
                    etype=StreamEventType.TOOL_RESULT,
                    tool_result={
                        "name": tool.name,
                        "content": result["return_display"],
                        "time": (perf_counter() - start_time) * 1000,
                    },
                )
            )
            return result["llm_content"]
        except Exception as e:
            error_msg = str(e)
            logger.exception(f"[TOOL ERROR] {error_msg}")
            await self.event_bus.publish(
                StreamEvent(
                    etype=StreamEventType.TOOL_ERROR,
                    tool_result={
                        "name": tool.name,
                        "content": str(e),
                    },
                )
            )
            return error_msg
