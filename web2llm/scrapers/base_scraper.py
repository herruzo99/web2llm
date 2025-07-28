from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """Abstract base class for all scraper implementations."""

    def __init__(self, source: str, config: dict | None = None):
        # `source` can be a URL or a local file path.
        # `config` holds the merged configuration for the scraper to use.
        self.source = source
        self.config = config if config is not None else {}

    @abstractmethod
    def scrape(self) -> tuple[str, dict]:
        """
        Performs the scraping.

        Returns:
            A tuple of (markdown_content, context_data).
        """
        pass
