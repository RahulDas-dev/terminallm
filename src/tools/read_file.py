from pathlib import Path
from typing import Any

import aiofiles

from src.config import Config

from .base import Tool


class ReadFileTool(Tool):
    """
    A tool for reading files from the filesystem.
    """

    Name = "read_file"

    def __init__(self, config: Config):
        """
        Initializes the ReadFileTool.

        Args:
            config: The configuration object.
        """
        super().__init__(name="read_file", display_name="ReadFile", description="Reads a file from the filesystem")
        self.config = config

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": "Read contents from a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file",
                    }
                },
                "required": ["file_path"],
            },
        }

    async def execute(self, args: dict[str, Any], signal: Any = None) -> dict[str, Any]:
        """
        Executes the read file tool.

        Args:
            args: A dictionary of arguments, including the file path.
            signal: An optional signal to cancel the operation.

        Returns:
            A dictionary containing the file content and a display message.
        """
        file_path = Path(args["file_path"])
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()
            return {
                "llm_content": content,
                "return_display": f"Read {len(content)} characters from {file_path}",
            }
        except Exception as e:
            raise Exception(f"Error reading file: {e!s}") from e
