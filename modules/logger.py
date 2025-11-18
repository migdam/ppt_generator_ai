"""
Logging Configuration Module
Provides centralized logging setup for the application.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class LoggerSetup:
    """Centralized logging configuration."""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerSetup, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not LoggerSetup._initialized:
            self.log_dir = Path("logs")
            self.log_dir.mkdir(exist_ok=True)
            LoggerSetup._initialized = True

    def setup_logger(
        self,
        name: str,
        level: int = logging.INFO,
        log_to_file: bool = True,
        log_to_console: bool = True
    ) -> logging.Logger:
        """
        Set up a logger with file and console handlers.

        Args:
            name: Logger name
            level: Logging level
            log_to_file: Whether to log to file
            log_to_console: Whether to log to console

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Clear existing handlers
        logger.handlers.clear()

        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )

        # File handler
        if log_to_file:
            timestamp = datetime.now().strftime("%Y%m%d")
            log_file = self.log_dir / f"ppt_generator_{timestamp}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)

        # Console handler
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

        return logger

    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger."""
        return logging.getLogger(name)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Convenience function to get a configured logger.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger
    """
    setup = LoggerSetup()
    return setup.setup_logger(name, level)
