from pathlib import Path
from typing import Any

from lib.config import Config

from .base import Tool


class ListDirectoryTool(Tool):
    """Tool for listing directory contents."""

    def __init__(self, config: Config):
        super().__init__(
            name="list_directory", display_name="List Directory", description="List the contents of a directory"
        )
        self.config = config

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the directory to list",
                        "default": ".",
                    },
                    "show_hidden": {
                        "type": "boolean",
                        "description": "Include hidden files and directories",
                        "default": False,
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "List directories recursively",
                        "default": False,
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum depth to list",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 10,
                    },
                },
                "required": ["path"],
            },
        }

    async def execute(self, args: dict[str, Any], signal: Any = None):
        """Execute the list directory tool."""
        dir_path = args.get("path", ".")
        show_hidden = args.get("show_hidden", False)
        recursive = args.get("recursive", False)
        max_depth = args.get("max_depth", 3)

        try:
            path = Path(dir_path).resolve()

            if not path.exists():
                return {
                    "llm_content": f"Directory not found: {dir_path}",
                    "return_display": f"Directory not found: {dir_path}",
                }

            if not path.is_dir():
                return {
                    "llm_content": f"Path is not a directory: {dir_path}",
                    "return_display": f"Path is not a directory: {dir_path}",
                }

            # List directory contents
            entries = await self._list_directory_recursive(path, show_hidden, recursive, max_depth, 0)

            # Format output
            output_lines = [f"Directory listing for: {path}\\n"]

            for entry in entries:
                indent = "  " * entry["depth"]
                type_indicator = "/" if entry["is_dir"] else ""
                size_info = f" ({entry['size']} bytes)" if not entry["is_dir"] else ""

                output_lines.append(f"{indent}{entry['name']}{type_indicator}{size_info}")

            content = "\\n".join(output_lines)

            return {"llm_content": content, "return_display": f"Listed {len(entries)} entries in directory: {path}"}

        except Exception as e:
            return {
                "llm_content": f"Failed to list directory: {e!s}",
                "return_display": f"Failed to list directory: {e!s}",
            }

    async def _list_directory_recursive(
        self,
        path: Path,
        show_hidden: bool,
        recursive: bool,
        max_depth: int,
        current_depth: int,
    ) -> list[dict[str, Any]]:
        """List directory contents recursively."""
        entries = []

        try:
            for item in path.iterdir():
                # Skip hidden files if not requested
                if not show_hidden and item.name.startswith("."):
                    continue

                entry = {
                    "name": item.name,
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "depth": current_depth,
                }

                if item.is_file():
                    try:
                        entry["size"] = item.stat().st_size
                    except OSError:
                        entry["size"] = 0
                else:
                    entry["size"] = 0

                entries.append(entry)

                # Recurse into directories
                if recursive and item.is_dir() and current_depth < max_depth:
                    try:
                        sub_entries = await self._list_directory_recursive(
                            item, show_hidden, recursive, max_depth, current_depth + 1
                        )
                        entries.extend(sub_entries)
                    except PermissionError:
                        # Skip directories we can't access
                        pass

        except PermissionError:
            # Handle permission denied
            pass

        return entries
