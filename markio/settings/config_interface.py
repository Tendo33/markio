from typing import Optional

import dotenv
from pydantic_settings import BaseSettings

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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        populate_by_name = True

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
                logger.info(f"Settings loaded successfully: {cls._instance}")
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
