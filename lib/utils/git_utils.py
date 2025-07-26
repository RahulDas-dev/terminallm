from pathlib import Path


def is_git_repository(path: str | Path) -> bool:
    """
    Check if a directory is a Git repository.

    Args:
        path: Directory path to check

    Returns:
        True if the directory is a Git repository
    """
    git_dir = Path(path) / ".git"
    return git_dir.exists() and (git_dir.is_dir() or git_dir.is_file())
