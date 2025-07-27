import logging
from typing import Any

from lib.agent import CoderAgent

from .console import get_console
from .setup_loggers import setup_logger_for_cli

logger = logging.getLogger("Terminallm")


class TerminaLLMApp(CoderAgent):
    """
    TerminalLMClient is the main client class for the TerminalLM application.
    It initializes the client with a target directory and configuration.

    Args:
        target_dir (str): The target directory for the client.
        config (Config): The configuration for the application.
        tool_call_manager (ToolCallManager): The ToolCallManager instance to handle tool calls.
    """

    def __init__(self, target_dir: str, config: dict[str, Any]):
        super().__init__(target_dir, config_params=config)
        self.console = get_console()

    async def initialize(self) -> None:
        setup_logger_for_cli(self.config)
        await super().initialize()
        await self.console.setup_listeners()

    async def run_non_interactive(self, question: str) -> str | None:
        """
        Runs the CLI in non-interactive mode.
        """
        try:
            response = await self._execute_task(question)
            await self.save_chat_history()
            return response
        except Exception as e:
            logger.exception(f"An error occurred: {e}")

    async def run_interactive(self) -> str | None:
        """
        Runs the CLI in interactive mode.
        """
        response = None
        try:
            task_str = "Enter your question or type 'exit' to quit >"
            while True:
                user_input = await self.console.get_user_input(task_str)
                if user_input.lower() in ("exit", "quit"):
                    break
                # self.console.print("Assistant >")
                response = await self._execute_task(user_input)
                task_str = ""
            await self.save_chat_history()
            return response
        except Exception as e:
            logger.exception(f"An error occurred: {e}")
