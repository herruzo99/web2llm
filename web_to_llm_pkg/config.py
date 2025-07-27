"""
Central configuration for the web_to_llm package.

This module holds configuration data, such as CSS selectors and ignore lists,
to allow for easy modification of scraper behavior without changing core logic.
"""

GITHUB_SCRAPER_IGNORE_CONFIG = {
    "directories": [
        ".git", ".github", ".vscode", ".idea", "__pycache__", "node_modules",
        "vendor", "target", "build", "dist", "venv", "env", ".cache", "docs",
    ],
    "filenames": [
        "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
        "pipfile.lock", "cargo.lock", "composer.lock", "gemfile.lock", "go.sum",
        "license", "license.md", "license.txt", "contributing.md",
        "contributors.md", "code_of_conduct.md", "security.md", "changelog.md",
        "history.md", "authors.md", ".editorconfig", ".ds_store", "thumbs.db",
    ],
    "extensions": [
        ".log", ".tmp", ".swp", ".swo", ".env", ".pyc", ".pyo", ".o", ".so",
        ".dll", ".exe", ".class", ".jar", ".deb", ".rpm", ".png", ".jpg",
        ".jpeg", ".gif", ".webp", ".svg", ".mp4", ".mp3", ".mov", ".wav", ".ico",
    ]
}

WEB_SCRAPER_CONFIG = {
    "main_content_selectors": [
        'main .md-content', 'main.VPContent', 'main#content', 'main article',
        'div[role="main"]', 'div.book', 'div.body', 'article', 'main',
        'div#main', 'div.main-content', 'div#content', 'div.content',
    ],
    "nav_selectors": [
        'div[role="navigation"]', 'nav.md-nav--primary', 'aside.VPSidebar',
        'nav.sidebar-container', 'aside.theme-doc-sidebar-container-mobile',
        'div.toc', 'nav[aria-label="Main"]', 'nav#main-nav', '.bd-sidebar-primary',
        'nav#bd-docs-nav', 'div.wy-menu-vertical', 'div[class*="sidebar"]',
        'div[id*="sidebar"]', 'nav',
    ]
}