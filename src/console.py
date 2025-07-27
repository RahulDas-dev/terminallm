# ruff: noqa:  PLW0603
import logging
import shutil
import sys

from colorama import Fore, Style

from .event_sys import StreamEvent, StreamEventType, get_event_manager

logger = logging.getLogger("Console")


class Console:
    def __init__(self):
        """
        Initializes the console with colorama.
        """
        self.terminal_width = shutil.get_terminal_size().columns
        self.event_bus = get_event_manager()

    async def setup_listeners(self) -> None:
        """Set up event listeners."""
        await self.event_bus.subscribe(
            [StreamEventType.STREAM_CONTENT, StreamEventType.STREAM_CHUNK], self.handle_llm_content
        )
        await self.event_bus.subscribe([StreamEventType.STREAM_COMPLETE], self.handle_llm_complete)
        await self.event_bus.subscribe([StreamEventType.STREAM_ERROR], self.handle_stream_error)
        await self.event_bus.subscribe([StreamEventType.TOOL_CALL_START], self.handle_tool_start)
        await self.event_bus.subscribe([StreamEventType.TOOL_RESULT], self.handle_tool_result)
        await self.event_bus.subscribe([StreamEventType.TOOL_ERROR], self.handle_tool_error)
        await self.event_bus.subscribe([StreamEventType.TOKEN_COUNT], self.handle_token_counts)
        # await event_bus.subscribe([StreamEventType.USER_INPUT], self.handel_user_input)

    def handle_llm_content(self, event: StreamEvent) -> None:
        """Handle LLM content chunks."""
        data = event.data.choices[0].delta.content
        if not data:
            return
        sys.stdout.write(f"{Fore.GREEN}{data}{Style.RESET_ALL}")
        sys.stdout.flush()

    def handle_llm_complete(self, _event: StreamEvent) -> None:
        """Handle LLM response completion."""
        sys.stdout.write("\n")
        sys.stdout.flush()

        # Add a slight delay to ensure token count events are displayed properly
        # This signals to the user that the response is complete and token information should follow

    def handle_stream_error(self, event: StreamEvent) -> None:
        error_msg = event.error
        sys.stderr.write(f"{Fore.RED}ERROR - {error_msg}{Style.RESET_ALL}")
        sys.stderr.flush()

    def handle_tool_start(self, event: StreamEvent) -> None:
        """Handle tool execution start."""
        tolls_count = len(event.tool_call_data)
        if tolls_count == 1:
            tool_names = event.tool_call_data[0].function.name
        elif tolls_count > 1:
            # If multiple tools are called, join their names
            tool_names = ", ".join(
                [tool.function.name for tool in event.tool_call_data if tool.function.name is not None]
            )
        else:
            tool_names = None
        if tool_names is None:
            logger.warning("Tool Name is None, skipping tool execution display")
            return
        sys.stdout.write(f"{Fore.YELLOW}[ EXECUTING TOOL ] | {tool_names.upper()}{Style.RESET_ALL}\n")
        sys.stdout.flush()

    def handle_tool_result(self, event: StreamEvent) -> None:
        """Handle tool execution start."""
        tool_names = event.tool_result.get("name", "Unknown Tool").upper()
        message = event.tool_result.get("content", "No content returned")
        time = event.tool_result.get("time", "Unknown time")
        time = round(time, 2) if isinstance(time, (int, float)) else time
        sys.stdout.write(f"{Fore.YELLOW}[ TOOL COMPLITED ] | {time} ms | {tool_names} | {message} {Style.RESET_ALL}\n")
        sys.stdout.flush()

    def handle_tool_error(self, event: StreamEvent) -> None:
        """Handle tool execution error."""
        tool_names = event.tool_result.get("name", "Unknown Tool").upper()
        message = event.tool_result.get("content", "No content returned")
        sys.stderr.write(f"{Fore.RED}[TOOL ERROR] | {tool_names} | {message} {Style.RESET_ALL}\n")
        sys.stderr.flush()

    def handle_token_counts(self, event: StreamEvent) -> None:
        """Display token usage information."""
        input_token = event.token_count.get("prompt_tokens", 0)
        output_token = event.token_count.get("completion_tokens", 0)
        allowed_token = event.token_count.get("tokens_allowed", None)
        total_tokens = input_token + output_token
        token_str = f"Tokens used - {total_tokens} [ = {input_token} + {output_token}]"
        if allowed_token is not None:
            try:
                allowed_token = int(allowed_token)
                token_used = round((total_tokens / allowed_token) * 100, 2)
                token_str += f" | {allowed_token}, {token_used}%"
            except (ValueError, TypeError, ZeroDivisionError):
                pass  # Skip percentage calculation if there's an issue
        clean_text = token_str.replace(Fore.YELLOW, "").replace(Fore.RED, "").replace(Style.RESET_ALL, "")
        padding = max(0, self.terminal_width - len(clean_text) - 2)
        sys.stderr.write(f"\n\r{' ' * padding}{Fore.LIGHTBLUE_EX}{token_str}{Style.RESET_ALL}\n")
        sys.stderr.flush()

    async def get_user_input(self, user_input: str) -> str:
        """Get input from the user with optional prompt.

        Args:
            prompt: Optional text to display as input prompt

        Returns:
            The user's input as a string
        """
        prompt_ = user_input or "\nEnter your input Query or Type 'exit' to 'quit' >"
        await self.event_bus.wait_for_previous_events()
        while True:
            sys.stdout.write(f"{Fore.CYAN}{prompt_}{Style.RESET_ALL} ")
            sys.stdout.flush()
            try:
                usr_input = input()
                if not usr_input.strip():
                    prompt_ = "\nEnter your input Query or Type 'exit' to 'quit' > "
                else:
                    break
            except KeyboardInterrupt:
                sys.stdout.write("\nOperation cancelled\n")
                return "exit"
            except EOFError:
                sys.stdout.write("\n")
                return "exit"
        sys.stdout.flush()
        return usr_input

    def print(self, message: str) -> None:
        """Print a message to the console."""
        sys.stdout.write(f"{Fore.GREEN}{message}{Style.RESET_ALL}")
        sys.stdout.flush()


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
