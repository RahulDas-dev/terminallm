# ruff: noqa: PLR0911
"""
This module provides utility functions for the LLM Coder application,
including logging, configuration management, and other helper functions.
"""

import logging
import os
from typing import ClassVar

from colorama import Fore, Style


class ColorFormatter(logging.Formatter):
    format_str: ClassVar[str] = "%(message)s"

    FORMATS: ClassVar[dict[int, str]] = {
        logging.DEBUG: f"{Fore.BLUE}{format_str}{Style.RESET_ALL}",
        logging.INFO: f"{Fore.YELLOW}{format_str}{Style.RESET_ALL}",
        logging.WARNING: f"{Fore.MAGENTA}{format_str}{Style.RESET_ALL}",
        logging.ERROR: f"{Fore.RED}{format_str}{Style.RESET_ALL}",
        logging.CRITICAL: f"{Fore.RED}{Style.BRIGHT}{format_str}{Style.RESET_ALL}",
    }

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno, self.format_str)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logger_for_sdk(name: str) -> logging.Logger:
    root_handlers = logging.getLogger().handlers
    current_logger = logging.getLogger(name)
    if not root_handlers:
        new_handler = logging.StreamHandler()
        new_handler.terminator = ""
        new_handler.setFormatter(ColorFormatter("%(message)s"))
        current_logger.addHandler(new_handler)
        current_logger.propagate = False
        current_logger.setLevel(logging.INFO)
        return current_logger

    # Remove  exixting Handlers from the current logger
    for handler in current_logger.handlers[:]:
        current_logger.removeHandler(handler)

    for handler_r in root_handlers:
        if type(handler_r) is logging.StreamHandler:
            new_handler = logging.StreamHandler()
            new_handler.terminator = ""
            new_handler.setFormatter(ColorFormatter("%(message)s"))
            current_logger.addHandler(new_handler)
        elif type(handler_r) is logging.FileHandler:
            new_handler = logging.FileHandler(
                handler_r.baseFilename,
                handler_r.mode,
                handler_r.encoding,
                handler_r.delay,
                handler_r.errors,
            )
            new_handler.terminator = ""
            new_handler.setFormatter(logging.Formatter("%(message)s"))
            current_logger.addHandler(new_handler)
        else:
            continue
    current_logger.propagate = False
    return current_logger


def get_litellm_model_params(model: str, provider: str) -> dict[str, str]:
    """
    Returns the model name formatted for use with the litellm library.
    This function handles special cases for different providers.

    Args:
        model: The model name, which may include a provider prefix
        provider: The provider name specified separately

    Returns:
        The properly formatted model name for litellm
    """
    # Format model name based on provider
    if provider == "openai":
        return {"model": model}
    if provider == "vertex_ai" and model == "gemini-1.5":
        return {"model": "vertex_ai/gemini-1.5-pro-002"}
    if provider == "vertex_ai" and model == "gemini-2.0":
        return {"model": "vertex_ai/gemini-2.0-flash-001"}
    if provider == "bedrock" and model == "claude-3-7-sonnet":
        return {"model": "bedrock/us.anthropic.claude-3-7-sonnet-20250219-v1:0"}
    if provider == "bedrock" and model == "pixtral-large":
        return {"model": "bedrock/us.mistral.pixtral-large-2502-v1:0"}
    if provider == "bedrock" and model == "deepseek-r1":
        return {"model": "bedrock/us.deepseek.r1-v1:0"}
    if provider == "ollama" and model == "deepseek-r1":
        return {"model": "ollama/deepseek-r1", "api_base": os.environ.get("OLLAMA_API_BASE", "")}
    raise ValueError(f"Unsupported model for provider {provider}: {model}")
