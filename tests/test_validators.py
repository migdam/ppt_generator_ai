"""
Tests for input validation module.
"""

import pytest
from modules.validators import InputValidator, ValidationError


class TestURLValidation:
    """Test URL validation."""

    def test_valid_http_url(self):
        is_valid, msg = InputValidator.validate_url("http://example.com")
        assert is_valid
        assert msg == ""

    def test_valid_https_url(self):
        is_valid, msg = InputValidator.validate_url("https://example.com/path")
        assert is_valid
        assert msg == ""

    def test_empty_url(self):
        is_valid, msg = InputValidator.validate_url("")
        assert not is_valid
        assert "empty" in msg.lower()

    def test_invalid_scheme(self):
        is_valid, msg = InputValidator.validate_url("ftp://example.com")
        assert not is_valid
        assert "scheme" in msg.lower()

    def test_too_long_url(self):
        long_url = "https://example.com/" + "a" * 3000
        is_valid, msg = InputValidator.validate_url(long_url)
        assert not is_valid
        assert "too long" in msg.lower()

    def test_path_traversal(self):
        is_valid, msg = InputValidator.validate_url("https://example.com/../etc/passwd")
        assert not is_valid
        assert "suspicious" in msg.lower()


class TestFilePathValidation:
    """Test file path validation."""

    def test_path_traversal_attack(self):
        is_valid, msg, path = InputValidator.validate_file_path(
            "../etc/passwd",
            base_dir="Input"
        )
        assert not is_valid
        assert "traversal" in msg.lower()

    def test_absolute_path_rejected(self):
        is_valid, msg, path = InputValidator.validate_file_path(
            "/etc/passwd",
            base_dir="Input"
        )
        assert not is_valid

    def test_empty_filepath(self):
        is_valid, msg, path = InputValidator.validate_file_path("", base_dir="Input")
        assert not is_valid
        assert "empty" in msg.lower()

    def test_dangerous_extension(self):
        is_valid, msg, path = InputValidator.validate_file_path(
            "script.exe",
            base_dir="Input",
            must_exist=False
        )
        assert not is_valid
        assert "dangerous" in msg.lower()


class TestSlideCountValidation:
    """Test slide count validation."""

    def test_valid_auto(self):
        is_valid, msg, count = InputValidator.validate_slide_count("auto")
        assert is_valid
        assert count is None

    def test_valid_integer(self):
        is_valid, msg, count = InputValidator.validate_slide_count("10")
        assert is_valid
        assert count == 10

    def test_too_small(self):
        is_valid, msg, count = InputValidator.validate_slide_count("1")
        assert not is_valid
        assert "at least 2" in msg.lower()

    def test_too_large(self):
        is_valid, msg, count = InputValidator.validate_slide_count("100")
        assert not is_valid
        assert "cannot exceed" in msg.lower()

    def test_invalid_value(self):
        is_valid, msg, count = InputValidator.validate_slide_count("abc")
        assert not is_valid


class TestStyleValidation:
    """Test presentation style validation."""

    def test_valid_general(self):
        is_valid, msg = InputValidator.validate_style("general")
        assert is_valid

    def test_valid_detailed(self):
        is_valid, msg = InputValidator.validate_style("detailed")
        assert is_valid

    def test_invalid_style(self):
        is_valid, msg = InputValidator.validate_style("invalid")
        assert not is_valid
        assert "must be one of" in msg.lower()

    def test_empty_style(self):
        is_valid, msg = InputValidator.validate_style("")
        assert not is_valid


class TestAPIKeyValidation:
    """Test API key validation."""

    def test_valid_key(self):
        is_valid, msg = InputValidator.validate_api_key("AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI")
        assert is_valid

    def test_empty_key(self):
        is_valid, msg = InputValidator.validate_api_key("")
        assert not is_valid
        assert "required" in msg.lower()

    def test_too_short(self):
        is_valid, msg = InputValidator.validate_api_key("short")
        assert not is_valid
        assert "too short" in msg.lower()

    def test_placeholder_value(self):
        is_valid, msg = InputValidator.validate_api_key("your-api-key-here")
        assert not is_valid
        assert "placeholder" in msg.lower()


class TestFilenameSanitization:
    """Test filename sanitization."""

    def test_remove_path_separators(self):
        result = InputValidator.sanitize_filename("path/to/file.txt")
        assert "/" not in result
        assert "\\" not in result

    def test_remove_dangerous_chars(self):
        result = InputValidator.sanitize_filename("file<>:|?*.txt")
        assert not any(c in result for c in '<>:|?*')

    def test_limit_length(self):
        long_name = "a" * 300 + ".txt"
        result = InputValidator.sanitize_filename(long_name)
        assert len(result) <= 255
