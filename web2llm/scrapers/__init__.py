"""
Scraper Factory: selects the correct scraping strategy for a given source.
"""

import os
from urllib.parse import urlparse

from ..utils import get_url_content_type
from .base_scraper import BaseScraper
from .generic_scraper import GenericScraper
from .github_scraper import GitHubScraper
from .local_folder_scraper import LocalFolderScraper
from .pdf_scraper import PDFScraper


async def get_scraper(source: str, config: dict) -> BaseScraper | None:
    """
    Selects the appropriate scraper class for a given source (URL or local path).
    It uses fast, local checks by default and performs an optional network check for edge cases.
    """

    # 1. Check if it's a local path first.
    source_path = os.path.expanduser(source)
    if os.path.exists(source_path):
        if os.path.isdir(source_path):
            return LocalFolderScraper(source_path, config)
        elif source_path.lower().endswith(".pdf"):
            return PDFScraper(source_path, config)
        else:
            raise ValueError(f"Unsupported local file type: {source_path}")

    # 2. If not a local path, treat it as a URL.
    parsed_url = urlparse(source)
    if not all([parsed_url.scheme, parsed_url.netloc]):
        raise ValueError(f"Invalid URL or non-existent local path: {source}")

    # 3. Check for specific URL patterns.
    if "github.com" in parsed_url.netloc:
        return GitHubScraper(source, config)

    # 4. Perform scraper selection for general URLs.
    # Fast path: check for .pdf extension first. This covers the majority of cases.
    if parsed_url.path.lower().endswith(".pdf"):
        return PDFScraper(source, config)

    # Slow path (user-opt-in): make a network request to check Content-Type for edge cases
    # like `https://example.com/get-report?id=123`
    if config.get("check_content_type"):
        content_type = await get_url_content_type(source, debug=config.get("debug", False))
        if content_type and "application/pdf" in content_type:
            return PDFScraper(source, config)

    # 5. Default to the generic HTML scraper for all other valid URLs.
    return GenericScraper(source, config)
