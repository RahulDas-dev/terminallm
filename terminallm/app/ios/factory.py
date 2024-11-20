from .audio import MicroPhone, Speaker
from .base import InputDevice, OutputDevice
from .console import Console


def build_io_devices(mode: str) -> tuple[InputDevice, OutputDevice]:
    if mode.lower() == "tt":
        inputd = Console()
        outputd = Console()
    elif mode.lower() == "ms":
        inputd = MicroPhone()
        outputd = Speaker()
    elif mode.lower() == "mt":
        inputd = MicroPhone()
        outputd = Console()
    elif mode.lower() == "ts":
        inputd = Console()
        outputd = Speaker()
    else:
        raise ValueError(f"Invalid mode: {mode}")
    return inputd, outputd
