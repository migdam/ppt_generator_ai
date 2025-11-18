"""
Tests for configuration management module.
"""

import pytest
import os
from modules.config import AppConfig, ConfigManager, get_config


class TestAppConfig:
    """Test AppConfig dataclass."""

    def test_default_values(self):
        config = AppConfig()
        assert config.gemini_model == "gemini-1.5-flash"
        assert config.quality_threshold == 45
        assert config.max_quality_attempts == 5
        assert config.default_style == "general"

    def test_custom_values(self):
        config = AppConfig(
            quality_threshold=40,
            max_retries=3
        )
        assert config.quality_threshold == 40
        assert config.max_retries == 3


class TestConfigManager:
    """Test ConfigManager singleton."""

    def test_singleton_pattern(self):
        manager1 = ConfigManager()
        manager2 = ConfigManager()
        assert manager1 is manager2

    def test_get_config(self):
        config = get_config()
        assert isinstance(config, AppConfig)

    def test_environment_override(self):
        # Set environment variable
        os.environ['QUALITY_THRESHOLD'] = '40'

        # Create new manager (this will load from env)
        manager = ConfigManager()
        manager._config = manager._load_config()

        assert manager.config.quality_threshold == 40

        # Cleanup
        del os.environ['QUALITY_THRESHOLD']
