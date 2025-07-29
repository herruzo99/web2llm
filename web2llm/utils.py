import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
import pathspec

if TYPE_CHECKING:
    from playwright.async_api import Page

logger = logging.getLogger(__name__)
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


# --- Core HTTP Request Logic ---


async def _make_httpx_request(url: str, debug: bool = False) -> httpx.Response:
    """
    Creates an httpx client and makes a GET request, handling common errors.
    This is a low-level helper to be used by other fetch functions.
    """
    logger.debug(f"Making httpx GET request to {url}")
    async with httpx.AsyncClient(headers=REQUEST_HEADERS, follow_redirects=True) as client:
        try:
            response = await client.get(url, timeout=15)
            response.raise_for_status()
            return response
        except httpx.RequestError as e:
            raise IOError(f"Network error fetching '{url}': {e}")


# --- HTML Fetching ---


async def _fetch_html_httpx(url: str, debug: bool = False) -> str:
    """Fetches HTML using the core httpx request helper."""
    response = await _make_httpx_request(url, debug)
    return response.text


async def _wait_for_first_selector(page: "Page", selectors: list[str], timeout: int) -> None:
    """
    A helper for Playwright that waits for the first selector in a list to become visible.
    """
    tasks = [asyncio.create_task(page.wait_for_selector(selector, state="visible", timeout=timeout)) for selector in selectors]
    try:
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        if done:
            await done.pop()
    except asyncio.CancelledError:
        for task in tasks:
            task.cancel()
        raise


async def _fetch_html_playwright(url: str, wait_for_selectors: list[str] | None = None, debug: bool = False) -> str:
    """Fetches fully rendered HTML using a headless browser."""
    try:
        from playwright.async_api import Error as PlaywrightError
        from playwright.async_api import TimeoutError, async_playwright
    except ImportError:
        error_message = (
            'Playwright is not installed, but is required for the --render-js flag.\nPlease install it with: pip install "web2llm[js]"'
        )
        raise ImportError(error_message)

    logger.debug(f"Using Playwright to fetch and render {url}")
    BROWSER_TIMEOUT = 30000
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT)

            if wait_for_selectors:
                try:
                    await _wait_for_first_selector(page, wait_for_selectors, BROWSER_TIMEOUT)
                except TimeoutError:
                    logger.debug(f"Timed out waiting for selectors: {wait_for_selectors}")
                    logger.warning(f"Timed out waiting for content selectors on {url}. Content may be incomplete.")
            content = await page.content()
            await browser.close()
            return content
    except PlaywrightError as e:
        if "Executable doesn't exist" in e.message:
            error_message = "Playwright browser binaries not found.\nPlease run `playwright install` to download them."
            raise RuntimeError(error_message) from e
        raise IOError(f"A browser automation error occurred while fetching '{url}': {e}")
    except Exception as e:
        raise IOError(f"Network or page load error fetching URL '{url}': {e}")


async def fetch_html(url: str, render_js: bool = False, wait_for_selectors: list[str] | None = None, debug: bool = False) -> str:
    """
    Public dispatcher for fetching HTML, choosing the method based on `render_js`.
    """
    if render_js:
        return await _fetch_html_playwright(url, wait_for_selectors, debug)
    else:
        return await _fetch_html_httpx(url, debug)


# --- Other Fetching Utilities ---


async def fetch_json(url: str, debug: bool = False) -> dict:
    """Fetches and parses JSON data from a URL asynchronously."""
    response = await _make_httpx_request(url, debug)
    try:
        return response.json()
    except ValueError:  # httpx raises ValueError for JSON decoding errors
        raise ValueError(f"Failed to decode JSON from API response at '{url}'.")


async def get_url_content_type(url: str, debug: bool = False) -> str | None:
    """Checks the Content-Type of a URL using a lightweight async HEAD request."""
    logger.debug(f"Making httpx HEAD request to {url}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.head(url, headers=REQUEST_HEADERS, timeout=10, follow_redirects=True)
            response.raise_for_status()
            return response.headers.get("Content-Type")
        except httpx.RequestError as e:
            logger.warning(f"Could not determine content type for {url}: {e}")
            return None


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


# A dedicated logger for the filesystem processing utility function.
fs_logger = logging.getLogger("web2llm.scrapers.fs_processor")


def process_directory(root_path: str, ignore_patterns: list[str], debug: bool = False) -> tuple[str, str]:
    """
    Walk a directory, creating a file tree and concatenating the content of text files,
    respecting gitignore-style patterns.
    """
    fs_logger.debug(f"Processing directory: {root_path}")
    fs_logger.debug(f"Using {len(ignore_patterns)} gitignore patterns.")

    file_tree_lines = []
    concatenated_content_parts = []
    root = Path(root_path)

    spec = pathspec.PathSpec.from_lines("gitwildmatch", ignore_patterns)
    all_files = [p for p in root.rglob("*") if p.is_file()]
    matched_files = [f for f in all_files if not spec.match_file(str(f.relative_to(root)))]

    fs_logger.debug(f"Found {len(all_files)} total files. Matched {len(matched_files)} files after filtering.")

    seen_dirs = set()
    for file_path in sorted(matched_files):
        relative_path = file_path.relative_to(root)
        for parent in reversed(list(relative_path.parents)[:-1]):
            if parent not in seen_dirs:
                depth = len(parent.parts) - 1
                indent = "    " * depth
                file_tree_lines.append(f"{indent}|-- {parent.name}/")
                seen_dirs.add(parent)

        depth = len(relative_path.parts) - 1
        indent = "    " * depth
        file_tree_lines.append(f"{indent}|-- {relative_path.name}")

        if is_likely_text_file(file_path):
            fs_logger.debug(f"  - Reading text file: {relative_path}")
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                lang = LANGUAGE_MAP.get(file_path.suffix.lower(), "text")
                if file_path.name.lower() in LANGUAGE_MAP:
                    lang = LANGUAGE_MAP[file_path.name.lower()]

                relative_file_path_str = str(relative_path).replace("\\", "/")
                concatenated_content_parts.append(f"\n---\n\n### `{relative_file_path_str}`\n\n```{lang}\n{content}\n```\n")
            except Exception as e:
                fs_logger.warning(f"Could not read file {file_path}: {e}")
        else:
            fs_logger.debug(f"  - Skipping binary file: {relative_path}")

    fs_logger.debug(f"Generated file tree with {len(file_tree_lines)} lines.")
    return "\n".join(file_tree_lines), "".join(concatenated_content_parts)
