from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiofiles

from .base import BaseTool, ToolExecutionContext, ToolExecutionResult, ToolParameter, ToolSchema


class WriteFileTool(BaseTool):
    """Tool for writing file contents."""

    def __init__(self):
        super().__init__(name="write_file", description="Write content to a file")

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(name="path", data_type="string", description="Path to the file to write", required=True),
                ToolParameter(
                    name="content", data_type="string", description="Content to write to the file", required=True
                ),
                ToolParameter(
                    name="encoding", data_type="string", description="File encoding (default: utf-8)", default="utf-8"
                ),
                ToolParameter(
                    name="create_dirs",
                    data_type="boolean",
                    description="Create parent directories if they don't exist",
                    default=True,
                ),
            ],
            required=["path", "content"],
        )

    async def should_confirm_execute(self, parameters: dict[str, Any], context: ToolExecutionContext) -> bool:
        """Confirm before overwriting existing files."""
        file_path = parameters["path"]
        path = Path(file_path)
        return path.exists()

    async def execute(self, parameters: dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        """Execute the write file tool."""
        file_path = parameters["path"]
        content = parameters["content"]
        encoding = parameters.get("encoding", "utf-8")
        create_dirs = parameters.get("create_dirs", True)

        try:
            path = Path(file_path).resolve()

            # Create parent directories if needed
            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)

            # Write file atomically
            temp_path = path.with_suffix(path.suffix + ".tmp")

            async with aiofiles.open(temp_path, "w", encoding=encoding) as f:
                await f.write(content)

            # Atomic move
            temp_path.replace(path)

            # Get file info
            stat = path.stat()
            file_info = {
                "path": str(path),
                "size": stat.st_size,
                "lines_written": len(content.splitlines()),
                "created": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            }

            return ToolExecutionResult(
                content=f"Successfully wrote {len(content)} characters to {file_path}",
                success=True,
                metadata=file_info,
            )

        except Exception as e:
            return ToolExecutionResult(
                content=f"Failed to write file: {e!s}",
                success=False,
            )
