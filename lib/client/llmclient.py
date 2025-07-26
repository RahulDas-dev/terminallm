from lib.configs import ProviderConfigs
from lib.event_system import EventManager, get_event_manager
from lib.tools import ToolRegistry, get_tool_registry


class LLMClient:
    def __init__(
        self,
        config: ProviderConfigs,
        event_manager: EventManager | None = None,
        tool_registry: ToolRegistry | None = None,
    ):
        self.config = config
        self.event_manager = event_manager or get_event_manager()
        self.tool_registry = tool_registry or get_tool_registry()
