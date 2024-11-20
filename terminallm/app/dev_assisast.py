import json
import logging
import sys
from typing import NoReturn

from litellm import Message, completion, get_max_tokens, stream_chunk_builder, token_counter
from termcolor import colored

from terminallm.app.client import get_llm_config
from terminallm.app.system_message.dev_assisast import SYSTEM_MESSAGE
from terminallm.app.tools.functions import (
    find_directory,
    find_file,
    get_absolute_path,
    get_curret_directory,
    list_files,
    read_file,
    write_file,
)
from terminallm.app.tools.schema_builder import get_function_schema

from .base import BaseApp
from .ios.base import InputDevice, OutputDevice

logger = logging.getLogger(__name__)


class DevAssisast(BaseApp):
    def __init__(
        self,
        input_device: InputDevice,
        output_device: OutputDevice,
        client_name: str | None = None,
    ):
        super().__init__(input_device, output_device, client_name)

        self.f_map = {}

    def _configure_llm(self) -> None:
        client_names = "gpt-3.5-turbo" if self._client_names is None else self._client_names[0]
        client_config = get_llm_config(client_names)
        self._client_names = client_names
        tools = []
        f_map = {}
        for fitem in [
            get_absolute_path,
            list_files,
            find_file,
            find_directory,
            read_file,
            get_curret_directory,
            write_file,
        ]:
            if not callable(fitem):
                logger.warning(f"{fitem} is not a valid functions ...")
            f_map[fitem.__name__] = fitem
            f_signature = get_function_schema(fitem, name=fitem.__name__)
            tools.append(f_signature)
        if tools:
            client_config["tools"] = tools
            client_config["tool_choice"] = "auto"
        self.f_map = f_map
        self._llm_config = client_config

    def _send_to_llm(self) -> Message:
        chunks = []
        try:
            response = completion(
                model=self._client_names,
                messages=self._chat_history,
                stream=True,
                caching=False,
                **self._llm_config,
            )
        except Exception as err:
            self._console.log(err)
            reply_msg = None
        else:
            self._console.print_message("Response: - \n\t", color="yellow")
            for chunk in response:
                chunks.append(chunk)
                content = chunk.choices[0].delta.content
                if content is not None:
                    self._console.print_llm_response(content)
            message_final = stream_chunk_builder(chunks, messages=self._chat_history)
            reply_msg = message_final.choices[0].message
            self._console.print_message("\n")
        return reply_msg

    def _ask_for_next_query(self) -> None:
        token_used = token_counter(model=self._client_names, messages=self._chat_history)
        try:
            max_tokens = get_max_tokens(self._client_names)
        except Exception:
            max_tokens = "NONE"
        message = (
            colored(f"\nTokens Used: {token_used} / {max_tokens}", "light_red")
            + colored(" | ", "light_blue")
            + colored("enter <q:> to quit -\n\t", "yellow")
        )
        self._console.print_message(message)

    def _resolve_function_calls(self, reply_msg: Message) -> list[dict[str, str]]:
        functions = []
        if reply_msg.tool_calls is not None:
            functions = functions + list(reply_msg.tool_calls)
        if reply_msg.function_call is not None:
            functions = functions + list(reply_msg.function_call)

        results = []
        for f_item in functions:
            if f_item.function.name not in self.f_map:
                continue
            func = self.f_map[f_item.function.name]
            args = json.loads(f_item.function.arguments)
            func_details = (
                colored("\n\tFunction: ", "white")
                + colored(f"{f_item.function.name}", "cyan")
                + colored("\n\tArguments: ", "white")
                + colored(f"{args!s}\n", "cyan")
            )
            self._console.print_message(func_details)
            try:
                result = func(**args)
            except Exception as err:
                logger.exception(err)
                result = f"Error: {err}"
            result_msg = colored("\tResult: ", "white") + colored(f"{result!s}\n", "light_cyan")
            self._console.print_message(result_msg)
            results.append(
                {
                    "tool_call_id": f_item.id,
                    "role": "tool",
                    "name": f_item.function.name,
                    "content": result,
                }
            )
        return results

    def run(self, new: bool = True) -> NoReturn:
        self._configure_llm()
        message = self.receive_input("Query : - \n\t")
        if message is None:
            sys.exit(0)
        self._chat_history = (
            [
                {
                    "role": "system",
                    "content": SYSTEM_MESSAGE.format(current_directory=get_curret_directory()),
                }
            ]
            if new
            else self._chat_history
        )
        self._chat_history.append({"role": "user", "content": message})

        while True:
            self._console.print_message("\n")
            reply_msg = self._send_to_llm()
            if reply_msg is None:
                break
            if reply_msg.tool_calls is None and reply_msg.function_call is None:
                self._chat_history.append({"role": "assistant", "content": reply_msg.content})
                self._ask_for_next_query()
                message = self.receive_input()
                if message is None:
                    break
                self._chat_history.append({"role": "user", "content": message})
            elif reply_msg.tool_calls is not None:
                self._chat_history.append(
                    {
                        "role": reply_msg.role,
                        "content": reply_msg.content,
                        "tool_calls": [tool.model_dump() for tool in reply_msg.tool_calls],
                    }
                )
                results = self._resolve_function_calls(reply_msg)
                self._chat_history.extend(results)
            elif reply_msg.function_call_calls is not None:
                pass
        sys.exit(0)
