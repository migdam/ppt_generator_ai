"""
Content Extractor Module
Handles HTML parsing and content extraction from URLs and local files.
Production version with logging, retry logic, and validation.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Tuple, List
from pathlib import Path

from modules.logger import get_logger
from modules.config import get_config
from modules.retry import retry_with_backoff
from modules.validators import InputValidator

logger = get_logger(__name__)


class ContentExtractor:
    """Extracts clean text and images from HTML sources."""

    def __init__(self):
        self.config = get_config()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        logger.info("ContentExtractor initialized")

    @retry_with_backoff(max_retries=3, base_delay=2.0, exceptions=(requests.RequestException,))
    def extract_from_url(self, url: str) -> Tuple[str, List[str], str]:
        """
        Extract content from a web URL with retry logic.

        Args:
            url: The URL to fetch content from

        Returns:
            Tuple of (clean_text, image_urls, page_title)

        Raises:
            ValueError: If URL is invalid
            requests.RequestException: If fetch fails after retries
        """
        # Validate URL
        is_valid, error_msg = InputValidator.validate_url(url)
        if not is_valid:
            logger.error(f"Invalid URL: {error_msg}")
            raise ValueError(f"Invalid URL: {error_msg}")

        logger.info(f"Fetching content from URL: {url[:100]}...")

        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.config.request_timeout,
                allow_redirects=True
            )
            response.raise_for_status()

            logger.info(f"Successfully fetched {len(response.text)} bytes from {url}")

            html_content = response.text
            return self._parse_html(html_content, base_url=url)

        except requests.Timeout:
            logger.error(f"Request timeout after {self.config.request_timeout}s")
            raise requests.RequestException(f"Request timed out after {self.config.request_timeout} seconds")

        except requests.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code}: {str(e)}")
            raise

        except requests.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise

    def extract_from_file(self, filepath: str) -> Tuple[str, List[str], str]:
        """
        Extract content from a local HTML file.

        Args:
            filepath: Path to the HTML file (relative to Input directory)

        Returns:
            Tuple of (clean_text, image_urls, page_title)

        Raises:
            ValueError: If file path is invalid
            FileNotFoundError: If file doesn't exist
        """
        # Validate file path
        is_valid, error_msg, full_path = InputValidator.validate_file_path(
            filepath,
            base_dir=self.config.input_dir,
            must_exist=True
        )

        if not is_valid:
            logger.error(f"Invalid file path: {error_msg}")
            raise ValueError(f"Invalid file path: {error_msg}")

        logger.info(f"Reading content from file: {full_path}")

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            logger.info(f"Successfully read {len(html_content)} bytes from {full_path}")

            return self._parse_html(html_content, base_url=None)

        except UnicodeDecodeError as e:
            logger.error(f"File encoding error: {str(e)}")
            raise ValueError(f"File encoding error. Please ensure file is UTF-8 encoded.")

        except Exception as e:
            logger.error(f"Failed to read file: {str(e)}")
            raise

    def _parse_html(self, html_content: str, base_url: str = None) -> Tuple[str, List[str], str]:
        """
        Parse HTML content and extract text, images, and title.

        Args:
            html_content: Raw HTML string
            base_url: Base URL for resolving relative URLs (optional)

        Returns:
            Tuple of (clean_text, image_urls, page_title)
        """
        logger.debug("Parsing HTML content...")

        try:
            soup = BeautifulSoup(html_content, 'lxml')
        except Exception as e:
            logger.warning(f"lxml parser failed, falling back to html.parser: {e}")
            soup = BeautifulSoup(html_content, 'html.parser')

        # Extract title
        title_tag = soup.find('title')
        page_title = title_tag.get_text().strip() if title_tag else "Untitled Presentation"
        logger.info(f"Extracted title: {page_title}")

        # Remove script and style elements
        removed_count = 0
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
            removed_count += 1

        logger.debug(f"Removed {removed_count} non-content elements")

        # Extract text
        text = soup.get_text(separator=' ', strip=True)
        # Clean up whitespace
        clean_text = ' '.join(text.split())

        word_count = len(clean_text.split())
        logger.info(f"Extracted {word_count} words of text content")

        # Extract images
        image_urls = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                # Resolve relative URLs
                if base_url:
                    absolute_url = urljoin(base_url, src)
                    # Validate and filter URLs
                    if absolute_url.startswith(('http://', 'https://')):
                        # Basic validation
                        if self._is_valid_image_url(absolute_url):
                            image_urls.append(absolute_url)
                elif src.startswith(('http://', 'https://')):
                    if self._is_valid_image_url(src):
                        image_urls.append(src)

        # Remove duplicates while preserving order
        image_urls = list(dict.fromkeys(image_urls))

        logger.info(f"Found {len(image_urls)} valid image URLs")

        return clean_text, image_urls, page_title

    def _is_valid_image_url(self, url: str) -> bool:
        """
        Check if a URL appears to be a valid image.

        Args:
            url: The URL to check

        Returns:
            True if URL appears valid
        """
        # Skip data URLs and very long URLs
        if url.startswith('data:') or len(url) > 2048:
            return False

        # Check for common image extensions
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'}
        parsed = urlparse(url)
        path_lower = parsed.path.lower()

        # Accept if has image extension or contains image-related paths
        has_extension = any(path_lower.endswith(ext) for ext in image_extensions)
        has_image_path = any(keyword in path_lower for keyword in ['/image', '/img', '/photo'])

        return has_extension or has_image_path

    def calculate_suggested_slides(self, text: str) -> int:
        """
        Calculate suggested number of slides based on content length.

        Args:
            text: The extracted text content

        Returns:
            Suggested number of slides
        """
        word_count = len(text.split())

        logger.debug(f"Calculating slide count for {word_count} words")

        # Rough heuristic: 150-200 words per slide
        if word_count < 300:
            suggested = 3
        elif word_count < 600:
            suggested = 5
        elif word_count < 1200:
            suggested = 7
        elif word_count < 2000:
            suggested = 10
        else:
            suggested = min(
                self.config.max_slides,
                max(10, word_count // 200)
            )

        logger.info(f"Suggested {suggested} slides for {word_count} words")
        return suggested
