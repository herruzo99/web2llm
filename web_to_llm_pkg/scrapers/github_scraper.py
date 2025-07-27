"""A scraper for GitHub repositories with intelligent filtering."""

import os
import re
import tempfile
import git
from datetime import datetime, timezone

from .base_scraper import BaseScraper
from ..utils import fetch_json_api
from ..config import GITHUB_SCRAPER_IGNORE_CONFIG

class GitHubScraper(BaseScraper):
    """
    Scrapes a GitHub repository by cloning it and extracting its content.
    Supports allow-listing (--include-dirs) and block-listing (--exclude-dirs)
    of specific directories for a focused scrape.
    """
    LANGUAGE_MAP = {
        '.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.java': 'java', '.c': 'c', '.cpp': 'cpp', '.h': 'c',
        '.cs': 'csharp', '.go': 'go', '.rs': 'rust', '.rb': 'ruby', '.php': 'php', '.html': 'html', '.css': 'css', '.scss': 'scss',
        '.json': 'json', '.xml': 'xml', '.yaml': 'yaml', '.yml': 'yaml', '.md': 'markdown', '.sh': 'shell', '.ps1': 'powershell',
        'dockerfile': 'dockerfile', 'makefile': 'makefile', '.txt': 'text'
    }

    def __init__(self, url: str, include_dirs: list[str] = None, exclude_dirs: list[str] = None):
        """
        Initializes the GitHub scraper.
        """
        super().__init__(url)
        self.ignore_config = GITHUB_SCRAPER_IGNORE_CONFIG
        self.ignore_config["filenames_lower"] = {fn.lower() for fn in self.ignore_config["filenames"]}
        self.include_dirs = include_dirs or []
        self.exclude_dirs = exclude_dirs or []

    def scrape(self) -> tuple[str, dict]:
        """Clones the repo, processes its files, and returns the structured content."""
        owner, repo_name = self._parse_github_url()
        if not owner or not repo_name:
            raise ValueError("Invalid GitHub URL format. Expected 'https://github.com/owner/repo'.")

        api_url = f"https://api.github.com/repos/{owner}/{repo_name}"
        repo_data = fetch_json_api(api_url)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_url = f"https://github.com/{owner}/{repo_name}.git"
            print(f"Cloning repository from {repo_url}...")
            git.Repo.clone_from(repo_url, temp_dir)
            print("Clone successful.")
            
            file_tree, concatenated_content = self._process_repo(temp_dir)

        front_matter = self._create_front_matter(repo_data)
        final_markdown = f"{front_matter}\n## Repository File Tree\n\n```\n{file_tree}\n```\n\n## File Contents\n\n{concatenated_content}"
        context_data = repo_data
        
        return final_markdown, context_data

    def _should_ignore(self, path: str, is_dir: bool) -> bool:
        """
        Checks if a path should be ignored based on static config or dynamic exclude list.
        """
        name = os.path.basename(path)
        
        if is_dir and name in self.exclude_dirs:
            return True

        if is_dir:
            return name in self.ignore_config["directories"]
        
        name_lower = name.lower()
        _, extension = os.path.splitext(name_lower)
        
        return (
            name_lower in self.ignore_config["filenames_lower"] or
            extension in self.ignore_config["extensions"]
        )

    def _process_repo(self, repo_path: str) -> tuple[str, str]:
        """Walks the repo, builds a file tree, and concatenates text files."""
        file_tree_lines = []
        concatenated_content_parts = []

        if self.include_dirs and self.exclude_dirs:
            print("Warning: Both --include-dirs and --exclude-dirs are specified. "
                  "--include-dirs will take precedence.")
        
        start_paths = [repo_path]
        if self.include_dirs:
            start_paths = []
            for d in self.include_dirs:
                path = os.path.join(repo_path, d)
                if os.path.exists(path):
                    start_paths.append(path)
                else:
                     print(f"Warning: Specified include directory does not exist: {d}")

        for start_path in start_paths:
            if self.include_dirs:
                 file_tree_lines.append(f"|-- {os.path.basename(start_path)}/")
                 
            for root, dirs, files in os.walk(start_path, topdown=True):
                dirs[:] = [d for d in dirs if not self._should_ignore(os.path.join(root, d), is_dir=True)]
                
                relative_root_to_start = os.path.relpath(root, start_path)
                if relative_root_to_start == ".":
                    level = 0
                else:
                    level = len(relative_root_to_start.split(os.sep))
                
                if self.include_dirs:
                    level += 1
                
                indent = " " * 4 * level
                
                if root != start_path:
                    dir_indent = " " * 4 * (level - 1)
                    file_tree_lines.append(f"{dir_indent}|-- {os.path.basename(root)}/")

                file_indent = " " * 4 * level

                for f in sorted(files):
                    file_path = os.path.join(root, f)
                    if self._should_ignore(file_path, is_dir=False):
                        continue
                    
                    file_tree_lines.append(f"{file_indent}|-- {f}")
                    
                    if self._is_text_file(file_path):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as file_content:
                                content = file_content.read()
                            
                            relative_file_path = os.path.relpath(file_path, repo_path)
                            file_ext = os.path.splitext(f)[1]
                            lang = self.LANGUAGE_MAP.get(file_ext, 'text')
                            if os.path.basename(f).lower() in self.LANGUAGE_MAP:
                                 lang = self.LANGUAGE_MAP.get(os.path.basename(f).lower())
                                 
                            concatenated_content_parts.append(
                                f"\n---\n\n"
                                f"### `{relative_file_path}`\n\n"
                                f"```{lang}\n"
                                f"{content}\n"
                                f"```\n"
                            )
                        except Exception as e:
                            print(f"Could not read file {file_path}: {e}")

        return "\n".join(file_tree_lines), "".join(concatenated_content_parts)

    def _parse_github_url(self) -> tuple[str | None, str | None]:
        """Extracts owner and repo name from the GitHub URL."""
        match = re.search(r"github\.com/([^/]+)/([^/]+)", self.url)
        if match:
            return match.group(1), match.group(2).replace('.git', '')
        return None, None

    def _create_front_matter(self, data: dict) -> str:
        """Creates the YAML front matter string from GitHub API data."""
        description_text = (data.get("description") or "No description available.").strip()
        license_text = (data.get("license", {}).get("name") or "No license specified") if data.get("license") else "No license specified"

        return (
            "---\n"
            f'repo_name: "{data.get("full_name", "")}"\n'
            f'source_url: "{data.get("html_url", "")}"\n'
            f'description: "{description_text}"\n'
            f'language: "{data.get("language", "N/A")}"\n'
            f'stars: {data.get("stargazers_count", 0)}\n'
            f'forks: {data.get("forks_count", 0)}\n'
            f'watchers: {data.get("watchers_count", 0)}\n'
            f'open_issues: {data.get("open_issues_count", 0)}\n'
            f'license: "{license_text}"\n'
            f'created_at: "{data.get("created_at", "")}"\n'
            f'last_pushed: "{data.get("pushed_at", "")}"\n'
            f'scraped_at: "{datetime.now(timezone.utc).isoformat()}"\n'
            "---\n"
        )
    
    def _is_text_file(self, filepath: str) -> bool:
        """Determines if a file is likely a text file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                f.read(1024)
            return True
        except (UnicodeDecodeError, IOError):
            return False