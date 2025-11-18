"""
Configuration Management Module
Handles application configuration from environment variables and config files.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict


@dataclass
class AppConfig:
    """Application configuration."""

    # API Configuration
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-flash"

    # Quality Control
    quality_threshold: int = 45
    max_quality_attempts: int = 5
    max_quality_score: int = 50

    # Request Configuration
    request_timeout: int = 30
    image_download_timeout: int = 10
    max_retries: int = 4
    retry_backoff_base: float = 2.0

    # Content Processing
    max_content_length: int = 8000
    max_images_in_prompt: int = 10

    # Output Configuration
    output_dir: str = "Output"
    input_dir: str = "Input"
    log_dir: str = "logs"

    # Presentation Defaults
    default_slide_count: str = "auto"
    default_style: str = "general"
    min_slides: int = 2
    max_slides: int = 20

    # Rate Limiting
    api_calls_per_minute: int = 60
    rate_limit_enabled: bool = True

    # Cache Configuration
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 hour

    # Security
    validate_urls: bool = True
    allowed_url_schemes: list = field(default_factory=lambda: ['http', 'https'])
    max_file_size_mb: int = 50

    # Performance
    parallel_image_downloads: bool = True
    max_concurrent_downloads: int = 5


class ConfigManager:
    """Manages application configuration."""

    _instance = None
    _config: Optional[AppConfig] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._config = self._load_config()

    def _load_config(self) -> AppConfig:
        """Load configuration from environment and config file."""
        config = AppConfig()

        # Load from environment variables
        config.gemini_api_key = self._get_api_key()
        config.gemini_model = os.getenv('GEMINI_MODEL', config.gemini_model)

        # Load numeric configs
        config.quality_threshold = int(os.getenv('QUALITY_THRESHOLD', config.quality_threshold))
        config.max_quality_attempts = int(os.getenv('MAX_QUALITY_ATTEMPTS', config.max_quality_attempts))
        config.request_timeout = int(os.getenv('REQUEST_TIMEOUT', config.request_timeout))
        config.max_retries = int(os.getenv('MAX_RETRIES', config.max_retries))

        # Load directories
        config.output_dir = os.getenv('OUTPUT_DIR', config.output_dir)
        config.input_dir = os.getenv('INPUT_DIR', config.input_dir)
        config.log_dir = os.getenv('LOG_DIR', config.log_dir)

        # Load boolean configs
        config.rate_limit_enabled = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
        config.cache_enabled = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
        config.validate_urls = os.getenv('VALIDATE_URLS', 'true').lower() == 'true'

        # Load from config file if exists
        config_file = Path('config.json')
        if config_file.exists():
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                for key, value in file_config.items():
                    if hasattr(config, key):
                        setattr(config, key, value)

        return config

    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment or shell config."""
        # First check environment variable
        api_key = os.environ.get('GEMINI_API_KEY')

        if not api_key:
            # Try to read from ~/.zshrc or ~/.bashrc
            for rc_file in ['~/.zshrc', '~/.bashrc']:
                rc_path = Path(rc_file).expanduser()
                if rc_path.exists():
                    try:
                        with open(rc_path, 'r') as f:
                            for line in f:
                                if 'GEMINI_API_KEY' in line and '=' in line:
                                    parts = line.split('=', 1)
                                    if len(parts) == 2:
                                        key = parts[1].strip().strip('"').strip("'")
                                        if key and not key.startswith('export'):
                                            return key
                    except Exception:
                        pass

        return api_key

    @property
    def config(self) -> AppConfig:
        """Get the current configuration."""
        return self._config

    def save_config(self, filepath: str = 'config.json') -> None:
        """Save current configuration to file."""
        config_dict = asdict(self._config)
        # Don't save API key to file
        config_dict.pop('gemini_api_key', None)

        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2)

    def update_config(self, **kwargs) -> None:
        """Update configuration values."""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)


def get_config() -> AppConfig:
    """Get the application configuration."""
    manager = ConfigManager()
    return manager.config
