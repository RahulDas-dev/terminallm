import logging
from abc import abstractmethod
from typing import Literal, NoReturn, Optional

from .db.database import Database
from .ios.base import InputDevice, OutputDevice

logger = logging.getLogger(__name__)

TMode = Literal["tt", "ms", "mt", "ts"]


class BaseEngine:
    _client_name: str
    _input_device: InputDevice
    _output_device: OutputDevice
    _chat_history: list[dict[str, str]]
    _llm_config: dict[str, str]

    def __init__(
        self,
        input_device: InputDevice,
        output_device: OutputDevice,
        client_name: Optional[str] = None,
    ):
        self._client_name = client_name
        self._input_device = input_device
        self._output_device = output_device
        self._chat_history = []
        self._llm_config = {}

    @abstractmethod
    def _configure_llm(self) -> None:
        pass

    def _save_chat_history(self) -> None:
        try:
            llm_config_ = {**self._llm_config, "model": self._client_name}
            Database().insert_data(app_mode="qna", chat_history=self._chat_history, llm_config=llm_config_)
        except Exception as err:
            logger.exception(err)

    def _perse_input(self, message: str) -> Optional[str]:
        message_ = message.strip().lower()
        persed_message = None
        if message_ in ["q:", "quit"]:
            if self._chat_history:
                self._save_chat_history()
            persed_message = None
        elif message_ in ["r:", "new"]:
            self._save_chat_history()
            self._chat_history = []
            self._output_device.deliver_message("New Chat Initiated \n\n", color="magenta")
            persed_message = ""
        elif message.strip().lower() == "":
            persed_message = ""
        else:
            persed_message = message
        return persed_message

    def _receive_input(self, msg_input: Optional[str] = None) -> Optional[str]:
        retry_limit, retry_counter = 5, 1
        while retry_counter < retry_limit:
            if retry_counter != 1:
                self._output_device.deliver_message("Kindly enter <q:> to quit or a valid message \n\t", color="red")
            msg_recived = self._input_device.accept_input(msg_input)
            msg_persed = self._perse_input(msg_recived)
            if msg_persed == "":
                msg_persed = None
                retry_counter += 1
                continue
            break
        return msg_persed

    @abstractmethod
    def run(self) -> NoReturn:
        raise NotImplementedError('Method "run" must be implemented in the child class')
