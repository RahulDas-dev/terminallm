import logging
import time
from typing import Any, Optional

import pyttsx3
import speech_recognition
from litellm import CustomStreamWrapper, stream_chunk_builder
from termcolor._types import Color

from .base import InputDevice, OutputDevice
from .utility import modify_logger_behaviour

logger = logging.getLogger(__name__)


class MicroPhone(InputDevice):
    def __init__(self, enable_logging: bool = True, enable_audio: bool = False):
        self.audio = speech_recognition.Recognizer()
        self.logger = modify_logger_behaviour(__name__)
        self.enable_logging = enable_logging
        self.enable_audio = enable_audio

    def accept_input(self, message: str | None) -> str:
        text_accmulator = []
        start_time = time.time()
        max_wait_time = 3
        if self.enable_logging and message is not None:
            self.logger.info(message, extra={"color": "yellow"})
        if self.enable_audio:
            self._speak_text(message)
        while True:
            with speech_recognition.Microphone() as source:
                # wait for a second to let the recognizer
                # adjust the energy threshold based on
                # the surrounding noise level
                self.audio.adjust_for_ambient_noise(source, duration=0.2)
                # listens for the user's input
                audio = self.audio.listen(source, stream=False, timeout=100)
                # Using google to recognize audio
                if audio is None:
                    continue
                try:
                    text = self.audio.recognize_google(audio)
                    text = text.lower()
                    if self.enable_logging:
                        self.logger.info(text, extra={"color": "white"})
                    if self.enable_audio:
                        self._speak_text(text)
                    text_accmulator.append(text)
                except speech_recognition.exceptions.UnknownValueError:
                    pass
                else:
                    if time.time() - start_time > max_wait_time and text_accmulator:
                        break
        return " ".join(text_accmulator)

    def _speak_text(self, text: str) -> None:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()


class Speaker(OutputDevice):
    def __init__(self, enable_logging: bool = True):
        self.engine = pyttsx3.init()
        # self.engine.setProperty("rate", 125)
        voices = self.engine.getProperty("voices")
        self.engine.setProperty("voice", voices[1].id)
        self.logger = modify_logger_behaviour(__name__)
        self.enable_logging = enable_logging

    def deliver_response(self, response: Any) -> None:
        response = "" if response is None else response
        if self.enable_logging:
            self.logger.info(response, extra={"color": "green"})
        self.engine.say(response)
        self.engine.runAndWait()

    def deliver_stream_response(self, response: CustomStreamWrapper) -> Optional[str]:
        self.logger.info("Response: - \n\t", extra={"color": "yellow"})
        chunks = []
        for chunk in response:
            chunks.append(chunk)
            content = chunk.choices[0].delta.content
            content = "" if content is None else content
            self.logger.info(content, extra={"color": "green"})
        message_final = stream_chunk_builder(chunks, messages=None)
        reply_msg = message_final.choices[0].message.content
        self.logger.info("\n")
        self.engine.say(reply_msg)
        self.engine.runAndWait()
        return reply_msg

    def deliver_message(self, message: Any, color: Optional[Color] = None) -> None:
        if self.enable_logging:
            self.logger.info(message, extra={"color": color})
        # self.engine.say(message)
        # self.engine.runAndWait()
