import logging
from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """Abstract base class for all scraper implementations."""

    def __init__(self, source: str, config: dict | None = None):
        self.source = source
        self.config = config if config is not None else {}
        self.debug = self.config.get("debug", False)
        self.render_js = self.config.get("render_js", False)
        self.check_content_type = self.config.get("check_content_type", False)
        self.include_all = self.config.get("include_all", False)
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def scrape(self) -> tuple[str, dict]:
        """
        Performs the scraping asynchronously.

        Returns:
            A tuple of (markdown_content, context_data).
        """
        pass
