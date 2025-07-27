import logging
from typing import Any

import litellm
from litellm.types.utils import Choices, Message, ModelResponse  # , ModelResponseStream

from lib.config import Config
from lib.event_sys import StreamEvent, StreamEventType, get_event_manager
from lib.tools import ToolExecutor, get_registry

from .client import LlmClient

logger = logging.getLogger(__name__)


class ContentGenerator:
    def __init__(self, config: Config, target_dir: str):
        self.config = config
        self.target_dir = target_dir
        self.client = LlmClient(target_dir=self.target_dir, config=self.config)
        self.event_bus = get_event_manager()
        self.tool_call_manager = ToolExecutor(self.config, get_registry())

    async def generate_content_streaming(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> str | None:
        final_response = None
        while True:
            chunks = []
            async for chunk in self.client.send_message_stream(messages=messages, tools=tools):
                chunks.append(chunk)
            response_ = litellm.stream_chunk_builder(chunks)
            response_choice: Choices = response_.choices[0]
            response_message = response_choice.message
            messages = self._update_llm_response(response_message, messages)

            if response_message.tool_calls:
                tool_response = await self.tool_call_manager.schedule(
                    response_message.tool_calls,
                    signal=None,
                )
                messages = self._update_tool_response(tool_response, messages)
            await self._token_counts(response_)
            if response_message.content and response_choice.finish_reason == "stop":
                final_response = response_message.content
                break
        return final_response

    def _update_llm_response(self, response_message: Message, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Format the response from the model into a readable string.
        """
        messages_ = messages.copy()
        if response_message.tool_calls and response_message.content:
            messages_.append(
                {
                    "role": "assistant",
                    "content": response_message.content,
                    "tool_calls": response_message.tool_calls,
                }
            )
        elif response_message.content and not response_message.tool_calls:
            messages_.append({"role": "assistant", "content": response_message.content})
        elif response_message.tool_calls and response_message.content is None:
            messages_.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": response_message.tool_calls,
                }
            )
        else:
            logger.warning("Received an assistant message with no content or tool calls.")
        return messages_

    def _update_tool_response(self, tool_response: Any, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Update the messages list with the tool response.
        """
        messages_ = messages.copy()
        for message in tool_response:
            messages_.append(
                {
                    "role": "tool",
                    "content": message["content"],
                    "tool_call_id": message["tool_call_id"],
                    "name": message["name"],
                }
            )
        return messages_

    async def _token_counts(self, response: ModelResponse) -> tuple[int, int, int | None]:
        if not response:
            logger.warning("No Usage information, Response is None or empty.")
            return 0, 0, None
        if not hasattr(response, "usage") or response.usage is None:
            logger.warning("Response does not contain usage information.")
            return 0, 0, None
        total_tokens = response.usage.total_tokens
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        try:
            tokens_allowed = litellm.utils.get_max_tokens(model=self.config.model)
        except Exception:
            tokens_allowed = None
        await self.event_bus.publish(
            StreamEvent(
                etype=StreamEventType.TOKEN_COUNT,
                token_count={
                    "total_tokens": total_tokens,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "tokens_allowed": tokens_allowed,
                },
            )
        )
        return prompt_tokens, completion_tokens, tokens_allowed
