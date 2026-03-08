from typing import Optional

import dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

from markio.utils.logger_config import get_logger

from .config_model import ApplicationConfig

# Load environment variables from .env file
dotenv.load_dotenv()

logger = get_logger(__name__)


class Settings(ApplicationConfig, BaseSettings):
    """
    Application settings class with environment variable support.

    Inherits from ApplicationConfig for configuration fields and uses
    pydantic-settings for configuration management and validation.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
    )

    _instance: Optional["Settings"] = None

    @classmethod
    def get_instance(cls) -> "Settings":
        """
        Get the unique Settings instance with environment variable support.

        Returns:
            Settings: Unique Settings instance
        """
        if cls._instance is None:
            try:
                cls._instance = cls()
                secret = (cls._instance.auth_jwt_secret or "").strip()
                if not secret:
                    raise ValueError(
                        "AUTH_JWT_SECRET is required because all /v1 endpoints enforce JWT auth"
                    )
                algorithm = (cls._instance.auth_jwt_algorithm or "HS256").strip().upper()
                if algorithm != "HS256":
                    raise ValueError("AUTH_JWT_ALGORITHM must be HS256")
                logger.info(
                    "Settings loaded successfully (redis_enabled={}, task_backend={}, mcp={}, log_level={})",
                    cls._instance.redis_enabled,
                    cls._instance.task_queue_backend,
                    cls._instance.enable_mcp,
                    cls._instance.log_level,
                )
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
                raise
        else:
            logger.info("Using existing Settings instance")

        return cls._instance

    @classmethod
    def reload(cls) -> "Settings":
        """
        Reload configuration by clearing existing instance and recreating.

        Returns:
            Settings: New Settings instance
        """
        cls._instance = None
        return cls.get_instance()


# Initialize global configuration instance
Settings._instance = None
settings = Settings.get_instance()
logger.info("Configuration file loading completed")
