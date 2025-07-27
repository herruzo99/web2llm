"""A scraper for processing a local directory structure."""

import os
from datetime import datetime, timezone

from .base_scraper import BaseScraper
from .github_scraper import _process_directory # Import the shared logic

class LocalFolderScraper(BaseScraper):
    """
    Scrapes a local folder, reusing the file processing and filtering logic
    from the GitHubScraper.
    """
    def __init__(self, path: str, include_dirs_str: str, exclude_dirs_str: str):
        super().__init__(source=path)
        self.include_dirs = [d.strip() for d in include_dirs_str.split(',') if d.strip()]
        self.exclude_dirs = [d.strip() for d in exclude_dirs_str.split(',') if d.strip()]

    def scrape(self) -> tuple[str, dict]:
        """Processes the local folder and returns its structured content."""
        if not os.path.isdir(self.source):
            raise NotADirectoryError(f"The provided path is not a directory: {self.source}")

        print(f"Processing local directory: {self.source}")

        file_tree, concatenated_content = _process_directory(self.source, self.include_dirs, self.exclude_dirs)

        scraped_at = datetime.now(timezone.utc).isoformat()
        folder_name = os.path.basename(os.path.normpath(self.source))

        front_matter = (
            "---\n"
            f'folder_name: "{folder_name}"\n'
            f'source_path: "{self.source}"\n'
            f'scraped_at: "{scraped_at}"\n'
            "---\n"
        )

        final_markdown = f"{front_matter}\n## Folder File Tree\n\n```\n{file_tree}\n```\n\n## File Contents\n\n{concatenated_content}"

        context_data = {
            "source_path": self.source,
            "folder_name": folder_name,
            "scraped_at": scraped_at,
        }

        return final_markdown, context_data