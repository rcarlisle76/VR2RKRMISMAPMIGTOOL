"""
Centralized logging configuration for the Ventiv to Riskonnect Migration Tool.

Provides rotating file logs and console output with separate log levels
for UI and business logic.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional


class LoggingConfig:
    """Manages application logging configuration."""

    # Log levels
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    # Default settings
    DEFAULT_LOG_LEVEL = logging.INFO
    MAX_LOG_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5

    _initialized = False
    _log_directory: Optional[Path] = None

    @classmethod
    def setup_logging(cls,
                     log_level: int = DEFAULT_LOG_LEVEL,
                     log_dir: Optional[str] = None,
                     console_output: bool = True) -> None:
        """
        Setup application logging with rotating file handler and console output.

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory for log files (default: ~/.salesforce_migration_tool/logs)
            console_output: Whether to output logs to console
        """
        if cls._initialized:
            return

        # Determine log directory
        if log_dir:
            cls._log_directory = Path(log_dir)
        else:
            home_dir = Path.home()
            cls._log_directory = home_dir / ".salesforce_migration_tool" / "logs"

        # Create log directory if it doesn't exist
        cls._log_directory.mkdir(parents=True, exist_ok=True)

        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Remove existing handlers
        root_logger.handlers.clear()

        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )

        # Create rotating file handler
        log_file = cls._log_directory / "migration_tool.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=cls.MAX_LOG_FILE_SIZE,
            backupCount=cls.BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)

        # Create console handler if requested
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)

        # Create separate error log file
        error_log_file = cls._log_directory / "errors.log"
        error_file_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=cls.MAX_LOG_FILE_SIZE,
            backupCount=cls.BACKUP_COUNT,
            encoding='utf-8'
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_file_handler)

        cls._initialized = True

        # Log initialization
        logger = cls.get_logger(__name__)
        logger.info(f"Logging initialized. Log directory: {cls._log_directory}")

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance with the specified name.

        Args:
            name: Logger name (typically __name__)

        Returns:
            Logger instance
        """
        if not cls._initialized:
            cls.setup_logging()

        return logging.getLogger(name)

    @classmethod
    def get_log_directory(cls) -> Optional[Path]:
        """
        Get the log directory path.

        Returns:
            Path to log directory or None if not initialized
        """
        return cls._log_directory


# Convenience function for getting loggers
def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return LoggingConfig.get_logger(name)
