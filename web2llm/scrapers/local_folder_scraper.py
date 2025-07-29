import os
import sys
from datetime import datetime, timezone

import yaml

from ..utils import process_directory
from .base_scraper import BaseScraper


class LocalFolderScraper(BaseScraper):
    """
    Scrapes a local folder, reusing the file processing and filtering logic
    from the GitHubScraper.
    """

    def __init__(self, path: str, config: dict):
        super().__init__(source=path, config=config)
        self.ignore_patterns = self.config.get("fs_scraper", {}).get("ignore_patterns", [])
        self.logger.debug("LocalFolderScraper initialized in debug mode.")

    async def scrape(self) -> tuple[str, dict]:
        if self.render_js:
            self.logger.warning(
                "Warning: The --render-js flag is not applicable to local folder scraping and will be ignored.", file=sys.stderr
            )
        self.logger.debug(f"Starting scrape for local path: {self.source}")
        if not os.path.isdir(self.source):
            raise NotADirectoryError(f"The provided path is not a directory: {self.source}")

        self.logger.info(f"Processing local directory: {self.source}")
        file_tree, concatenated_content = process_directory(self.source, self.ignore_patterns, self.debug)

        folder_name = os.path.basename(os.path.normpath(self.source))
        scraped_at = datetime.now(timezone.utc).isoformat()

        front_matter_data = {
            "folder_name": folder_name,
            "source_path": self.source,
            "scraped_at": scraped_at,
        }
        front_matter_string = yaml.dump(front_matter_data, sort_keys=False, default_flow_style=False, indent=2)
        front_matter = f"---\n{front_matter_string}---\n"

        final_markdown = f"{front_matter}\n## Folder File Tree\n\n```\n{file_tree}\n```\n\n## File Contents\n\n{concatenated_content}"

        context_data = {
            "source_path": self.source,
            "folder_name": folder_name,
            "scraped_at": scraped_at,
        }

        self.logger.debug("Local folder scrape complete.")
        return final_markdown, context_data
