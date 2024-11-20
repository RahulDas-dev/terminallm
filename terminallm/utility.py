import importlib.metadata
from importlib.metadata import PackageNotFoundError
from pathlib import Path


def get_version() -> str:
    try:
        version = importlib.metadata.version("terminallm")
    except PackageNotFoundError:
        version = "0.1.0"
    return version


def get_absolute_path(path_str: str) -> Path:
    return Path(path_str) if Path(path_str).is_absolute() else Path(path_str).resolve()


def llm_config_path() -> Path:
    return Path.home() / ".termilallm_config"
