"""A scraper for GitHub repositories with intelligent filtering."""

import os
import re
import tempfile
import git
from datetime import datetime, timezone
from typing import Generator

from .base_scraper import BaseScraper
from ..utils import fetch_json
from ..config import GITHUB_SCRAPER_IGNORE_CONFIG

LANGUAGE_MAP = {
    '.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.java': 'java', '.c': 'c', '.cpp': 'cpp', '.h': 'c',
    '.cs': 'csharp', '.go': 'go', '.rs': 'rust', '.rb': 'ruby', '.php': 'php', '.html': 'html', '.css': 'css', '.scss': 'scss',
    '.json': 'json', '.xml': 'xml', '.yaml': 'yaml', '.yml': 'yaml', '.md': 'markdown', '.sh': 'shell', '.ps1': 'powershell',
    'dockerfile': 'dockerfile', 'makefile': 'makefile', '.txt': 'text'
}

def _is_text_file(filepath: str) -> bool:
    """Determines if a file is likely a text file by trying to read it."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            f.read(1024) # Read a small chunk
        return True
    except (UnicodeDecodeError, IOError):
        return False

def _process_directory(
    root_path: str,
    include_dirs: list[str],
    exclude_dirs: list[str]
) -> tuple[str, str]:
    """
    Walks a directory, creating a file tree and concatenating the content of text files.
    This is the core logic shared by both the GitHub and Local Folder scrapers.
    """
    file_tree_lines = []
    concatenated_content_parts = []
    ignore_config = GITHUB_SCRAPER_IGNORE_CONFIG
    ignore_files_lower = {fn.lower() for fn in ignore_config["filenames"]}

    # Determine the starting points for the walk
    start_paths = [root_path]
    if include_dirs:
        start_paths = [os.path.join(root_path, d) for d in include_dirs if os.path.isdir(os.path.join(root_path, d))]
        if not start_paths:
            print(f"Warning: None of the specified --include-dirs exist: {include_dirs}")

    for path in start_paths:
        for dirpath, dirnames, filenames in os.walk(path, topdown=True):
            # Filter directories in-place
            dirnames[:] = [d for d in dirnames if d not in ignore_config["directories"] and d not in exclude_dirs]

            relative_path = os.path.relpath(dirpath, root_path)
            depth = relative_path.count(os.sep) if relative_path != '.' else 0
            indent = "    " * depth

            if relative_path != '.':
                file_tree_lines.append(f"{indent}|-- {os.path.basename(dirpath)}/")
            indent += "    "

            for f in sorted(filenames):
                file_path = os.path.join(dirpath, f)
                _, extension = os.path.splitext(f)
                if f.lower() in ignore_files_lower or extension in ignore_config["extensions"]:
                    continue

                file_tree_lines.append(f"{indent}|-- {f}")
                if _is_text_file(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file_content:
                            content = file_content.read()

                        relative_file_path = os.path.relpath(file_path, root_path)
                        lang = LANGUAGE_MAP.get(extension, 'text')
                        if f.lower() in LANGUAGE_MAP: # for Dockerfile, Makefile
                            lang = LANGUAGE_MAP[f.lower()]

                        concatenated_content_parts.append(
                            f"\n---\n\n### `{relative_file_path}`\n\n```{lang}\n{content}\n```\n"
                        )
                    except Exception as e:
                        print(f"Warning: Could not read file {file_path}: {e}")

    return "\n".join(file_tree_lines), "".join(concatenated_content_parts)


class GitHubScraper(BaseScraper):
    """
    Scrapes a GitHub repository by cloning it and extracting its content.
    """
    def __init__(self, url: str, include_dirs_str: str, exclude_dirs_str: str):
        super().__init__(source=url)
        self.include_dirs = [d.strip() for d in include_dirs_str.split(',') if d.strip()]
        self.exclude_dirs = [d.strip() for d in exclude_dirs_str.split(',') if d.strip()]

    def scrape(self) -> tuple[str, dict]:
        """Clones the repo, processes its files, and returns the structured content."""
        owner, repo_name = self._parse_github_url()
        if not owner or not repo_name:
            raise ValueError("Invalid GitHub URL format. Expected 'https://github.com/owner/repo'.")

        api_url = f"https://api.github.com/repos/{owner}/{repo_name}"
        repo_data = fetch_json(api_url)

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_url = f"https://github.com/{owner}/{repo_name}.git"
            print(f"Cloning repository from {repo_url}...")
            git.Repo.clone_from(repo_url, temp_dir, depth=1) # shallow clone
            print("Clone successful.")

            file_tree, concatenated_content = _process_directory(temp_dir, self.include_dirs, self.exclude_dirs)

        front_matter = self._create_front_matter(repo_data)
        final_markdown = f"{front_matter}\n## Repository File Tree\n\n```\n{file_tree}\n```\n\n## File Contents\n\n{concatenated_content}"

        # We'll use the API response as the context data
        return final_markdown, repo_data

    def _parse_github_url(self) -> tuple[str | None, str | None]:
        """Extracts owner and repo name from the GitHub URL."""
        match = re.search(r"github\.com/([^/]+)/([^/]+)", self.source)
        if match:
            return match.group(1), match.group(2).replace('.git', '')
        return None, None

    def _create_front_matter(self, data: dict) -> str:
        """Creates the YAML front matter string from GitHub API data."""
        # Use .get() with default values for safety
        description_text = (data.get("description") or "No description available.").strip()
        license_info = data.get("license")
        license_text = license_info.get("name", "No license specified") if license_info else "No license specified"

        return (
            "---\n"
            f'repo_name: "{data.get("full_name", "")}"\n'
            f'source_url: "{data.get("html_url", "")}"\n'
            f'description: "{description_text}"\n'
            f'language: "{data.get("language", "N/A")}"\n'
            f'stars: {data.get("stargazers_count", 0)}\n'
            f'forks: {data.get("forks_count", 0)}\n'
            f'license: "{license_text}"\n'
            f'scraped_at: "{datetime.now(timezone.utc).isoformat()}"\n'
            "---\n"
        )