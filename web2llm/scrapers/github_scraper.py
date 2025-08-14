import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import git
import yaml

from ..utils import fetch_json, process_directory
from .base_scraper import BaseScraper


class GitHubScraper(BaseScraper):
    """Scrapes a GitHub repository by cloning it and extracting its content."""

    def __init__(self, url: str, config: dict):
        super().__init__(source=url, config=config)
        self.ignore_patterns = self.config.get("fs_scraper", {}).get("ignore_patterns", [])
        self.logger.debug("GitHubScraper initialized in debug mode.")

    async def scrape(self) -> tuple[str, dict]:
        if self.render_js:
            self.logger.warning("Warning: The --render-js flag is not applicable to GitHub scraping and will be ignored.", file=sys.stderr)
        self.logger.debug(f"Starting scrape for GitHub URL: {self.source}")
        owner, repo_name = self._parse_github_url()
        if not owner or not repo_name:
            raise ValueError("Invalid GitHub URL format. Expected 'https://github.com/owner/repo'.")

        api_url = f"https://api.github.com/repos/{owner}/{repo_name}"
        self.logger.debug(f"Fetching repository metadata from API: {api_url}")
        repo_data = await fetch_json(api_url, debug=self.debug)
        self.logger.debug("Successfully fetched repository metadata.")

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_url = f"https://github.com/{owner}/{repo_name}.git"
            self.logger.debug(f"Cloning repository from {repo_url} into {temp_dir}")
            git.Repo.clone_from(repo_url, temp_dir, depth=1)
            self.logger.debug("Clone successful.")
            # Combine base ignore patterns with patterns from the repo's .gitignore
            repo_root = Path(temp_dir)
            combined_ignore_patterns = list(self.ignore_patterns)
            gitignore_path = repo_root / ".gitignore"
            if gitignore_path.is_file() and not self.include_all:
                self.logger.debug("Found .gitignore in repository, adding its patterns.")
                combined_ignore_patterns.extend(gitignore_path.read_text(encoding="utf-8").splitlines())

            file_tree, concatenated_content = process_directory(str(repo_root), combined_ignore_patterns, self.debug)

        front_matter = self._create_front_matter(repo_data)
        final_markdown = f"{front_matter}\n## Repository File Tree\n\n```\n{file_tree}\n```\n\n## File Contents\n\n{concatenated_content}"

        self.logger.debug("GitHub scrape complete.")
        return final_markdown, repo_data

    def _parse_github_url(self) -> tuple[str | None, str | None]:
        match = re.search(r"github\.com/([^/]+)/([^/]+)", self.source)
        if match:
            return match.group(1), match.group(2).replace(".git", "")
        return None, None

    def _create_front_matter(self, data: dict) -> str:
        description_text = (data.get("description") or "").strip()
        license_info = data.get("license")
        license_text = license_info.get("name") if license_info else "No license specified"

        front_matter_data = {
            "repo_name": data.get("full_name", ""),
            "source_url": data.get("html_url", ""),
            "description": description_text,
            "language": data.get("language", "N/A"),
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "license": license_text,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }

        front_matter_string = yaml.dump(front_matter_data, sort_keys=False, default_flow_style=False, indent=2)
        return f"---\n{front_matter_string}---\n"
