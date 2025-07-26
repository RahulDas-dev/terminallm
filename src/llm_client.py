import logging
from string import Template
from typing import Any

import litellm
from litellm.types.utils import Message, ModelResponse, TextCompletionResponse

# from litellm.utils import token_counter
from .config import Config
from .event_system import get_event_emitter
from .utils import get_litellm_model_name

logger = logging.getLogger(__name__)

# React-style prompt components
REACT_SYSTEM_PROMPT = """
You are an interactive CLI agent specializing in software engineering tasks. Your primary goal is to help users safely and efficiently, adhering strictly to the following instructions and utilizing your available tools.

# Core Mandates

- **Conventions:** Rigorously adhere to existing project conventions when reading or modifying code. Analyze surrounding code, tests, and configuration first.
- **Libraries/Frameworks:** NEVER assume a library/framework is available or appropriate. Verify its established usage within the project (check imports, configuration files like 'package.json', 'requirements.txt', 'pyproject.toml', etc., or observe neighboring files) before employing it.
- **Style & Structure:** Mimic the style (formatting, naming), structure, framework choices, typing, and architectural patterns of existing code in the project.
- **Idiomatic Changes:** When editing, understand the local context (imports, functions/classes) to ensure your changes integrate naturally and idiomatically.
- **Comments:** Add code comments sparingly. Focus on *why* something is done, especially for complex logic, rather than *what* is done. Only add high-value comments if necessary for clarity or if requested by the user.
- **Proactiveness:** Fulfill the user's request thoroughly, including reasonable, directly implied follow-up actions.
- **Confirm Ambiguity/Expansion:** Do not take significant actions beyond the clear scope of the request without confirming with the user.
- **Explaining Changes:** After completing a code modification or file operation *do not* provide summaries unless asked.
- **Do Not revert changes:** Do not revert changes to the codebase unless asked to do so by the user.

# Primary Workflows

## Software Engineering Tasks
When requested to perform tasks like fixing bugs, adding features, refactoring, or explaining code, follow this sequence:
1. **Understand:** Think about the user's request and the relevant codebase context. Use search and file reading tools extensively to understand file structures, existing code patterns, and conventions.
2. **Plan:** Build a coherent and grounded plan for how you intend to resolve the user's task. Share a concise yet clear plan with the user if it would help them understand your thought process.
3. **Implement:** Use the available tools (file operations, shell commands, etc.) to act on the plan, strictly adhering to the project's established conventions.
4. **Verify (Tests):** If applicable and feasible, verify the changes using the project's testing procedures. Identify the correct test commands by examining build/package configuration.
5. **Verify (Standards):** VERY IMPORTANT: After making code changes, execute project-specific build, linting and type-checking commands that you have identified for this project.


## Tool Usage
- **File Paths:** Always use absolute paths when referring to files. Relative paths are not supported.
- **Parallelism:** Execute multiple independent tool calls in parallel when feasible.
- **Command Execution:** Use shell tools for running commands, remembering the safety rule to explain modifying commands first.
- **Interactive Commands:** Avoid shell commands requiring user interaction.

# Context-Specific Information

Your are currently Pointed to the directory: ${target_dir}

Remember: First understand the request, then plan your approach, use tools as needed, and finally respond clearly.
"""  # noqa: E501


class LLMClient:
    """
    A client for interacting with a large language model.
    """

    def __init__(self, target_dir: str, config: Config, tool_call_manager: Any = None) -> None:
        """
        Initializes a new instance of the LLMClient class.

        Args:
            config: The configuration for the application.
            tool_call_manager: The ToolCallManager instance to handle tool calls.
        """
        self.config = config
        self.target_dir = target_dir
        self.history: list[dict[str, Any]] = []
        self.tool_call_manager = tool_call_manager
        self.event_bus = get_event_emitter()

    def _build_system_prompt(self) -> str:
        """
        Builds the system prompt for the language model.

        Returns:
            The system prompt string.
        """
        return Template(REACT_SYSTEM_PROMPT).safe_substitute(target_dir=self.target_dir)

    async def send_message_stream(self, task_str: str, tools: list[dict[str, Any]]) -> str | None:
        """
        Sends a message to the language model and streams the response, yielding parsed events.
        """

        if not self.history:
            system_prompt = self._build_system_prompt()
            self.history.append({"role": "system", "content": system_prompt})

        self.history.append({"role": "user", "content": task_str})

        messages = self.chat_history()
        tool_choice = "auto"
        litellm_model_ = get_litellm_model_name(self.config.model, self.config.provider)
        while True:
            response = await litellm.acompletion(
                model=litellm_model_,
                messages=messages,
                stream=True,
                tools=tools,
                tool_choice=tool_choice,
            )
            chunks = []
            async for chunk in response:
                chunks.append(chunk)
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                if "content" in delta and delta["content"] is not None:
                    # sys.stdout.write(delta["content"])
                    self.event_bus.emit("llm:content", delta["content"])
            self.event_bus.emit("llm:complete")
            # sys.stdout.flush()
            response_ = litellm.stream_chunk_builder(chunks)
            if response_ is None:
                logger.error("No response from model, exiting loop.")
                break
            self._token_counts(response_)
            response_message = response_.choices[0].message
            self.set_assistant_msg(response_message)
            if self.config.debug:
                logger.debug(f"Response message: {response_}")
            if response_message.tool_calls:
                tool_response = await self.tool_call_manager.schedule(
                    response_message.tool_calls,
                    signal=None,
                )
                self.set_toolcall_response(tool_response)
                if self.config.debug:
                    logger.debug(f"Tool call response: {tool_response}")
            if response_message.content and response_message.tool_calls is None:
                final_response = response_message.content
                break
            messages = self.chat_history()

        return final_response

    def _token_counts(self, response: ModelResponse | TextCompletionResponse) -> tuple[int, int, int | None]:
        output_tokens = response.usage.completion_tokens
        input_tokens = response.usage.prompt_tokens
        # token_used = token_counter(model=self.config.model, messages=self.chat_history())
        try:
            tokens_allowed = litellm.utils.get_max_tokens(model=self.config.model)
        except Exception:
            tokens_allowed = None
        self.event_bus.emit("token:counts", input_tokens, output_tokens, tokens_allowed)
        return input_tokens, output_tokens, tokens_allowed

    def chat_history(self) -> list[dict[str, Any]]:
        return self.history.copy()

    def set_user_msg(self, message: dict[str, Any]) -> None:
        self.history.append({"role": "user", "content": message["content"]})

    def set_assistant_msg(self, message: Message) -> None:
        if message.tool_calls and message.content:
            self.history.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": message.tool_calls,
                }
            )
        elif message.content and not message.tool_calls:
            self.history.append({"role": "assistant", "content": message.content})
        elif message.tool_calls and message.content is None:
            self.history.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": message.tool_calls,
                }
            )
        else:
            logger.warning("Received an assistant message with no content or tool calls.")

    def set_toolcall_response(self, messages: list[dict[str, Any]]) -> None:
        for message in messages:
            self.history.append(
                {
                    "role": "tool",
                    "content": message["content"],
                    "tool_call_id": message["tool_call_id"],
                    "name": message["name"],
                }
            )
