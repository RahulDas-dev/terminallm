# ruff:  noqa: PLW0603 PLC0415
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from lib.config import Config

    from .base import Tool

logger = logging.getLogger("tools")


class ToolRegistry:
    """
    A registry for all the tools that can be used by the language model.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance of the ToolRegistry class.
        """
        self._tools: dict[str, Tool] = {}

    def _register_tool(self, tool: Tool) -> None:
        """
        Registers a tool with the registry.

        Args:
            tool: The tool to register.
        """
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Tool | None:
        """
        Gets a tool from the registry by name.

        Args:
            name: The name of the tool to get.

        Returns:
            The tool with the given name, or None if it is not found.
        """
        return self._tools.get(name)

    def get_available_functions(self) -> list[str]:
        """
        Gets the function declarations for all the tools in the registry.

        Returns:
            A list of function declarations.
        """
        return list(self._tools.keys())

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        return [{"type": "function", "function": tool.schema} for tool in self._tools.values()]

    async def discover_tools(self) -> None:
        """
        Discovers any project-specific tools and registers them with the registry.
        """

    def register_tools(self, config: Config, target_dir: str) -> None:
        """
        Registers all core tools with the global registry based on the provided configuration.

        Args:
            config: The configuration for the application.
            target_dir: Optional target directory for file operations.

        Returns:
            The global tool registry instance with tools registered.
        """
        self._tools.clear()

        from .directory_tools import ListDirectoryTool
        from .edit_file import EditFile
        from .glob_tool import GlobTool
        from .read_file import ReadFileTool
        from .shell_tools import ShellTool
        from .write_file import WriteFileTool

        tools = [
            ListDirectoryTool(config),
            ReadFileTool(config),
            WriteFileTool(config),
            ShellTool(config),
            GlobTool(config),
            EditFile(config, target_dir),
        ]

        for tool in tools:
            class_name = tool.__class__.__name__
            tool_name = tool.name

            # Validate if tool is enabled based on config
            is_enabled = True

            # Check if tool is in the exclude list
            if tool_name in config.exclude_tools or class_name in config.exclude_tools:
                is_enabled = False
            # Check if tool is in the core tools list (if specified)
            elif config.core_tools is not None:
                is_enabled = tool_name in config.core_tools

            if is_enabled:
                self._register_tool(tool)
                logger.info(f"Registered tool: {tool_name} ({class_name})")


# Global instance of the tool registry
_global_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    """
    Gets the global tool registry instance.
    If the registry hasn't been initialized yet, this will return a new empty registry.
    Note: This will not have any tools registered until register_tools is called.

    Returns:
        The global tool registry instance.
    """
    global _global_registry

    if _global_registry is None:
        _global_registry = ToolRegistry()

    return _global_registry
