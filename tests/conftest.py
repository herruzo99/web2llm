import importlib.resources as pkg_resources
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def project_structure(tmp_path: Path) -> Path:
    """
    Creates a more complex temporary directory structure for testing filesystem scrapers.
    """
    root = tmp_path / "test-project"
    root.mkdir()

    # Top-level files
    (root / "README.md").write_text("# Test Project")
    (root / "main.py").write_text("print('main')")
    (root / ".gitignore").write_text("*.log\n.env\n")
    (root / "app.log").write_text("some log data")
    (root / "poetry.lock").write_text("# lockfile")
    (root / "LICENSE").write_text("MIT License")

    # Source directory
    src_dir = root / "src"
    src_dir.mkdir()
    (src_dir / "app.py").write_text("import utils")
    (src_dir / "utils.py").write_text("# utilities")
    (src_dir / "__init__.py").write_text("")

    # Build artifacts in source
    pycache_dir = src_dir / "__pycache__"
    pycache_dir.mkdir()
    # HACK: Write invalid UTF-8 bytes to ensure is_likely_text_file() returns False.
    # This simulates a real binary file.
    (pycache_dir / "app.cpython-311.pyc").write_bytes(b"\x03\xf3\r\n")

    # Docs directory
    docs_dir = root / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Docs")
    (docs_dir / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n")  # PNG header

    # Nested project/module
    nested_dir = root / "components"
    nested_dir.mkdir()
    (nested_dir / "button.js").write_text("export default Button;")

    # Ignored by default
    node_modules = root / "node_modules"
    node_modules.mkdir()
    (node_modules / "react").mkdir()
    (node_modules / "react" / "index.js").write_text("// react source")

    return root


@pytest.fixture
def default_config() -> dict:
    """
    Provides a real, parsed copy of the default configuration settings.
    This ensures tests run against the production default config.
    """
    with pkg_resources.open_text("web2llm", "default_config.yaml") as f:
        config = yaml.safe_load(f)
    return config


@pytest.fixture
def project_config_file(project_structure: Path) -> Path:
    """Creates a project-specific .web2llm.yaml file."""
    config_path = project_structure / ".web2llm.yaml"
    config_data = {
        "fs_scraper": {
            # Add a new rule and override a default
            "ignore_patterns": ["docs/", "*.js"]
        }
    }
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)
    return config_path


@pytest.fixture
def mock_github_api_response():
    """Provides a mock of the GitHub API response for a repository."""
    return {
        "full_name": "test-owner/test-repo",
        "html_url": "https://github.com/test-owner/test-repo",
        "description": "A test repository for scraping.",
        "language": "Python",
        "stargazers_count": 123,
        "forks_count": 45,
        "license": {"name": "MIT License"},
        "scraped_at": "2023-10-27T10:00:00Z",
    }
