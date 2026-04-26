"""Application settings and environment configuration."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env file with override=True
load_dotenv(override=True)


# Model-specific default parameters. Add new models here.
MODEL_PRESETS: dict[str, dict] = {
    "kimi-k2.5": {
        "base_url": "https://api.moonshot.cn/v1",
        "temperature": 0.6,
        "model_kwargs": {},
        "extra_body": {"thinking": {"type": "disabled"}},
    },
    "deepseek-v4-flash": {
        "base_url": "https://api.deepseek.com/v1",
        "temperature": 0.7,
        "model_kwargs": {},
        "extra_body": {},
    },
}


def _get_preset(model_name: str) -> dict:
    """Get preset for a model, falling back to kimi-k2.5 if unknown."""
    return MODEL_PRESETS.get(model_name, MODEL_PRESETS["kimi-k2.5"])


@dataclass(frozen=True)
class LLMSettings:
    """LLM provider configuration."""

    api_key: str
    base_url: str
    model: str
    temperature: float
    model_kwargs: dict
    extra_body: dict

    @classmethod
    def from_env(cls) -> "LLMSettings":
        """Create settings from environment variables."""
        model = os.getenv("OPENAI_MODEL", "kimi-k2.5")
        preset = _get_preset(model)
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            base_url=preset["base_url"],
            model=model,
            temperature=preset["temperature"],
            model_kwargs=preset["model_kwargs"],
            extra_body=preset["extra_body"],
        )

    def validate(self) -> None:
        """Validate required settings."""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required")


@dataclass(frozen=True)
class LightLLMSettings:
    """Lightweight LLM provider configuration (OpenAI-compatible)."""

    api_key: str
    base_url: str
    model: str
    temperature: float
    model_kwargs: dict
    extra_body: dict

    @classmethod
    def from_env(cls) -> "LightLLMSettings":
        """Create settings from environment variables."""
        model = os.getenv("OPENAI_LIGHT_MODEL", "kimi-k2.5")
        preset = _get_preset(model)
        return cls(
            api_key=os.getenv("OPENAI_LIGHT_API_KEY") or os.getenv("OPENAI_API_KEY", ""),
            base_url=preset["base_url"],
            model=model,
            temperature=preset["temperature"],
            model_kwargs=preset["model_kwargs"],
            extra_body=preset["extra_body"],
        )

    def validate(self) -> None:
        """Validate required settings."""
        if not self.api_key:
            raise ValueError("OPENAI_LIGHT_API_KEY (or fallback OPENAI_API_KEY) is required")


@dataclass(frozen=True)
class ServerSettings:
    """Server configuration."""

    host: str
    port: int
    log_level: str

    @classmethod
    def from_env(cls) -> "ServerSettings":
        """Create settings from environment variables."""
        return cls(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            log_level=os.getenv("LOG_LEVEL", "info"),
        )


@dataclass(frozen=True)
class SearchSettings:
    """Search tool configuration."""

    server_url: str
    tool_name: str
    auth_token: str | None
    auth_header: str
    result_count: int

    @classmethod
    def from_env(cls) -> "SearchSettings":
        """Create settings from environment variables."""
        auth_token = os.getenv("MCP_SEARCH_AUTH_TOKEN")
        # Allow empty string to be treated as None
        if auth_token == "":
            auth_token = None

        return cls(
            server_url=os.getenv("MCP_SEARCH_URL", "http://localhost:3000"),
            tool_name=os.getenv("MCP_SEARCH_TOOL", "bailian_web_search"),
            auth_token=auth_token,
            auth_header=os.getenv("MCP_SEARCH_AUTH_HEADER", "Authorization"),
            result_count=int(os.getenv("MCP_SEARCH_RESULT_COUNT", "10")),
        )


class Settings:
    """Application settings container."""

    def __init__(self) -> None:
        self.llm = LLMSettings.from_env()
        self.llm_light = LightLLMSettings.from_env()
        self.server = ServerSettings.from_env()
        self.search = SearchSettings.from_env()
        self.project_root = Path(__file__).parent.parent.parent.parent

        # Validate
        self.llm.validate()
        self.llm_light.validate()


# Global settings singleton
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    load_dotenv(override=True)
    _settings = Settings()
    return _settings