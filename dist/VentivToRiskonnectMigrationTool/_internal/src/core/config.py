"""
Application configuration management.

Handles loading, saving, and managing application settings and connection profiles.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict

from .logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class AppConfig:
    """Application configuration settings."""

    # Window settings
    window_width: int = 500
    window_height: int = 400
    remember_last_username: bool = True
    last_username: str = ""

    # Salesforce settings
    default_instance_url: str = "https://login.salesforce.com"
    api_version: str = "58.0"

    # Application settings
    log_level: str = "INFO"
    auto_update_check: bool = True

    # AI-enhanced mapping settings
    use_semantic_matching: bool = True  # Phase 1: Local embeddings
    use_llm_mapping: bool = False  # Phase 2: Claude API (requires API key)
    llm_provider: str = "claude"  # "claude" or "openai"
    llm_model: str = "claude-3-5-sonnet-20241022"  # Default Claude model
    claude_api_key: str = ""  # User provides their own API key
    ai_mapping_threshold: float = 0.6  # Minimum confidence for AI suggestions
    fuzzy_mapping_threshold: float = 0.7  # Higher threshold when AI is enabled


class ConfigManager:
    """Manages application configuration."""

    DEFAULT_CONFIG_DIR = Path.home() / ".salesforce_migration_tool"
    DEFAULT_CONFIG_FILE = "config.json"

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration manager.

        Args:
            config_dir: Directory for configuration files
        """
        self.config_dir = config_dir or self.DEFAULT_CONFIG_DIR
        self.config_file = self.config_dir / self.DEFAULT_CONFIG_FILE
        self.config = AppConfig()

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> AppConfig:
        """
        Load configuration from file.

        Returns:
            AppConfig instance

        Raises:
            Exception if configuration file is corrupted
        """
        if not self.config_file.exists():
            logger.info("No configuration file found, using defaults")
            return self.config

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # Update config object with loaded values
            for key, value in config_data.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

            logger.info(f"Configuration loaded from {self.config_file}")
            return self.config

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse configuration file: {e}")
            raise Exception(f"Configuration file is corrupted: {e}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise

    def save(self) -> None:
        """
        Save current configuration to file.

        Raises:
            Exception if unable to save configuration
        """
        try:
            config_dict = asdict(self.config)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2)

            logger.info(f"Configuration saved to {self.config_file}")

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise Exception(f"Failed to save configuration: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key doesn't exist

        Returns:
            Configuration value
        """
        return getattr(self.config, key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        if hasattr(self.config, key):
            setattr(self.config, key, value)
        else:
            logger.warning(f"Unknown configuration key: {key}")

    def update(self, **kwargs) -> None:
        """
        Update multiple configuration values.

        Args:
            **kwargs: Key-value pairs to update
        """
        for key, value in kwargs.items():
            self.set(key, value)

    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self.config = AppConfig()
        logger.info("Configuration reset to defaults")
