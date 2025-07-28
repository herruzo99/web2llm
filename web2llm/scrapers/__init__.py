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


def get_scraper(source: str, config: dict) -> BaseScraper | None:
    """Selects the appropriate scraper class for a given source (URL or local path)."""

    # Check if it's a local path first.
    source_path = os.path.expanduser(source)
    if os.path.exists(source_path):
        if os.path.isdir(source_path):
            return LocalFolderScraper(source_path, config)
        elif source_path.lower().endswith(".pdf"):
            return PDFScraper(source_path)
        else:
            # We could eventually support scraping local files other than PDFs here.
            raise ValueError(f"Unsupported local file type: {source_path}")

    # If not a local path, treat it as a URL.
    parsed_url = urlparse(source)
    if not all([parsed_url.scheme, parsed_url.netloc]):
        raise ValueError(f"Invalid URL or non-existent local path: {source}")

    if "github.com" in parsed_url.netloc:
        return GitHubScraper(source, config)

    # For other URLs, check the content-type to see if it's a PDF.
    content_type = get_url_content_type(source)
    if content_type and "application/pdf" in content_type:
        return PDFScraper(source)

    # Default to the generic HTML scraper.
    return GenericScraper(source, config)
