"""
Scraper Factory Module

This module contains the unified factory function `get_scraper`, which is the
primary entry point for selecting the correct scraping strategy for any given
resource, whether it's a local path or a remote URL.
"""
import os
from urllib.parse import urlparse

from .base_scraper import BaseScraper
from .generic_scraper import GenericScraper
from .github_scraper import GitHubScraper
from .local_folder_scraper import LocalFolderScraper
from .pdf_scraper import PDFScraper
from ..utils import get_url_content_type

def get_scraper(resource: str, include_dirs_str: str = "", exclude_dirs_str: str = "") -> BaseScraper | None:
    """
    Selects the appropriate scraper class for a given resource.

    This function inspects the resource string to determine if it's a local
    path or a URL and then chooses the best scraper for the job.
    """
    # First, sanitize and check if it's a local path.
    # This is more reliable than just checking for "http"
    resource_path = os.path.expanduser(resource)
    if os.path.exists(resource_path):
        if os.path.isdir(resource_path):
            return LocalFolderScraper(resource_path, include_dirs_str, exclude_dirs_str)
        elif resource_path.lower().endswith('.pdf'):
            return PDFScraper(resource_path)
        else:
            # We could eventually support local .html files here.
            raise ValueError(f"Unsupported local file type: {resource_path}")

    # If it's not a local path, treat it as a URL.
    parsed_url = urlparse(resource)
    if not all([parsed_url.scheme, parsed_url.netloc]):
        raise ValueError(f"Invalid URL or non-existent local path: {resource}")

    if "github.com" in parsed_url.netloc:
        return GitHubScraper(resource, include_dirs_str, exclude_dirs_str)

    # For other URLs, check the content-type to see if it's a PDF.
    content_type = get_url_content_type(resource)
    if content_type and 'application/pdf' in content_type:
        return PDFScraper(resource)

    # If all else fails, assume it's a standard HTML page.
    return GenericScraper(resource)