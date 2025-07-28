import os
from datetime import datetime, timezone

from .base_scraper import BaseScraper
from .github_scraper import _process_directory


class LocalFolderScraper(BaseScraper):
    """
    Scrapes a local folder, reusing the file processing and filtering logic
    from the GitHubScraper.
    """

    def __init__(self, path: str, config: dict):
        super().__init__(source=path, config=config)
        self.ignore_patterns = self.config.get("fs_scraper", {}).get("ignore_patterns", [])

    def scrape(self) -> tuple[str, dict]:
        if not os.path.isdir(self.source):
            raise NotADirectoryError(f"The provided path is not a directory: {self.source}")

        print(f"Processing local directory: {self.source}")

        file_tree, concatenated_content = _process_directory(self.source, self.ignore_patterns)

        scraped_at = datetime.now(timezone.utc).isoformat()
        folder_name = os.path.basename(os.path.normpath(self.source))

        front_matter = f'---\nfolder_name: "{folder_name}"\nsource_path: "{self.source}"\nscraped_at: "{scraped_at}"\n---\n'

        final_markdown = f"{front_matter}\n## Folder File Tree\n\n```\n{file_tree}\n```\n\n## File Contents\n\n{concatenated_content}"

        context_data = {
            "source_path": self.source,
            "folder_name": folder_name,
            "scraped_at": scraped_at,
        }

        return final_markdown, context_data
