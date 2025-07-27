from pathlib import Path
from typing import Any

from lib.config import Config

from .base import Tool


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
