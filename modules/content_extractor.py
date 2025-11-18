"""
Content Extractor Module
Handles HTML parsing and content extraction from URLs and local files.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Tuple, List
import os


class ContentExtractor:
    """Extracts clean text and images from HTML sources."""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def extract_from_url(self, url: str) -> Tuple[str, List[str], str]:
        """
        Extract content from a web URL.

        Args:
            url: The URL to fetch content from

        Returns:
            Tuple of (clean_text, image_urls, page_title)
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            html_content = response.text
            return self._parse_html(html_content, base_url=url)
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch URL: {str(e)}")

    def extract_from_file(self, filepath: str) -> Tuple[str, List[str], str]:
        """
        Extract content from a local HTML file.

        Args:
            filepath: Path to the HTML file

        Returns:
            Tuple of (clean_text, image_urls, page_title)
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()
            return self._parse_html(html_content, base_url=None)
        except Exception as e:
            raise Exception(f"Failed to read file: {str(e)}")

    def _parse_html(self, html_content: str, base_url: str = None) -> Tuple[str, List[str], str]:
        """
        Parse HTML content and extract text, images, and title.

        Args:
            html_content: Raw HTML string
            base_url: Base URL for resolving relative URLs (optional)

        Returns:
            Tuple of (clean_text, image_urls, page_title)
        """
        soup = BeautifulSoup(html_content, 'lxml')

        # Extract title
        title_tag = soup.find('title')
        page_title = title_tag.get_text().strip() if title_tag else "Untitled Presentation"

        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()

        # Extract text
        text = soup.get_text(separator=' ', strip=True)
        # Clean up whitespace
        clean_text = ' '.join(text.split())

        # Extract images
        image_urls = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                # Resolve relative URLs
                if base_url:
                    absolute_url = urljoin(base_url, src)
                    # Only include http/https URLs
                    if absolute_url.startswith(('http://', 'https://')):
                        image_urls.append(absolute_url)
                elif src.startswith(('http://', 'https://')):
                    image_urls.append(src)

        # Remove duplicates while preserving order
        image_urls = list(dict.fromkeys(image_urls))

        return clean_text, image_urls, page_title

    def calculate_suggested_slides(self, text: str) -> int:
        """
        Calculate suggested number of slides based on content length.

        Args:
            text: The extracted text content

        Returns:
            Suggested number of slides
        """
        word_count = len(text.split())

        # Rough heuristic: 150-200 words per slide
        if word_count < 300:
            return 3
        elif word_count < 600:
            return 5
        elif word_count < 1200:
            return 7
        elif word_count < 2000:
            return 10
        else:
            return min(15, max(10, word_count // 200))
