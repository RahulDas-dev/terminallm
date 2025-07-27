import json
import logging
from pathlib import Path
from typing import Any

import aiofiles
import colorama
from dotenv import load_dotenv

from .client import LLMClientSession
from .config import Config
from .console import get_console
from .event_sys import get_event_manager
from .tools import get_registry
from .utils import setup_logger_for_cli

logger = logging.getLogger("Agent")


class CoderAgent:
    """
    A command-line interface for interacting with a large language model.
    This class provides methods for initializing the model, processing user input,
    and handling tool calls.
    """

    def __init__(self, target_dir: str, config_params: dict[str, Any] | None = None) -> None:
        """
        Initializes the LLM CLI with the given configuration parameters.
        If no parameters are provided, default values will be used.
        """
        self.target_dir = target_dir
        self.config = Config() if config_params is None else Config(**config_params)
        self.console = get_console()
        self.tool_registry = get_registry()
        self.session = LLMClientSession(config=self.config, target_dir=self.target_dir)
        self.event_bus = get_event_manager()

    async def initialize(self) -> None:
        """
        Initializes the configuration, client, and tool call manager.
        This method must be called before processing any input.
        """
        setup_logger_for_cli(self.config)
        logger.info(f"Config Details: {self.config}")
        status = load_dotenv()
        if not status:
            logger.warning("No .env file found Make Sure Required Environment Variables are set")
        colorama.init()
        await self.console.setup_listeners()
        self.tool_registry.register_tools(self.config, target_dir=self.target_dir)
        logger.info(f"Available tools: {self.tool_registry.get_available_functions()}")

    async def save_chat_history(self) -> None:
        chat_history = self.session.get_history()
        async with aiofiles.open(Path(self.target_dir, "chat_history.json"), "w", encoding="utf-8") as f:
            await f.write(json.dumps(chat_history, indent=2))
        logger.info(f"Chat history saved to {Path(self.target_dir, 'chat_history.json')}")

    async def _execute_task(self, user_input: str) -> str | None:
        """
        Executes a user task by sending it to the LLM and handling tool calls in a loop until a
        final response is produced.
        """
        logger.info(f"Model: {self.config.model} Provider: {self.config.provider}")
        if self.tool_registry is None:
            raise RuntimeError("Tool registry is not initialized. Call initialize() before executing tasks.")

        tool_definitions = self.tool_registry.get_tool_definitions()
        if self.config.debug:
            logger.debug(f"Tool definitions: {tool_definitions}")
        final_response = None

        final_response = await self.session.chat_message_stream(user_input, tool_definitions)

        return final_response

    async def run_non_interactive(self, question: str) -> str | None:
        """
        Runs the CLI in non-interactive mode.
        """
        response = await self._execute_task(question)
        await self.save_chat_history()
        return response

    async def run_interactive(self) -> None:
        """
        Runs the CLI in interactive mode.
        """
        task_str = "Enter your question or type 'exit' to quit >"
        while True:
            user_input = self.console.get_user_input(task_str)
            if user_input.lower() in ("exit", "quit"):
                break
            self.console.print("Assistant >")
            _ = await self._execute_task(user_input)
            task_str = ""
        await self.save_chat_history()
