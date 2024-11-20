from pathlib import Path
from typing import Annotated, Optional

from pathspec import PathSpec, patterns


def list_files(directory: Annotated[str, "The directory to list files from"]) -> str:
    """
    List all files in the specified directory and its subdirectories, returning their absolute paths,
    respecting the .gitignore.

    Args:
    directory (str): The path to the directory.

    Returns:
    str: A list of absolute file paths separated by comma if the directory has files, else returns `No files found`.
    """
    path = Path(directory)
    gitignore_path = path / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            lines = f.readlines()
            lines.append(".git")
            spec = PathSpec.from_lines(pattern_factory=patterns.GitWildMatchPattern, lines=lines)
        file_list = [
            str(file.resolve())
            for file in path.rglob("*")
            if file.is_file() and not spec.match_file(str(file.relative_to(path)))
        ]
    else:
        file_list = [str(file.resolve()) for file in path.rglob("*") if file.is_file()]

    return "\n, ".join(file_list) if file_list else "No files found"


def get_absolute_path(path_str: Annotated[str, "The path string to get the absolute path for"]) -> str:
    """
    Get the absolute path of the given path string.

    Args:
    path_str (str): The path string.

    Returns:
    str: The absolute path as a string.
    """
    return str(Path(path_str)) if Path(path_str).is_absolute() else str(Path(path_str).resolve())


def find_file(
    file_name: Annotated[str, "The name of the file to find"],
    directory: Annotated[str, "The directory to search in"],
) -> str:
    """
    Find a file by name in the specified directory and its subdirectories.

    Args:
    file_name (str): The name of the file to find.
    directory (str): The path to the directory to search in.

    Returns:
    str: The absolute path of the file if found, otherwise returns `Error - File {file_name} not found in {directory}`.
    """
    path = Path(directory)
    found_results = [file.resolve() for file in path.rglob("*") if file.is_file() and file.name == file_name]
    if found_results:
        if len(found_results) == 1:
            return found_results[0]
        return f"Found Multiple files with name {file_name}" + "".join(
            f"{idx + 1}. {item}\n" for idx, item in enumerate(found_results)
        )
    return f"Error - File {file_name} not found in {directory}"


def find_directory(
    dir_name: Annotated[str, "The name of the directory to find"],
    directory: Annotated[str, "The directory to search in"],
) -> str:
    """
    Find a directory by name in the specified directory and its subdirectories.

    Args:
    dir_name (str): The name of the directory to find.
    directory (str): The path to the directory to search in.

    Returns:
    str: The absolute path of the directory if found, otherwise returns
    `Error - Directory {dir_name} not found in {directory}`.
    """
    path = Path(directory)
    found_results = []
    for d in path.rglob("*"):
        if d.is_dir() and d.name == dir_name:
            return str(d.resolve())
    if found_results:
        if len(found_results) == 1:
            return found_results[0]
        return f"Found Multiple Directories with name {dir_name}" + "".join(
            f"{idx + 1}. {item}\n" for idx, item in enumerate(found_results)
        )
    return f"Error - Directory {dir_name} not found in {directory}"


def read_file(file_path: Annotated[str, "The absolute path to the file to read"]) -> str:
    """
    Read the content of the specified file.

    Args:
    file_path (str): The absolute path to the file.

    Returns:
    str: returns the content of the file if it exists, otherwise returns `Error - {error message}`.
    """
    try:
        with open(file_path, "r") as file:
            return file.read()
    except Exception as err:
        return f"Error - {err!s}"


def get_curret_directory() -> str:
    """
    Get the current working directory.

    Returns:
    str: The current working directory as a string.
    """
    return str(Path.cwd())


def write_file(
    filename: Annotated[str, "The absolute path of the file to write to."],
    content: Annotated[str, "The content to write to the file."],
) -> Optional[str]:
    """
    Write the content to the specified file.

    Args:
    filename (str): The name of the file to write to.
    content (str): The content to write to the file.

    Returns:
    None
    """
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)
    return None
