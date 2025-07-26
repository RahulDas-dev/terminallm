from pathlib import Path
from typing import Any

from .base import BaseTool, ToolExecutionContext, ToolExecutionResult, ToolParameter, ToolSchema


class ListDirectoryTool(BaseTool):
    """Tool for listing directory contents."""

    def __init__(self):
        super().__init__(name="list_directory", description="List the contents of a directory")

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="path",
                    data_type="string",
                    description="Path to the directory to list",
                    required=True,
                    default=".",
                ),
                ToolParameter(
                    name="show_hidden",
                    data_type="boolean",
                    description="Include hidden files and directories",
                    default=False,
                ),
                ToolParameter(
                    name="recursive",
                    data_type="boolean",
                    description="List directories recursively",
                    default=False,
                ),
                ToolParameter(
                    name="max_depth",
                    data_type="integer",
                    description="Maximum depth to list",
                    default=3,
                    extra={
                        "minimum": 1,
                        "maximum": 10,
                    },
                ),
            ],
            required=["path"],
        )

    async def execute(self, parameters: dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        """Execute the list directory tool."""
        dir_path = parameters.get("path", ".")
        show_hidden = parameters.get("show_hidden", False)
        recursive = parameters.get("recursive", False)
        max_depth = parameters.get("max_depth", 3)

        try:
            path = Path(dir_path).resolve()

            if not path.exists():
                return ToolExecutionResult(
                    content=f"Directory not found: {dir_path}",
                    success=False,
                )

            if not path.is_dir():
                return ToolExecutionResult(
                    content=f"Path is not a directory: {dir_path}",
                    success=False,
                )

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

            return ToolExecutionResult(
                content=content,
                success=True,
                metadata={
                    "path": str(path),
                    "total_entries": len(entries),
                    "directories": sum(1 for e in entries if e["is_dir"]),
                    "files": sum(1 for e in entries if not e["is_dir"]),
                },
            )

        except Exception as e:
            return ToolExecutionResult(
                content=f"Failed to list directory: {e!s}",
                success=False,
            )

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
