import fnmatch
import glob as glob_module
import logging
from pathlib import Path
from typing import Any

from lib.base_types import CancellationToken

from .base import BaseTool, ToolExecutionContext, ToolExecutionResult, ToolParameter, ToolSchema

logger = logging.getLogger("tools")


class GlobTool(BaseTool):
    """Tool for finding files using glob patterns."""

    def __init__(self, root_directory: str | None = None):
        super().__init__(
            name="glob",
            description="Finds files and directories using glob patterns. "
            "Supports wildcards, recursive search, and file filtering.",
        )
        self.root_directory = Path(root_directory) if root_directory else Path.cwd()
        self.root_directory = self.root_directory.resolve()

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="pattern",
                    data_type="string",
                    description="Glob pattern to match files and directories (e.g., '*.py', '**/*.js', 'src/**/test_*.py')",
                    required=True,
                ),
                ToolParameter(
                    name="include_dirs",
                    data_type="boolean",
                    description="Whether to include directories in results (default: false)",
                    default=False,
                ),
                ToolParameter(
                    name="max_results",
                    data_type="integer",
                    description="Maximum number of results to return (default: 1000)",
                    default=1000,
                    extra={
                        "minimum": 1,
                        "maximum": 10000,
                    },
                ),
                ToolParameter(
                    name="base_path",
                    data_type="string",
                    description="Base directory to search from (optional, defaults to current directory)",
                ),
            ],
            required=["pattern"],
        )

    def _is_within_root(self, path: Path) -> bool:
        """Check if path is within the root directory."""
        try:
            path.resolve().relative_to(self.root_directory)
            return True
        except ValueError:
            return False

    def _should_ignore_path(self, path: Path) -> bool:
        """Check if path should be ignored based on common patterns."""
        ignore_patterns = [
            "__pycache__",
            ".git",
            ".svn",
            ".hg",
            "node_modules",
            ".DS_Store",
            ".env",
            "*.pyc",
            "*.pyo",
            "*.pyd",
        ]

        path_str = str(path)
        name = path.name

        for pattern in ignore_patterns:
            if pattern.startswith("*"):
                if fnmatch.fnmatch(name, pattern):
                    return True
            elif pattern in path_str:
                return True

        return False

    async def execute(
        self,
        parameters: dict[str, Any],
        context: ToolExecutionContext,
        cancellation_token: CancellationToken | None = None,
    ) -> ToolExecutionResult:
        """Execute the glob tool."""
        try:
            pattern = parameters.get("pattern", "").strip()
            include_dirs = parameters.get("include_dirs", False)
            max_results = parameters.get("max_results", 1000)
            base_path_str = parameters.get("base_path")

            if not pattern:
                return ToolExecutionResult(
                    success=False,
                    content="Error: pattern parameter is required and cannot be empty.",
                    metadata={"error": "empty_pattern"},
                )

            # Determine base path
            if base_path_str:
                base_path = Path(base_path_str)
                if not base_path.is_absolute():
                    return ToolExecutionResult(
                        success=False,
                        content=f"Error: base_path must be absolute: {base_path_str}",
                        metadata={"error": "invalid_base_path"},
                    )

                if not self._is_within_root(base_path):
                    return ToolExecutionResult(
                        success=False,
                        content=f"Error: base_path must be within root directory ({self.root_directory}): {base_path_str}",
                        metadata={"error": "base_path_outside_root"},
                    )
            else:
                base_path = self.root_directory

            if not base_path.exists():
                return ToolExecutionResult(
                    success=False,
                    content=f"Error: base_path does not exist: {base_path}",
                    metadata={"error": "base_path_not_found"},
                )

            # Perform glob search
            try:
                search_pattern = str(base_path / pattern)
                matches = glob_module.glob(search_pattern, recursive=True)

                # Filter and process results
                results = []
                for match_str in matches:
                    match_path = Path(match_str)

                    # Skip if path should be ignored
                    if self._should_ignore_path(match_path):
                        continue

                    # Check if it's a file or directory
                    is_dir = match_path.is_dir()
                    is_file = match_path.is_file()

                    # Filter based on include_dirs setting
                    if is_dir and not include_dirs:
                        continue

                    if not is_file and not is_dir:
                        continue  # Skip broken symlinks, etc.

                    # Calculate relative path
                    try:
                        relative_path = match_path.relative_to(self.root_directory)
                    except ValueError:
                        relative_path = match_path

                    # Get file info
                    try:
                        stat_info = match_path.stat()
                        size = stat_info.st_size if is_file else None
                        modified = stat_info.st_mtime
                    except Exception:
                        size = None
                        modified = None

                    results.append(
                        {
                            "path": str(relative_path),
                            "absolute_path": str(match_path),
                            "type": "directory" if is_dir else "file",
                            "size": size,
                            "modified": modified,
                        }
                    )

                    # Check max results limit
                    if len(results) >= max_results:
                        break

                # Sort results by path
                results.sort(key=lambda x: x["path"])

                if not results:
                    return ToolExecutionResult(
                        success=True,
                        content=f"No files found matching pattern '{pattern}'",
                        display_content="No matches found",
                        metadata={
                            "pattern": pattern,
                            "base_path": str(base_path),
                            "include_dirs": include_dirs,
                            "matches_found": 0,
                        },
                    )

                # Format output
                result_lines = []
                result_lines.append(f"Found {len(results)} match(es) for pattern '{pattern}':")
                result_lines.append("")

                files_count = sum(1 for r in results if r["type"] == "file")
                dirs_count = sum(1 for r in results if r["type"] == "directory")

                if files_count > 0:
                    result_lines.append(f"Files ({files_count}):")
                    for result in results:
                        if result["type"] == "file":
                            size_info = f" ({result['size']} bytes)" if result["size"] is not None else ""
                            result_lines.append(f"  {result['path']}{size_info}")
                    result_lines.append("")

                if dirs_count > 0:
                    result_lines.append(f"Directories ({dirs_count}):")
                    result_lines.extend([f"  {result['path']}/" for result in results if result["type"] == "directory"])
                    result_lines.append("")

                result_content = "\n".join(result_lines)

                display_content = f"Found {len(results)} matches"
                if len(results) >= max_results:
                    display_content += f" (limited to {max_results})"

                return ToolExecutionResult(
                    success=True,
                    content=result_content,
                    display_content=display_content,
                    metadata={
                        "pattern": pattern,
                        "base_path": str(base_path),
                        "include_dirs": include_dirs,
                        "matches_found": len(results),
                        "files_count": files_count,
                        "dirs_count": dirs_count,
                        "results_limited": len(results) >= max_results,
                        "matches": results,
                    },
                )

            except Exception as e:
                return ToolExecutionResult(
                    success=False,
                    content=f"Error: Glob search failed: {e!s}",
                    metadata={"error": "glob_failed", "exception": str(e)},
                )

        except Exception as e:
            logger.error(f"Glob tool execution failed: {e}")
            return ToolExecutionResult(
                success=False,
                content=f"Error: Glob operation failed: {e!s}",
                metadata={"error": "execution_failed", "exception": str(e)},
            )
