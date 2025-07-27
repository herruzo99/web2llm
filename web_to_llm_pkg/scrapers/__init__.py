"""
Scraper Factory Module for Remote URLs.

This module contains the factory function `get_scraper_for_url` which is the
primary entry point for selecting the correct scraping strategy for a remote
URL provided by the user.

Local path handling is done in the main application entry point.
"""
from .base_scraper import BaseScraper
from .generic_scraper import GenericScraper
from .github_scraper import GitHubScraper
from .pdf_scraper import PDFScraper
from ..utils import get_url_content_type

def get_scraper_for_url(url: str, include_dirs_str: str = "", exclude_dirs_str: str = "") -> 'BaseScraper':
    """
    Selects the appropriate scraper class for a remote URL.
    """
    if "github.com" in url:
        include_dirs = [d.strip() for d in include_dirs_str.split(',') if d.strip()]
        exclude_dirs = [d.strip() for d in exclude_dirs_str.split(',') if d.strip()]
        return GitHubScraper(url, include_dirs=include_dirs, exclude_dirs=exclude_dirs)

    content_type = get_url_content_type(url)
    if content_type and 'application/pdf' in content_type:
        return PDFScraper(url)
    
    return GenericScraper(url)