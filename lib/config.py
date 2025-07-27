import uuid
from dataclasses import dataclass, field


@dataclass
class Config:
    """
    A class to hold the configuration for the LLM Coder application.
    """

    session_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    model: str = field(default="gpt-4.1")
    provider: str = field(default="azure")
    debug_mode: bool = field(default=False)
    core_tools: list[str] = field(default_factory=list)
    exclude_tools: list[str] = field(default_factory=list)
    approval_mode: str = field(default="default")
    log_directory: str = field(default="")
    debug: bool = field(default=False)
