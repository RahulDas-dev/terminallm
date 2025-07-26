from pydantic import Field
from pydantic_settings import BaseSettings


class ModelConfig(BaseSettings):
    """
    Configuration for model settings.
    This class is used to manage model-specific configurations.
    """

    MODEL_NAME: str = Field(description="Name of the model", default="")
    API_KEY: str = Field(description="API key for the model", default="")
    API_ENDPOINT: str = Field(description="API endpoint for the model", default="")
    API_VERSION: str = Field(description="API version for the model", default="")


class ProviderConfig(BaseSettings):
    """
    Configuration for provider settings.
    This class is used to manage provider-specific configurations.
    """

    PROVIDER_NAME: str = Field(description="Name of the provider", default="")
    MODELCONFIG: list[ModelConfig]


class ProviderConfigs(BaseSettings):
    DEFAULT_MODEL: str = "default_model"
    PROVIDERS: list[ProviderConfig] = []
