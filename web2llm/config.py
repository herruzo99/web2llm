"""
Central configuration for scrapers.
"""

# Configuration for GitHub and local folder scrapers.
# Used to ignore common clutter and binary files.
CODE_IGNORE_CONFIG = {
    "directories": [
        ".git",
        ".github",
        ".vscode",
        ".idea",
        "__pycache__",
        "node_modules",
        "vendor",
        "target",
        "build",
        "dist",
        "venv",
        "env",
        ".cache",
        "docs",
    ],
    "filenames": [
        # Common metadata and config files
        ".gitignore",
        ".editorconfig",
        ".ds_store",
        "thumbs.db",
        # Lock files
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "poetry.lock",
        "pipfile.lock",
        "cargo.lock",
        "composer.lock",
        "gemfile.lock",
        "go.sum",
        # Common docs (can be overridden with --include-dirs)
        "license",
        "license.md",
        "license.txt",
        "contributing.md",
        "contributors.md",
        "code_of_conduct.md",
        "security.md",
        "changelog.md",
        "history.md",
        "authors.md",
    ],
    "extensions": [
        # Compiled files, logs, and other non-source artifacts
        ".log",
        ".tmp",
        ".swp",
        ".swo",
        ".env",
        ".pyc",
        ".pyo",
        ".o",
        ".so",
        ".dll",
        ".exe",
        ".class",
        ".jar",
        ".deb",
        ".rpm",
        # Media files
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".svg",
        ".mp4",
        ".mp3",
        ".mov",
        ".wav",
        ".ico",
    ],
}

# Configuration for the generic web scraper.
WEB_SCRAPER_CONFIG = {
    # CSS selectors to find the main content of a page, in order of priority.
    "main_content_selectors": [
        "main .md-content",
        "main.VPContent",
        "main#content",
        "main article",
        'div[role="main"]',
        "div.book",
        "div.body",
        "article",
        "main",
        "div#main",
        "div.main-content",
        "div#content",
        "div.content",
    ],
    # CSS selectors to find navigation elements for extracting site structure.
    "nav_selectors": [
        'div[role="navigation"]',
        "nav.md-nav--primary",
        "aside.VPSidebar",
        "nav.sidebar-container",
        "aside.theme-doc-sidebar-container-mobile",
        "div.toc",
        'nav[aria-label="Main"]',
        "nav#main-nav",
        ".bd-sidebar-primary",
        "nav#bd-docs-nav",
        "div.wy-menu-vertical",
        'div[class*="sidebar"]',
        'div[id*="sidebar"]',
        "nav",
    ],
}
