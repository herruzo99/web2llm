"""A scraper for processing a local directory structure."""

import os
from datetime import datetime, timezone

from .github_scraper import GitHubScraper

class LocalFolderScraper(GitHubScraper):
    """
    Scrapes a local folder, reusing the file processing and filtering logic
    from the GitHubScraper.
    """
    def __init__(self, path: str, include_dirs: list[str] = None, exclude_dirs: list[str] = None):
        """
        Initializes the LocalFolderScraper.

        Args:
            path: The local directory path to be scraped.
            include_dirs: An optional list of top-level directories to exclusively include.
            exclude_dirs: An optional list of top-level directories to exclude.
        """
        super().__init__(url=path, include_dirs=include_dirs, exclude_dirs=exclude_dirs)

    def scrape(self) -> tuple[str, dict]:
        """
        Processes the local folder and returns its structured content.
        """
        folder_path = self.url
        if not os.path.isdir(folder_path):
            raise NotADirectoryError(f"The provided path is not a directory: {folder_path}")

        print(f"Processing local directory: {folder_path}")

        file_tree, concatenated_content = self._process_repo(folder_path)

        scraped_at = datetime.now(timezone.utc).isoformat()
        folder_name = os.path.basename(os.path.normpath(folder_path))

        front_matter = (
            "---\n"
            f'folder_name: "{folder_name}"\n'
            f'source_path: "{folder_path}"\n'
            f'scraped_at: "{scraped_at}"\n'
            "---\n"
        )
        
        final_markdown = f"{front_matter}\n## Folder File Tree\n\n```\n{file_tree}\n```\n\n## File Contents\n\n{concatenated_content}"
        
        context_data = {
            "source_path": folder_path,
            "folder_name": folder_name,
            "scraped_at": scraped_at,
        }
        
        return final_markdown, context_data