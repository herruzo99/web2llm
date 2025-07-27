"""Defines the abstract base class for all scrapers."""

from abc import ABC, abstractmethod

class BaseScraper(ABC):
    """
    Abstract base class for all scraper implementations.

    This class defines the "contract" that all scraper strategies must adhere to,
    ensuring a consistent interface for the main application.
    """
    def __init__(self, url: str):
        self.url = url

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