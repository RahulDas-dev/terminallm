import logging
import sys
from typing import NoReturn

from litellm import completion, get_max_tokens, token_counter
from termcolor import colored

from .base import BaseEngine
from .client import get_llm_config
from .ios.base import InputDevice, OutputDevice

logger = logging.getLogger(__name__)


class QnaEnginee(BaseEngine):
    def __init__(
        self,
        input_device: InputDevice,
        output_device: OutputDevice,
        client_name: str | None = None,
    ):
        super().__init__(input_device, output_device, client_name)

    def _configure_llm(self) -> None:
        self._llm_config = get_llm_config(self._client_name)

    def _send_to_llm(self) -> str | None:
        # chunks = []
        try:
            response = completion(
                model=self._client_name,
                messages=self._chat_history,
                stream=True,
                caching=False,
                **self._llm_config,
            )
        except Exception as err:
            logger.exception(err)
            reply_msg = None
        else:
            reply_msg = self._output_device.deliver_stream_response(response)
            # self._output_device.deliver_stream_response("Response: - \n\t", color="yellow")
            # for chunk in response:
            #    chunks.append(chunk)
            #    content = chunk.choices[0].delta.content
            #    self._output_device.deliver_response(content)
            # message_final = stream_chunk_builder(chunks, messages=None)
            # reply_msg = message_final.choices[0].message.content
            # self._output_device.deliver_response(reply_msg, stream=True)
            # self._output_device.deliver_message("\n")
        return reply_msg

    def _ask_for_next_query(self) -> None:
        token_used = token_counter(model=self._client_name, messages=self._chat_history)
        try:
            max_tokens = get_max_tokens(self._client_name)
        except Exception:
            max_tokens = "NONE"
        message = (
            colored(f"\nTokens Used: {token_used} / {max_tokens}", "light_red")
            + colored(" | ", "light_blue")
            + colored("enter <q:> to quit -\n\t", "yellow")
        )
        self._output_device.deliver_message(message)

    def run(self, new: bool = True) -> NoReturn:
        self._configure_llm()
        message = self._receive_input("Query : - \n\t")
        if message is None:
            sys.exit(0)
        self._chat_history = [] if new else self._chat_history
        self._chat_history.append({"role": "user", "content": message})

        while True:
            self._output_device.deliver_message("\n")
            reply_msg = self._send_to_llm()
            self._chat_history.append({"role": "assistant", "content": reply_msg})

            self._ask_for_next_query()
            message = self._receive_input()
            if message is None:
                break
            self._chat_history.append({"role": "user", "content": message})
        sys.exit(0)
