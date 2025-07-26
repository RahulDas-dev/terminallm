from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiofiles

from .base import BaseTool, ToolExecutionContext, ToolExecutionResult, ToolParameter, ToolSchema


class ReadFileTool(BaseTool):
    """Tool for reading file contents."""

    def __init__(self):
        super().__init__(name="read_file", description="Read the contents of a file")

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(name="path", data_type="string", description="Path to the file to read", required=True),
                ToolParameter(
                    name="encoding", data_type="string", description="File encoding (default: utf-8)", default="utf-8"
                ),
                ToolParameter(
                    name="start_line",
                    data_type="integer",
                    description="Start reading from this line (1-based, optional)",
                    default=1,
                    extra={
                        "minimum": 1,
                    },
                ),
                ToolParameter(
                    name="end_line",
                    data_type="integer",
                    description="Stop reading at this line (1-based, optional)",
                    default=1,
                    extra={
                        "minimum": 1,
                    },
                ),
            ],
            required=["path"],
        )

    async def execute(self, parameters: dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        """Execute the read file tool."""
        file_path = parameters["path"]
        encoding = parameters.get("encoding", "utf-8")
        start_line = parameters.get("start_line")
        end_line = parameters.get("end_line")

        try:
            # Resolve path
            path = Path(file_path).resolve()

            # Security check - ensure path exists and is a file
            if not path.exists():
                return ToolExecutionResult(
                    content=f"File not found: {file_path}",
                    success=False,
                )

            if not path.is_file():
                return ToolExecutionResult(
                    content=f"Path is not a file: {file_path}",
                    success=False,
                )

            # Read file
            async with aiofiles.open(path, encoding=encoding) as f:
                if start_line or end_line:
                    # Read specific lines
                    lines = await f.readlines()

                    start_idx = (start_line - 1) if start_line else 0
                    end_idx = end_line if end_line else len(lines)

                    selected_lines = lines[start_idx:end_idx]
                    content = "".join(selected_lines)
                else:
                    # Read entire file
                    content = await f.read()

            # Get file info
            stat = path.stat()
            file_info = {
                "path": str(path),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "lines_read": len(content.splitlines()) if content else 0,
            }

            result_content = f"File: {file_path}\\n\\n{content}"

            return ToolExecutionResult(
                content=result_content,
                success=True,
                metadata=file_info,
            )

        except UnicodeDecodeError as e:
            return ToolExecutionResult(
                content=f"Failed to decode file with encoding '{encoding}': {e!s}",
                success=False,
            )
        except Exception as e:
            return ToolExecutionResult(
                content=f"Failed to read file: {e!s}",
                success=False,
            )
