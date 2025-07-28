import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import git
import pathspec

from ..utils import fetch_json
from .base_scraper import BaseScraper

LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".json": "json",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
    ".sh": "shell",
    ".ps1": "powershell",
    "dockerfile": "dockerfile",
    "makefile": "makefile",
    ".txt": "text",
}


def is_likely_text_file(filepath: Path) -> bool:
    """Check if a file is likely text-based by trying to decode a small chunk."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            f.read(1024)  # Read a small chunk to test encoding
        return True
    except (UnicodeDecodeError, IOError):
        return False


def _process_directory(root_path: str, ignore_patterns: list[str]) -> tuple[str, str]:
    """
    Walk a directory, creating a file tree and concatenating the content of text files,
    respecting gitignore-style patterns.
    """
    file_tree_lines = []
    concatenated_content_parts = []
    root = Path(root_path)

    # Use gitwildmatch for familiar .gitignore style patterns.
    spec = pathspec.PathSpec.from_lines("gitwildmatch", ignore_patterns)
    all_files = [p for p in root.rglob("*") if p.is_file()]
    matched_files = [f for f in all_files if not spec.match_file(str(f.relative_to(root)))]

    # We still need to walk the directories to build the tree structure accurately
    # and not show empty, ignored directories.
    seen_dirs = set()
    for file_path in sorted(matched_files):
        # Add parent directories to the tree structure
        relative_path = file_path.relative_to(root)
        for parent in reversed(list(relative_path.parents)[:-1]):
            if parent not in seen_dirs:
                depth = len(parent.parts) - 1
                indent = "    " * depth
                file_tree_lines.append(f"{indent}|-- {parent.name}/")
                seen_dirs.add(parent)

        # Add file to the tree structure
        depth = len(relative_path.parts) - 1
        indent = "    " * depth
        file_tree_lines.append(f"{indent}|-- {relative_path.name}")

        # Process and concatenate file content
        if is_likely_text_file(file_path):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Determine language for syntax highlighting
                lang = LANGUAGE_MAP.get(file_path.suffix.lower(), "text")
                if file_path.name.lower() in LANGUAGE_MAP:
                    lang = LANGUAGE_MAP[file_path.name.lower()]

                # Use forward slashes for cross-platform consistency in the markdown output
                relative_file_path_str = str(relative_path).replace("\\", "/")
                concatenated_content_parts.append(f"\n---\n\n### `{relative_file_path_str}`\n\n```{lang}\n{content}\n```\n")
            except Exception as e:
                print(f"Warning: Could not read file {file_path}: {e}")

    return "\n".join(file_tree_lines), "".join(concatenated_content_parts)


class GitHubScraper(BaseScraper):
    """Scrapes a GitHub repository by cloning it and extracting its content."""

    def __init__(self, url: str, config: dict):
        super().__init__(source=url, config=config)
        self.ignore_patterns = self.config.get("fs_scraper", {}).get("ignore_patterns", [])

    def scrape(self) -> tuple[str, dict]:
        owner, repo_name = self._parse_github_url()
        if not owner or not repo_name:
            raise ValueError("Invalid GitHub URL format. Expected 'https://github.com/owner/repo'.")

        api_url = f"https://api.github.com/repos/{owner}/{repo_name}"
        repo_data = fetch_json(api_url)

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_url = f"https://github.com/{owner}/{repo_name}.git"
            print(f"Cloning repository from {repo_url}...")
            # Use a shallow clone to save time and bandwidth
            git.Repo.clone_from(repo_url, temp_dir, depth=1)
            print("Clone successful.")

            file_tree, concatenated_content = _process_directory(temp_dir, self.ignore_patterns)

        front_matter = self._create_front_matter(repo_data)
        final_markdown = f"{front_matter}\n## Repository File Tree\n\n```\n{file_tree}\n```\n\n## File Contents\n\n{concatenated_content}"

        return final_markdown, repo_data

    def _parse_github_url(self) -> tuple[str | None, str | None]:
        # Simple regex to extract owner and repo name from various GitHub URL formats
        match = re.search(r"github\.com/([^/]+)/([^/]+)", self.source)
        if match:
            return match.group(1), match.group(2).replace(".git", "")
        return None, None

    def _create_front_matter(self, data: dict) -> str:
        # Safely get nested data to avoid KeyErrors
        description_text = (data.get("description") or "").strip()
        license_info = data.get("license")
        license_text = license_info.get("name") if license_info else "No license specified"

        return (
            "---\n"
            f'repo_name: "{data.get("full_name", "")}"\n'
            f'source_url: "{data.get("html_url", "")}"\n'
            f'description: "{description_text}"\n'
            f'language: "{data.get("language", "N/A")}"\n'
            f"stars: {data.get('stargazers_count', 0)}\n"
            f"forks: {data.get('forks_count', 0)}\n"
            f'license: "{license_text}"\n'
            f'scraped_at: "{datetime.now(timezone.utc).isoformat()}"\n'
            "---\n"
        )
