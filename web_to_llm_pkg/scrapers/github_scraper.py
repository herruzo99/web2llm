import os
import re
import tempfile
import git
from datetime import datetime, timezone

from .base_scraper import BaseScraper
from ..utils import fetch_json
from ..config import CODE_IGNORE_CONFIG

LANGUAGE_MAP = {
    '.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.java': 'java', '.c': 'c', '.cpp': 'cpp', '.h': 'c',
    '.cs': 'csharp', '.go': 'go', '.rs': 'rust', '.rb': 'ruby', '.php': 'php', '.html': 'html', '.css': 'css', '.scss': 'scss',
    '.json': 'json', '.xml': 'xml', '.yaml': 'yaml', '.yml': 'yaml', '.md': 'markdown', '.sh': 'shell', '.ps1': 'powershell',
    'dockerfile': 'dockerfile', 'makefile': 'makefile', '.txt': 'text'
}

def is_likely_text_file(filepath: str) -> bool:
    """Check if a file is likely text-based by trying to decode a small chunk."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            f.read(1024)
        return True
    except (UnicodeDecodeError, IOError):
        return False

def _process_directory(
    root_path: str,
    include_dirs: list[str],
    exclude_dirs: list[str],
    include_all: bool = False
) -> tuple[str, str]:
    """
    Walk a directory, creating a file tree and concatenating the content of text files.
    This is shared by both the GitHub and Local Folder scrapers.
    """
    file_tree_lines = []
    concatenated_content_parts = []
    
    if include_all:
        ignore_dirs_set = set()
        ignore_files_lower = set()
        ignore_extensions_set = set()
    else:
        ignore_dirs_set = set(CODE_IGNORE_CONFIG["directories"])
        ignore_files_lower = {fn.lower() for fn in CODE_IGNORE_CONFIG["filenames"]}
        ignore_extensions_set = set(CODE_IGNORE_CONFIG["extensions"])

    start_paths = [root_path]
    if include_dirs:
        start_paths = [os.path.join(root_path, d) for d in include_dirs if os.path.isdir(os.path.join(root_path, d))]
        if not start_paths:
            print(f"Warning: None of the specified --include-dirs exist: {include_dirs}")

    for path in start_paths:
        for dirpath, dirnames, filenames in os.walk(path, topdown=True):
            # Filter directories in-place to prevent `os.walk` from descending into them.
            dirnames[:] = [d for d in dirnames if d not in ignore_dirs_set and d not in exclude_dirs]

            relative_path = os.path.relpath(dirpath, root_path)
            
            if relative_path == '.':
                depth = 0
            else:
                depth = len(relative_path.split(os.sep))

            if relative_path != '.':
                indent = "    " * (depth)
                file_tree_lines.append(f"{indent}|-- {os.path.basename(dirpath)}/")

            files_indent = "    " * (depth + 1)

            for f in sorted(filenames):
                file_path = os.path.join(dirpath, f)
                _, extension = os.path.splitext(f)
                if f.lower() in ignore_files_lower or extension in ignore_extensions_set:
                    continue

                file_tree_lines.append(f"{files_indent}|-- {f}")
                if is_likely_text_file(file_path):
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
    """Scrapes a GitHub repository by cloning it and extracting its content."""
    def __init__(self, url: str, include_dirs: str, exclude_dirs: str, include_all: bool = False):
        super().__init__(source=url)
        self.include_dirs = [d.strip() for d in include_dirs.split(',') if d.strip()]
        self.exclude_dirs = [d.strip() for d in exclude_dirs.split(',') if d.strip()]
        self.include_all = include_all

    def scrape(self) -> tuple[str, dict]:
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

            file_tree, concatenated_content = _process_directory(temp_dir, self.include_dirs, self.exclude_dirs, self.include_all)

        front_matter = self._create_front_matter(repo_data)
        final_markdown = f"{front_matter}\n## Repository File Tree\n\n```\n{file_tree}\n```\n\n## File Contents\n\n{concatenated_content}"

        return final_markdown, repo_data

    def _parse_github_url(self) -> tuple[str | None, str | None]:
        match = re.search(r"github\.com/([^/]+)/([^/]+)", self.source)
        if match:
            return match.group(1), match.group(2).replace('.git', '')
        return None, None

    def _create_front_matter(self, data: dict) -> str:
        description_text = (data.get("description") or "").strip()
        license_info = data.get("license")
        license_text = license_info.get("name") if license_info else "No license specified"

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