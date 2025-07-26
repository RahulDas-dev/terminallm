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


class WriteFileTool(Tool):
    """
    A tool for writing content to a file.
    """

    def __init__(self, config: Config):
        """
        Initializes the WriteFileTool.

        Args:
            config: The configuration object.
        """
        super().__init__(
            name="write_file", display_name="WriteFile", description="Writes content to a file in the filesystem"
        )
        self.config = config

    @property
    def schema(self) -> dict[str, Any]:
        """
        Returns the schema for the write file tool's parameters.
        """
        return {
            "name": self.name,
            "description": "Write contents to a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file",
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file",
                    },
                },
                "required": ["file_path", "content"],
            },
        }

    async def should_confirm_execute(self, args: dict[str, Any], signal: Any = None) -> dict[str, Any]:
        """
        Determines if the user should confirm the write operation.

        Args:
            args: A dictionary of arguments, including the file path and content.
            signal: An optional signal to cancel the operation.

        Returns:
            A dictionary with the confirmation message.
        """
        return {
            "type": "write",
            "file_path": args["file_path"],
            "message": f"Write {len(args['content'])} characters to {args['file_path']}?",
        }

    async def execute(self, args: dict[str, Any], signal: Any = None) -> dict[str, Any]:
        """
        Executes the write file tool.

        Args:
            args: A dictionary of arguments, including the file path and content.
            signal: An optional signal to cancel the operation.

        Returns:
            A dictionary with a success message.
        """
        file_path = Path(args["file_path"])
        content = args["content"]
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(content)
            return {
                "llm_content": f"Successfully wrote {len(content)} characters to {file_path}",
                "return_display": f"Wrote {len(content)} characters to {file_path}",
            }
        except Exception as e:
            raise Exception(f"Error writing file: {e!s}") from e


class GlobTool(Tool):
    """
    A tool for finding files matching a pattern.
    """

    def __init__(self, config: Config):
        """
        Initializes the GlobTool.

        Args:
            config: The configuration object.
        """
        super().__init__(name="glob", display_name="Glob", description="Find files matching a pattern")
        self.config = config

    @property
    def schema(self) -> dict[str, Any]:
        """
        Returns the schema for the glob tool's parameters.
        """
        return {
            "name": self.name,
            "description": "Find files matching a glob pattern",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "The glob pattern to match files",
                    },
                    "path": {
                        "type": "string",
                        "description": "The directory to search in",
                    },
                },
                "required": ["pattern"],
            },
        }

    async def execute(self, args: dict[str, Any], signal: Any = None) -> dict[str, Any]:
        """
        Executes the glob tool.

        Args:
            args: A dictionary of arguments, including the pattern and path.
            signal: An optional signal to cancel the operation.

        Returns:
            A dictionary containing the list of files found.
        """
        pattern = args["pattern"]
        path = Path(args.get("path", Path.cwd()))

        try:
            results = list(path.rglob(pattern))
            sorted_results = sorted(results)
            result_text = "\n".join(map(str, sorted_results))
            return {
                "llm_content": result_text,
                "return_display": f"Found {len(sorted_results)} files matching pattern '{pattern}'",
            }
        except Exception as e:
            raise Exception(f"Error in glob search: {e!s}") from e
