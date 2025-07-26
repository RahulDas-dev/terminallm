from string import Template
from typing import Any

from src.client._prompt import REACT_SYSTEM_PROMPT
from src.client.content_generator import ContentGenerator
from src.config import Config
from src.tools.tool_manager import ToolCallManager


class LLMClientSession:
    """
    A session for interacting with a large language model.
    """

    def __init__(self, config: Config, target_dir: str, tool_call_manager: ToolCallManager):
        self.config = config
        self.target_dir = target_dir
        self.history: list[dict[str, Any]] = []
        self.content_generator = ContentGenerator(config, target_dir, tool_call_manager)

    def add_user_message(self, message: str) -> None:
        self.history.append({"role": "user", "content": message})

    def add_assistant_message(self, message: str) -> None:
        self.history.append({"role": "assistant", "content": message})

    def get_history(self) -> list[dict[str, Any]]:
        return self.history

    def _build_system_prompt(self) -> str:
        """
        Builds the system prompt for the language model.

        Returns:
            The system prompt string.
        """
        return Template(REACT_SYSTEM_PROMPT).safe_substitute(target_dir=self.target_dir)

    async def chat_message_stream(self, task_str: str, tools: list[dict[str, Any]] | None = None):
        if not self.history:
            system_prompt = self._build_system_prompt()
            self.history.append({"role": "system", "content": system_prompt})

        self.add_user_message(task_str)

        response = await self.content_generator.generate_content_streaming(
            messages=self.history.copy(),
            tools=tools,
        )
        if response is not None:
            self.add_assistant_message(response)
