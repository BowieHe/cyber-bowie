"""Application settings and environment configuration."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env file with override=True
load_dotenv(override=True)


@dataclass(frozen=True)
class LLMSettings:
    """LLM provider configuration."""

    api_key: str
    base_url: str
    model: str
    temperature: float

    @classmethod
    def from_env(cls) -> "LLMSettings":
        """Create settings from environment variables."""
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.moonshot.cn/v1"),
            model=os.getenv("OPENAI_MODEL", "kimi-k2.5"),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "1")),
        )

    def validate(self) -> None:
        """Validate required settings."""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required")


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


class Settings:
    """Application settings container."""

    def __init__(self) -> None:
        self.llm = LLMSettings.from_env()
        self.server = ServerSettings.from_env()
        self.project_root = Path(__file__).parent.parent.parent.parent

        # Validate
        self.llm.validate()


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