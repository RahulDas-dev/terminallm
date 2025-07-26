from pathlib import Path

PYTHON_FILES = ["requirements.txt", "pyproject.toml", "setup.py", "Pipfile", "environment.yml", "conda.yml"]


def has_python_files(workspace_path: Path | str) -> bool:
    """
    Check if the given workspace path contains any Python files.
    """
    return any(Path(workspace_path, file).exists() for file in PYTHON_FILES)


def is_valid_workspace(workspace_path: Path | str) -> bool:
    """
    Check if the given workspace path is valid.
    A valid workspace must contain at least one Python file.
    """
    workspace_path = Path(workspace_path)
    return workspace_path.is_dir()
