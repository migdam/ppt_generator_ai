"""
Input Validation Module
Provides validation and sanitization for user inputs.
"""

import re
from pathlib import Path
from urllib.parse import urlparse
from typing import Tuple, Optional
from modules.logger import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class InputValidator:
    """Validates and sanitizes user inputs."""

    # URL validation pattern
    URL_PATTERN = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )

    # Dangerous file extensions
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.sh', '.ps1', '.scr', '.vbs', '.js',
        '.jar', '.app', '.deb', '.rpm', '.dmg', '.pkg'
    }

    @staticmethod
    def validate_url(url: str, allowed_schemes: Optional[list] = None) -> Tuple[bool, str]:
        """
        Validate a URL.

        Args:
            url: The URL to validate
            allowed_schemes: List of allowed schemes (default: ['http', 'https'])

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url:
            return False, "URL cannot be empty"

        if len(url) > 2048:
            return False, "URL is too long (max 2048 characters)"

        # Basic pattern check
        if not InputValidator.URL_PATTERN.match(url):
            return False, "Invalid URL format"

        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            return False, f"Failed to parse URL: {str(e)}"

        # Check scheme
        if allowed_schemes is None:
            allowed_schemes = ['http', 'https']

        if parsed.scheme not in allowed_schemes:
            return False, f"URL scheme must be one of: {', '.join(allowed_schemes)}"

        # Check for suspicious patterns
        if '..' in url:
            return False, "URL contains suspicious path traversal patterns"

        logger.info(f"URL validation passed: {url[:50]}...")
        return True, ""

    @staticmethod
    def validate_file_path(
        filepath: str,
        base_dir: str = "Input",
        must_exist: bool = True
    ) -> Tuple[bool, str, Optional[Path]]:
        """
        Validate a file path.

        Args:
            filepath: The file path to validate
            base_dir: Base directory for the file
            must_exist: Whether the file must exist

        Returns:
            Tuple of (is_valid, error_message, resolved_path)
        """
        if not filepath:
            return False, "File path cannot be empty", None

        # Check for path traversal
        if '..' in filepath or filepath.startswith('/'):
            return False, "Invalid file path: path traversal detected", None

        # Resolve path
        base = Path(base_dir)
        full_path = base / filepath

        # Ensure path is within base directory
        try:
            full_path = full_path.resolve()
            base = base.resolve()
            if not str(full_path).startswith(str(base)):
                return False, "Invalid file path: outside allowed directory", None
        except Exception as e:
            return False, f"Failed to resolve path: {str(e)}", None

        # Check if file exists
        if must_exist and not full_path.exists():
            return False, f"File not found: {full_path}", None

        # Check file extension
        if full_path.suffix.lower() in InputValidator.DANGEROUS_EXTENSIONS:
            return False, f"Dangerous file extension: {full_path.suffix}", None

        # Check file size if exists
        if full_path.exists():
            size_mb = full_path.stat().st_size / (1024 * 1024)
            if size_mb > 50:  # 50 MB limit
                return False, f"File too large: {size_mb:.1f} MB (max 50 MB)", None

        logger.info(f"File path validation passed: {full_path}")
        return True, "", full_path

    @staticmethod
    def validate_slide_count(slides: str) -> Tuple[bool, str, Optional[int]]:
        """
        Validate slide count input.

        Args:
            slides: Slide count value ('auto' or integer)

        Returns:
            Tuple of (is_valid, error_message, resolved_value)
        """
        if not slides:
            return False, "Slide count cannot be empty", None

        if slides.lower() == 'auto':
            return True, "", None

        # Try to parse as integer
        try:
            count = int(slides)
        except ValueError:
            return False, "Slide count must be 'auto' or an integer", None

        # Validate range
        if count < 2:
            return False, "Slide count must be at least 2", None

        if count > 50:
            return False, "Slide count cannot exceed 50", None

        logger.info(f"Slide count validation passed: {count}")
        return True, "", count

    @staticmethod
    def validate_style(style: str) -> Tuple[bool, str]:
        """
        Validate presentation style.

        Args:
            style: Style value

        Returns:
            Tuple of (is_valid, error_message)
        """
        allowed_styles = ['general', 'detailed']

        if not style:
            return False, "Style cannot be empty"

        if style.lower() not in allowed_styles:
            return False, f"Style must be one of: {', '.join(allowed_styles)}"

        return True, ""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize a filename.

        Args:
            filename: The filename to sanitize

        Returns:
            Sanitized filename
        """
        # Remove path separators
        filename = filename.replace('/', '_').replace('\\', '_')

        # Remove or replace dangerous characters
        filename = re.sub(r'[<>:"|?*]', '', filename)

        # Remove control characters
        filename = ''.join(char for char in filename if ord(char) >= 32)

        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            if ext:
                filename = name[:250] + '.' + ext
            else:
                filename = filename[:255]

        return filename

    @staticmethod
    def validate_api_key(api_key: Optional[str]) -> Tuple[bool, str]:
        """
        Validate API key format.

        Args:
            api_key: The API key to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not api_key:
            return False, "API key is required"

        if len(api_key) < 20:
            return False, "API key appears to be invalid (too short)"

        # Check for placeholder values
        placeholders = ['your-api-key', 'api-key-here', 'your_key', 'xxx']
        if any(placeholder in api_key.lower() for placeholder in placeholders):
            return False, "API key appears to be a placeholder value"

        return True, ""
