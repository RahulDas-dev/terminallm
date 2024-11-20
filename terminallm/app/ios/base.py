from typing import Any, Optional, Protocol, runtime_checkable

from litellm import CustomStreamWrapper


@runtime_checkable
class InputDevice(Protocol):
    def accept_input(self) -> str:
        pass


@runtime_checkable
class OutputDevice(Protocol):
    def deliver_response(self, objects: Any) -> None:
        pass

    def deliver_stream_response(self, response: CustomStreamWrapper) -> Optional[str]:
        pass

    def deliver_message(self, objects: Any, color: Optional[str] = None) -> None:
        pass
