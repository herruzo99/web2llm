import pytest
from pathlib import Path

@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """
    Creates a temporary directory structure that mimics a simple project.
    This is perfect for testing the LocalFolderScraper and for mocking
    the result of a git clone for the GitHubScraper.
    """
    project_root = tmp_path / "my-test-project"
    
    # Create a few source files
    src_dir = project_root / "src"
    src_dir.mkdir(parents=True)
    (src_dir / "main.py").write_text("print('hello world')")
    (src_dir / "utils.py").write_text("# Utility functions")

    # Add a docs folder, which we'll often want to exclude
    docs_dir = project_root / "docs"
    docs_dir.mkdir()
    (docs_dir / "guide.md").write_text("# How to use this project")

    # Add a common file to ignore
    (project_root / ".gitignore").write_text("*.pyc\n__pycache__/")
    
    # Add a file in the root
    (project_root / "README.md").write_text("# My Test Project")
    
    return project_root

@pytest.fixture
def mock_github_api_response():
    """
    Provides a mock of the GitHub API response for a repository.
    This saves us from making a real network call and keeps tests consistent.
    """
    return {
        "full_name": "test-owner/test-repo",
        "html_url": "https://github.com/test-owner/test-repo",
        "description": "A test repository for scraping.",
        "language": "Python",
        "stargazers_count": 123,
        "forks_count": 45,
        "license": {"name": "MIT License"},
        "scraped_at": "2023-10-27T10:00:00Z"
    }