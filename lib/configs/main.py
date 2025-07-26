from pydantic_settings import SettingsConfigDict

from .extra_conf import ExtraConfig
from .log_conf import LogConfig
from .provider_conf import ProviderConfigs
from .tools_config import ToolsConfig


class AppConfig(LogConfig, ProviderConfigs, ExtraConfig, ToolsConfig):
    model_config = SettingsConfigDict(
        frozen=True,
        env_nested_delimiter="__",
        env_file=".config",
        env_file_encoding="utf-8",
        extra="ignore",
    )
