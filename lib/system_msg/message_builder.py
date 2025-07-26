import os
from pathlib import Path

from lib.utils.common import has_python_files
from lib.utils.git_utils import is_git_repository

from ._messages import (
    COMPRESSION_MESSAGES,
    CORE_SYSTEM_MESSAGE,
    DEBUGGING_SYSTEM_MESSAGE,
    DIRECT_SYSTEM_ACCESS_MESSAGE,
    DOCKER_CONTAINER_MESSAGE,
    DOCUMENTATION_SYSTEM_MESSAGE,
    FINAL_MESSAGE,
    GIT_CONTEXT_MESSAGE,
    INTERACTION_EXAMPLES,
    PYTHON_CONTEXT_MESSAGE,
    REFACTORING_SYSTEM_MESSAGE,
    REVIEWER_SYSTEM_MESSAGE,
    SANDBOX_CONTEXT_MESSAGE,
    TESTING_SYSTEM_MESSAGE,
)


class MessageBuilder:
    """
    Class to handle system messages for the application.
    """

    @classmethod
    def get_system_message(cls, workspace_path: Path) -> str:
        _system_message = cls._retrieve_system_message(workspace_path)
        return cls._retrieve_default_system_message(workspace_path) if _system_message is None else _system_message

    @classmethod
    def _retrieve_system_message(cls, workspace_path: Path) -> str | None:
        """
        Retrieve the system message from the file.
        """
        _system_md_var = os.environ.get("SYSTEM_MD", "").lower()

        if not _system_md_var:
            return None
        config_dir = workspace_path / ".config"
        _system_md_enabled = False
        if config_dir.exists():
            _system_message_file = config_dir / "system_messages.md"
            _system_md_enabled = bool(Path(_system_message_file).exists())
        if not _system_md_enabled:
            return None
        with open(_system_message_file, "r") as f:
            return f.read()

    @classmethod
    def _retrieve_default_system_message(cls, workspace_path: Path) -> str:
        _context_informations = []
        _sandbox_context = cls._retrive_sanbox_context()
        if _sandbox_context:
            _context_informations.append(_sandbox_context)
        _git_context = cls._retrive_git_context(workspace_path)
        if _git_context:
            _context_informations.append(_git_context)
        _has_python_context = cls._retrieve_python_context(workspace_path)
        if _has_python_context:
            _context_informations.append(_has_python_context)

        if _context_informations:
            return (
                CORE_SYSTEM_MESSAGE
                + "\n\n"
                + "\n".join(_context_informations)
                + "\n\n"
                + INTERACTION_EXAMPLES
                + "\n\n"
                + FINAL_MESSAGE
            )
        return CORE_SYSTEM_MESSAGE + "\n\n" + INTERACTION_EXAMPLES + "\n\n" + FINAL_MESSAGE

    @classmethod
    def _retrive_sanbox_context(cls) -> str:
        """
        Retrieve the sandbox context for the system message.
        """
        if os.environ.get("SANDBOX_CONTEXT"):
            return SANDBOX_CONTEXT_MESSAGE
        if os.environ.get("DOCKER_CONTAINER"):
            return DOCKER_CONTAINER_MESSAGE
        return DIRECT_SYSTEM_ACCESS_MESSAGE

    @classmethod
    def _retrive_git_context(cls, workspace_path: Path) -> str | None:
        if is_git_repository(workspace_path):
            return GIT_CONTEXT_MESSAGE
        return None

    @classmethod
    def _retrieve_python_context(cls, workspace_path: Path) -> str | None:
        """
        Retrieve the core system message.
        """
        if has_python_files(workspace_path):
            return PYTHON_CONTEXT_MESSAGE
        return None

    @classmethod
    def get_compression_messages(cls) -> str:
        return COMPRESSION_MESSAGES

    @classmethod
    def get_toolusage_messages(cls, available_tools: list[str]) -> str:
        if not available_tools:
            return ""

        tool_descriptions = {
            "file_read": "Read file contents",
            "file_write": "Write content to files",
            "file_edit": "Edit existing files",
            "shell_execute": "Execute shell commands",
            "code_search": "Search for code patterns",
            "git_operations": "Git repository operations",
            "web_fetch": "Fetch web content",
            "memory_store": "Store and retrieve user preferences",
        }

        tools_section = "# Available Tools\n\nYou have access to the following tools:\n"

        for tool in available_tools:
            description = tool_descriptions.get(tool, f"Tool: {tool}")
            tools_section += f"- **{tool}**: {description}\n"

        tools_section += "\nUse these tools effectively to accomplish user requests."

        return tools_section

    @classmethod
    def get_specialized_messages(cls, prompt_type: str) -> str:
        prompts = {
            "code_review": REVIEWER_SYSTEM_MESSAGE,
            "debugging": DEBUGGING_SYSTEM_MESSAGE,
            "testing": TESTING_SYSTEM_MESSAGE,
            "refactoring": REFACTORING_SYSTEM_MESSAGE,
            "documentation": DOCUMENTATION_SYSTEM_MESSAGE,
        }

        if prompt_type in prompts:
            return prompts[prompt_type]

        return ""
