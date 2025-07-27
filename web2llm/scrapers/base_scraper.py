from abc import ABC, abstractmethod

class BaseScraper(ABC):
    """Abstract base class for all scraper implementations."""
    def __init__(self, source: str):
        # `source` can be a URL or a local file path.
        self.source = source

    @abstractmethod
    def scrape(self) -> tuple[str, dict]:
        """
        Performs the scraping.

        Returns:
            A tuple of (markdown_content, context_data).
        """
        pass