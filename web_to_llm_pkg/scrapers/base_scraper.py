"""Defines the abstract base class for all scrapers."""

from abc import ABC, abstractmethod

class BaseScraper(ABC):
    """
    Abstract base class for all scraper implementations.
    """
    def __init__(self, source: str):
        # `source` can be a URL or a local file path.
        self.source = source

    @abstractmethod
    def scrape(self) -> tuple[str, dict]:
        """
        The main method to perform scraping. Must be implemented by all subclasses.

        Returns:
            A tuple containing:
            - The main content as a clean string (e.g., Markdown).
            - A dictionary with metadata and context.
        """
        pass