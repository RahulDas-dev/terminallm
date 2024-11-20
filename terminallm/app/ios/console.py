import logging
from typing import Any, Optional

from litellm import CustomStreamWrapper, stream_chunk_builder
from termcolor._types import Color

from .base import InputDevice, OutputDevice
from .utility import modify_logger_behaviour

logger = logging.getLogger(__name__)


class Console(InputDevice, OutputDevice):
    def __init__(self):
        self.logger = modify_logger_behaviour(__name__)

    def deliver_response(self, objects: Any) -> None:
        objects = "" if objects is None else objects
        self.logger.info(objects, extra={"color": "green"})

    def deliver_stream_response(self, response: CustomStreamWrapper) -> Optional[str]:
        self.logger.info("Response: - \n\t", extra={"color": "yellow"})
        chunks = []
        for chunk in response:
            chunks.append(chunk)
            content = chunk.choices[0].delta.content
            self.logger.info(content, extra={"color": "green"})
        message_final = stream_chunk_builder(chunks, messages=None)
        reply_msg = message_final.choices[0].message.content
        self.logger.info("\n")
        return reply_msg

    def accept_input(self, message: str) -> str:
        message = "" if message is None else message
        self.logger.info(message, extra={"color": "yellow"})
        input_str = input()
        # self.logger.info(input_str, extra={"color": "blue"})
        return input_str.strip()

    def deliver_message(self, objects: Any, color: Optional[Color] = None) -> None:
        self.logger.info(objects, extra={"color": color})
