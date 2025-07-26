# ruff: noqa: PLW0603 PLC0415
import logging

from .executor import ToolExecutor
from .registry import ToolRegistry

logger = logging.getLogger("tools")

_tool_registry: ToolRegistry | None = None
_tool_executor: ToolExecutor | None = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


def get_tool_executor() -> ToolExecutor:
    """Get the global tool executor instance."""
    global _tool_executor
    if _tool_executor is None:
        _tool_executor = ToolExecutor(get_tool_registry())
    return _tool_executor


def register_builtin_tools() -> None:
    """Register all built-in tools with the global registry."""

    registry = get_tool_registry()

    from .list_directory import ListDirectoryTool
    from .read_file import ReadFileTool
    from .shell_execute import ShellExecuteTool
    from .write_file import WriteFileTool

    # Register file system tools
    registry.register_tool(ReadFileTool())
    registry.register_tool(WriteFileTool())
    registry.register_tool(ListDirectoryTool())
    registry.register_tool(ShellExecuteTool())

    logger.info("Registered built-in tools")


__all__ = ("get_tool_executor", "get_tool_registry", "register_builtin_tools")
