import logging
from collections.abc import AsyncIterator
from string import Template
from typing import Any

import litellm
from litellm.types.utils import Message, ModelResponse, ModelResponseStream, TextCompletionResponse

# from litellm.utils import token_counter
from src.config import Config
from src.eventing_system import get_event_manager
from src.eventing_system.types import StreamEvent, StreamEventType
from src.utils import get_litellm_model_name

from ._prompt import REACT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class LlmClient:
    """
    A client for interacting with a large language model.
    """

    def __init__(self, target_dir: str, config: Config) -> None:
        """
        Initializes a new instance of the LLMClient class.

        Args:
            target_dir: The target directory for the client.
            config: The configuration for the application.
            tool_call_manager: The ToolCallManager instance to handle tool calls.
        """
        self.config = config
        self.target_dir = target_dir
        self.event_bus = get_event_manager()

    async def send_message_stream(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None
    ) -> AsyncIterator[StreamEvent]:
        """
        Sends a message to the language model and streams the response, yielding parsed events.
        handles model fallback and tool calls.
        """
        try:
            await self.event_bus.publish(
                StreamEvent(
                    etype=StreamEventType.STREAM_START,
                    data=None,
                )
            )
            litellm_model_ = get_litellm_model_name(self.config.model, self.config.provider)
            response = await litellm.acompletion(
                model=litellm_model_, messages=messages, stream=True, tools=tools, tool_choice="auto", n=1
            )
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    await self.event_bus.publish(
                        StreamEvent(
                            etype=StreamEventType.STREAM_CONTENT,
                            data=chunk,
                        )
                    )
                elif chunk.choices[0].delta.tool_calls:
                    await self.event_bus.publish(
                        StreamEvent(
                            etype=StreamEventType.STREAM_TOOL_CALL,
                            data=chunk,
                        )
                    )
                else:
                    await self.event_bus.publish(
                        StreamEvent(
                            etype=StreamEventType.STREAM_CHUNK,
                            data=chunk,
                        )
                    )
                yield chunk
            await self.event_bus.publish(
                StreamEvent(
                    etype=StreamEventType.STREAM_COMPLETE,
                    data=chunk,
                )
            )
        except Exception as e:
            logger.error(f"Error sending message stream: {e}")
            await self.event_bus.publish(
                StreamEvent(
                    etype=StreamEventType.STREAM_ERROR,
                    data=None,
                    error=str(e),
                )
            )
            raise e


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
        self.event_bus = get_event_manager()

    def _build_system_prompt(self) -> str:
        """
        Builds the system prompt for the language model.

        Returns:
            The system prompt string.
        """
        return Template(REACT_SYSTEM_PROMPT).safe_substitute(target_dir=self.target_dir)

    async def send_message_stream(
        self, task_str: str, tools: list[dict[str, Any]]
    ) -> AsyncIterator[ModelResponseStream]:
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
        response = await litellm.acompletion(
            model=litellm_model_,
            messages=messages,
            stream=True,
            tools=tools,
            tool_choice=tool_choice,
        )
        async for chunk in response:
            await self.event_bus.publish(ServerStreamEvent(etype=StreamEventType.CONTENT, data=chunk))
            yield chunk

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
