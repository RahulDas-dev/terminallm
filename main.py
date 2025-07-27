import argparse
import asyncio
import sys
from pathlib import Path

from src import CoderAgent


def _get_args() -> argparse.Namespace:
    """
    Parses and validates command-line arguments.
    """
    parser = argparse.ArgumentParser(description="LLM CLI")
    parser.add_argument("--task", help="Task to perform with the LLM")
    parser.add_argument("--target-dir", default=Path.cwd(), help="Target directory for operations")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        choices=[
            "gpt-4.1",
            "gpt-4o",
            "gemini-1.5",
            "gemini-2.0",
            "deepseek-r1",
            "claude-3-7-sonnet",
        ],
        help="Model to use",
    )
    parser.add_argument(
        "--provider",
        default="openai",
        help="Provider to use (azure, aws, vertex_ai)",
        choices=["openai", "azure", "vertex_ai", "bedrock"],
    )
    parser.add_argument("--yolo", action="store_true", help="Execute tools without confirmation")
    args = parser.parse_args()

    # Validate target directory
    target_path = Path(args.target_dir)
    if not target_path.is_dir():
        sys.exit(1)

    return args


async def main() -> str | None:
    """
    Main function for the LLM CLI application. Parses command-line arguments,
    initializes the CLI, and runs in either interactive or non-interactive mode.
    """
    args = _get_args()
    target_dir = "D:/python/doc-inference"
    task = args.task

    # Get the appropriate model name using the helper function

    config = {
        "model": args.model,
        "provider": args.provider,
        "debug_mode": args.debug,
        "approval_mode": "yolo" if args.yolo else "default",
        "core_tools": ["list_directory", "read_file", "write_file", "glob", "run_shell_command"],
        "debug": args.debug,
    }

    agent = CoderAgent(target_dir, config)
    await agent.initialize()

    if task:
        response = await agent.run_non_interactive(task)
    else:
        response = await agent.run_interactive()
    return response


if __name__ == "__main__":
    asyncio.run(main())
