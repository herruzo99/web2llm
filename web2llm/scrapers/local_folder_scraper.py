import sys
from datetime import datetime, timezone
from pathlib import Path

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
        # Use pathlib for modern path manipulation and consistency
        folder_root = Path(self.source)
        if not folder_root.is_dir():
            raise NotADirectoryError(f"The provided path is not a directory: {self.source}")

        self.logger.info(f"Processing local directory: {self.source}")

        # Combine base ignore patterns with patterns from the folder's .gitignore
        combined_ignore_patterns = list(self.ignore_patterns)
        gitignore_path = folder_root / ".gitignore"
        if gitignore_path.is_file() and not self.include_all:
            self.logger.debug("Found .gitignore in local folder, adding its patterns.")
            combined_ignore_patterns.extend(gitignore_path.read_text(encoding="utf-8").splitlines())

        file_tree, concatenated_content = process_directory(str(folder_root), combined_ignore_patterns, self.debug)

        folder_name = folder_root.name
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
