from typing import Any


class Tool:
    """
    A base class for all tools that can be used by the language model.
    """

    def __init__(self, name: str, display_name: str, description: str):
        """
        Initializes a new instance of the Tool class.

        Args:
            name: The name of the tool.
            display_name: The display name of the tool.
            description: A description of what the tool does.
            schema: The schema for the tool's parameters.
        """
        self.name = name
        self.display_name = display_name
        self.description = description

    @property
    def schema(self) -> dict[str, Any]:
        """
        Returns the schema for the tool's parameters.
        """
        raise NotImplementedError("Subclasses must implement the schema property.")

    async def execute(self, args: dict[str, Any], signal: Any = None) -> Any:
        """
        Executes the tool with the given arguments.

        Args:
            args: The arguments to pass to the tool.
            signal: An optional signal that can be used to cancel the operation.

        Returns:
            The result of the tool's execution.
        """
        raise NotImplementedError("Subclasses must implement the execute method.")

    async def should_confirm_execute(self, args: dict[str, Any], signal: Any = None) -> dict[str, Any] | None:
        """
        Determines whether the user should be prompted for confirmation before executing the tool.

        Args:
            args: The arguments to pass to the tool.
            signal: An optional signal that can be used to cancel the operation.

        Returns:
            A dictionary with confirmation details if confirmation is required, otherwise None.
        """
        return None
