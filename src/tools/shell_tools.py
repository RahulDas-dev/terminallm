import asyncio
from string import Template
from typing import Any

from src.config import Config

from .base import Tool

SHELL_RESPONSE_TEXT = """Command failed with exit code ${process.returncode}

STDOUT:
${output}

STDERR:
${error}"""


class ShellTool(Tool):
    """
    A tool for running shell commands.
    """

    def __init__(self, config: Config):
        """
        Initializes the ShellTool.

        Args:
            config: The configuration object.
        """
        super().__init__(name="run_shell_command", display_name="Shell", description="Runs a shell command")
        self.config = config

    @property
    def schema(self) -> dict[str, Any]:
        """
        Returns the schema for the shell tool's parameters.
        """
        return {
            "name": self.name,
            "description": "Execute a shell command",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command to execute",
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of what this command does",
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Timeout in milliseconds",
                    },
                },
                "required": ["command"],
            },
        }

    async def should_confirm_execute(self, args: dict[str, Any], signal: Any = None) -> dict[str, Any]:
        """
        Asks for confirmation before executing a shell command.

        Args:
            args: The arguments for the command.
            signal: An optional signal to cancel the operation.

        Returns:
            A dictionary with the confirmation details.
        """
        return {
            "type": "shell",
            "command": args["command"],
            "message": f"Run shell command: {args['command']}?",
        }

    async def execute(self, args: dict[str, Any], signal: Any = None) -> dict[str, Any]:
        """
        Executes the shell command.

        Args:
            args: The arguments for the command.
            signal: An optional signal to cancel the operation.

        Returns:
            A dictionary with the result of the command.
        """
        command = args["command"]
        timeout_ms = args.get("timeout", 120000)  # Default 2 minutes
        timeout_sec = timeout_ms / 1000
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_sec)
            except asyncio.TimeoutError:
                process.kill()
                raise Exception(f"Command timed out after {timeout_sec} seconds") from None
            output = stdout.decode("utf-8", errors="replace")
            error = stderr.decode("utf-8", errors="replace")
            if process.returncode != 0:
                result = Template(SHELL_RESPONSE_TEXT).substitute(process=process, output=output, error=error)
                return {"llm_content": result, "return_display": result}
            result_text = output if output else "(Command completed with no output)"
            return {
                "llm_content": result_text,
                "return_display": f"""Command executed successfully:\n{result_text}""",
            }

        except Exception as e:
            raise Exception(f"Error executing command: {e!s}") from e
