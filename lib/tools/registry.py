import logging
from typing import Any

from .base import BaseTool, ToolCapability, ToolMiddleware

logger = logging.getLogger("tools")


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._middleware: list[ToolMiddleware] = []
        self._capabilities: dict[str, list[ToolCapability]] = {}

    @property
    def middleware(self) -> list[ToolMiddleware]:
        """Get the list of global middleware."""
        return self._middleware

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool."""
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.info(f"Unregistered tool: {tool_name}")
            return True
        return False

    def get_tool(self, tool_name: str) -> BaseTool | None:
        """Get a tool by name."""
        return self._tools.get(tool_name)

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def get_tools_for_provider(self, provider: str) -> list[dict[str, Any]]:
        """Get tools formatted for a specific provider."""
        return [tool.get_provider_schema(provider) for tool in self._tools.values()]

    def add_middleware(self, middleware: ToolMiddleware) -> None:
        """Add global middleware that applies to all tools."""
        self._middleware.append(middleware)

    def remove_middleware(self, middleware: ToolMiddleware) -> None:
        """Remove global middleware."""
        if middleware in self._middleware:
            self._middleware.remove(middleware)

    def set_provider_capabilities(self, provider: str, capabilities: list[ToolCapability]) -> None:
        """Set capabilities for a provider."""
        self._capabilities[provider] = capabilities

    def get_provider_capabilities(self, provider: str) -> list[ToolCapability]:
        """Get capabilities for a provider."""
        return self._capabilities.get(provider, [])

    def filter_tools_by_capabilities(
        self, provider: str, required_capabilities: list[ToolCapability]
    ) -> list[BaseTool]:
        """Filter tools based on provider capabilities."""
        self.get_provider_capabilities(provider)

        if not required_capabilities:
            return list(self._tools.values())

        # For now, return all tools. In a real implementation,
        # you'd filter based on tool-specific capability requirements
        return list(self._tools.values())

    def get_schemas(self, provider: str = "generic") -> list[dict[str, Any]]:
        """Get all tool schemas for a provider."""
        return [tool.get_provider_schema(provider) for tool in self._tools.values()]

    def count(self) -> int:
        """Get total number of registered tools."""
        return len(self._tools)
