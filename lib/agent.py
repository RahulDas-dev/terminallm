from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from lib.base_types import ServerStreamEvent
from lib.client.llmclient import LLMClient
from lib.configs.main import AppConfig
from lib.event_system import get_event_manager
from lib.startup_ops import startup_operations
from lib.system_msg import MessageBuilder
from lib.tools import get_tool_executor, get_tool_registry, register_builtin_tools
from lib.utils.common import is_valid_workspace


class DeveloperAgent:
    """
    Developer Agent class for managing the agent's operations.
    """

    def __init__(
        self,
        config: AppConfig,
        workspace_path: str | None = None,
        console_manager: Any | None = None,
    ):
        workspace_path_ = Path(workspace_path) if workspace_path else Path.cwd()
        if not is_valid_workspace(workspace_path_):
            raise ValueError(f"Invalid workspace path: {workspace_path_}")
        self.workspace_path = workspace_path_.resolve()
        self.config = config
        self.event_manager = get_event_manager()
        self.tool_executor = get_tool_executor()
        self.tool_registry = get_tool_registry()
        self.console_manager = console_manager
        self.client: LLMClient | None = None

    def startup(self) -> None:
        """
        Perform all startup operations for the agent.
        """

        startup_operations(self.config)
        register_builtin_tools()
        self.client = LLMClient(
            self.config,
            self.event_manager,
            self.tool_registry,
        )

    async def execute_task(
        self,
        task: str,
        system_prompt: str | None = None,
        tools: list[str] | None = None,
        previous_task_id: str | None = None,
    ) -> AsyncIterator[ServerStreamEvent]:
        """
        Execute a given task using the agent.
        This method should be implemented by subclasses.
        """
        if system_prompt is None:
            system_prompt = MessageBuilder.get_system_message(self.workspace_path)
        if tools is not None:
            tools_prompt = MessageBuilder.get_toolusage_messages(available_tools=tools)
            system_prompt += f"\n\n{tools_prompt}"

        available_tools = []
        if tools:
            for tool_name in tools:
                tool = self.tool_registry.get_tool(tool_name)
                if tool:
                    available_tools.append(tool)

    def health_check(self) -> bool:
        """
        Perform a health check on the agent.
        Returns True if the agent is healthy, False otherwise.
        """
        # Placeholder for actual health check logic
        return True
