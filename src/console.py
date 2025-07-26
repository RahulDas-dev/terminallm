# ruff: noqa:  PLW0603
import shutil
import sys

import colorama
from colorama import Fore, Style

from .event_system import get_event_emitter

colorama.init()


class Console:
    """Console handler for displaying LLM output and logs."""

    def __init__(self):
        self.terminal_width = shutil.get_terminal_size().columns

    def setup_listeners(self) -> None:
        """Set up event listeners."""
        event_bus = get_event_emitter()
        event_bus.on("llm:content", self.handle_llm_content)
        event_bus.on("llm:complete", self.handle_llm_complete)
        event_bus.on("tool:start", self.handle_tool_start)
        event_bus.on("tool:complete", self.handle_tool_complete)
        event_bus.on("tool:error", self.handle_tool_error)
        event_bus.on("token:counts", self.handle_token_counts)

    def handle_llm_content(self, content: str) -> None:
        """Handle LLM content chunks."""
        sys.stdout.write(f"{Fore.GREEN}{content}{Style.RESET_ALL}")
        sys.stdout.flush()

    def handle_llm_complete(self) -> None:
        """Handle LLM response completion."""
        sys.stdout.write("\n")
        sys.stdout.flush()

    def handle_tool_start(self, tool_name: str) -> None:
        """Handle tool execution start."""
        # Tools logs go to stderr with yellow color
        sys.stderr.write(f"{Fore.YELLOW}[EXECUTING TOOL]{tool_name}{Style.RESET_ALL}\n")
        sys.stderr.flush()

    def handle_tool_complete(self, tool_name: str, message: str) -> None:
        """Handle tool execution completion."""
        sys.stderr.write(f"{Fore.YELLOW}[TOOL CALLED ] {tool_name} | {message}{Style.RESET_ALL}\n")
        sys.stderr.flush()

    def handle_tool_error(self, tool_name: str, error: str) -> None:
        """Handle tool execution error."""
        sys.stderr.write(f"{Fore.RED}[TOOL ERROR] {tool_name}: {error}{Style.RESET_ALL}\n")
        sys.stderr.flush()

    def handle_token_counts(self, input_token: int, output_token: int, tokens_allowed: int | None) -> None:
        """Display token usage information."""
        total_tokens = input_token + output_token
        token_str = f"Tokens used: {total_tokens}[ = {input_token} + {output_token}]"
        if tokens_allowed is not None:
            token_used = round((total_tokens / tokens_allowed) * 100, 2)
            token_str += f" | {tokens_allowed}, {token_used} %"

        clean_text = token_str.replace(Fore.YELLOW, "").replace(Fore.RED, "").replace(Style.RESET_ALL, "")

        # Calculate padding to align right
        padding = max(0, self.terminal_width - len(clean_text) - 2)

        sys.stderr.write(f"\r{' ' * padding}{Fore.BLUE}{token_str}{Style.RESET_ALL}\n")
        sys.stderr.flush()


_global_console: Console | None = None


def get_console() -> Console:
    """
    Gets the global console instance.
    If the console hasn't been initialized yet, this will return a new instance.
    """
    global _global_console

    if _global_console is None:
        _global_console = Console()

    return _global_console
