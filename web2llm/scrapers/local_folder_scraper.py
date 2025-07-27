import os
import re
from datetime import datetime, timezone

from .base_scraper import BaseScraper
from .github_scraper import _process_directory


class LocalFolderScraper(BaseScraper):
    """
    Scrapes a local folder, reusing the file processing and filtering logic
    from the GitHubScraper.
    """

    def __init__(
        self, path: str, include_dirs: str, exclude_dirs: str, include_all: bool = False
    ):
        super().__init__(source=path)
        try:
            self.include_patterns = [
                re.compile(p.strip()) for p in include_dirs.split(",") if p.strip()
            ]
            self.exclude_patterns = [
                re.compile(p.strip()) for p in exclude_dirs.split(",") if p.strip()
            ]
        except re.error as e:
            raise ValueError(f"Invalid regex pattern provided: {e}")
        self.include_all = include_all

    def scrape(self) -> tuple[str, dict]:
        if not os.path.isdir(self.source):
            raise NotADirectoryError(
                f"The provided path is not a directory: {self.source}"
            )

        print(f"Processing local directory: {self.source}")

        file_tree, concatenated_content = _process_directory(
            self.source, self.include_patterns, self.exclude_patterns, self.include_all
        )

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
