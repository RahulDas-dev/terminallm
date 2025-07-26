from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from lib.base_types import CancellationToken, ToolResult


class ToolCapability(str, Enum):
    """Tool capabilities supported by different providers."""

    BASIC_FUNCTIONS = "basic_functions"
    STRUCTURED_OUTPUTS = "structured_outputs"
    PARALLEL_EXECUTION = "parallel_execution"
    STREAMING_TOOLS = "streaming_tools"
    TOOL_CHOICE = "tool_choice"
    REQUIRED_TOOLS = "required_tools"


@dataclass(frozen=True, slots=True)
class ToolParameter:
    """Tool parameter definition."""

    name: str
    data_type: str
    description: str
    required: bool = False
    default: Any = field(default=None)
    extra: dict[str, Any] = field(default_factory=dict)

    def get_params_schema(self, provider: str = "litellm") -> dict[str, Any]:
        """Get the schema for a specific tool."""
        if provider == "openai":
            return self._format_openai_schema()
        if provider == "anthropic":
            return self._format_anthropic_schema()
        if provider == "google":
            return self._format_google_schema()
        return self._format_generic_schema()

    def _format_generic_schema(self) -> dict[str, Any]:
        """Format schema for generic use."""
        param_schema_ = {"type": self.data_type}
        if self.data_type == "array":
            items_schema = self.extra.get("items", {"type": "string"})
            param_schema_["items"] = items_schema
        # if self.default is not None:
        # #    param_schema_["default"] = self.default
        if self.extra.get("enum_values", None) is not None:
            param_schema_["enum"] = self.extra["enum_values"]
        if self.description:
            param_schema_["description"] = self.description

        return param_schema_

    def _format_openai_schema(self) -> dict[str, Any]:
        return {}

    def _format_anthropic_schema(self) -> dict[str, Any]:
        return {}

    def _format_google_schema(self) -> dict[str, Any]:
        return {}


@dataclass(frozen=True, slots=True)
class ToolSchema:
    """Schema definition for a tool."""

    name: str
    description: str
    parameters: list[ToolParameter] = field(default_factory=list)
    required: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_tool_schema(self, provider: str = "litellm") -> dict[str, Any]:
        """Get the schema for a specific tool."""
        if provider == "openai":
            return self._format_openai_schema()
        if provider == "anthropic":
            return self._format_anthropic_schema()
        if provider == "google":
            return self._format_google_schema()
        return self._format_generic_schema()

    def _format_generic_schema(self, provider: str = "litellm") -> dict[str, Any]:
        """Format schema for generic use."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {param.name: param.get_params_schema(provider) for param in self.parameters},
                    "required": self.required,
                },
            },
        }

    def _format_openai_schema(self) -> dict[str, Any]:
        return {}

    def _format_anthropic_schema(self) -> dict[str, Any]:
        return {}

    def _format_google_schema(self) -> dict[str, Any]:
        return {}


@dataclass
class ToolExecutionContext:
    """Context for tool execution."""

    provider: str
    model: str
    session_id: str | None = None
    user_id: str | None = None
    cancellation_token: CancellationToken | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolExecutionResult:
    """Result from tool execution (before being converted to ToolResult)."""

    success: bool
    content: str
    display_content: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: int | None = None

    @property
    def is_error(self) -> bool:
        """Return whether this is an error result."""
        return not self.success


class ToolMiddleware(Protocol):
    """Protocol for tool middleware."""

    async def before_execution(
        self, tool_name: str, parameters: dict[str, Any], context: ToolExecutionContext
    ) -> dict[str, Any]:
        """Called before tool execution. Can modify parameters."""
        ...

    async def after_execution(self, tool_name: str, result: ToolResult, context: ToolExecutionContext) -> ToolResult:
        """Called after tool execution. Can modify result."""
        ...

    async def on_error(self, tool_name: str, error: Exception, context: ToolExecutionContext) -> ToolResult | None:
        """Called when tool execution fails. Can provide fallback result."""
        ...


class BaseTool:
    """Base class for all tools."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.middleware: list[ToolMiddleware] = []

    @property
    @abstractmethod
    def schema(self) -> ToolSchema:
        """Build the tool schema."""
        raise NotImplementedError

    async def validate(self, params: dict[str, Any]) -> None:
        """Validate the input parameters against the schema."""
        required = self.schema.required or []
        for param in required:
            if param not in params:
                raise ValueError(f"Missing required parameter: {param}")

    async def execute(self, parameters: dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        """Execute the tool with given parameters."""
        raise NotImplementedError

    def add_middleware(self, middleware: ToolMiddleware) -> None:
        """Add middleware to this tool."""
        self.middleware.append(middleware)

    def remove_middleware(self, middleware: ToolMiddleware) -> None:
        """Remove middleware from this tool."""
        if middleware in self.middleware:
            self.middleware.remove(middleware)

    async def should_confirm_execute(self, parameters: dict[str, Any], context: ToolExecutionContext) -> bool:
        """Check if tool execution should be confirmed with user."""
        return False  # Default: no confirmation needed

    def get_provider_schema(self, provider: str) -> dict[str, Any]:
        """Get tool schema formatted for specific provider."""
        if provider == "openai":
            return self._format_openai_schema()
        if provider == "anthropic":
            return self._format_anthropic_schema()
        if provider == "google":
            return self._format_google_schema()
        return self._format_generic_schema()

    def _format_openai_schema(self) -> dict[str, Any]:
        """Format schema for OpenAI."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.schema.parameters,
                    "required": self.schema.required,
                },
            },
        }

    def _format_anthropic_schema(self) -> dict[str, Any]:
        """Format schema for Anthropic."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": self.schema.parameters,
                "required": self.schema.required,
            },
        }

    def _format_google_schema(self) -> dict[str, Any]:
        """Format schema for Google."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.schema.parameters,
                "required": self.schema.required,
            },
        }

    def _format_generic_schema(self) -> dict[str, Any]:
        """Format schema for generic use."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.schema.parameters,
            "required": self.schema.required,
        }
