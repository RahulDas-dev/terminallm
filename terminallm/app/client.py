"""Module provides configuration and utility functions for the LLM client."""

from typing import Optional

DEFAULT_CONFIG = {
    "temperature": 0.1,
    "timeout": 600,
    "num_retries": 3,
}


def get_llm_config(client_name: str, config: Optional[dict] = None) -> dict[str, str]:  # noqa: ARG001
    """Get the configuration for the LLM client.

    Args:
        clint_name (str): The name of the client.
        config (dict | None): Optional configuration dictionary to override defaults.

    Returns:
        dict[str, str]: The configuration dictionary for the LLM client.

    """
    config = {} if config is None else config
    return {**DEFAULT_CONFIG, **config}
