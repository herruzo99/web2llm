import os
from pathlib import Path
from unittest.mock import patch

from web2llm.config import load_and_merge_configs

# Mock the packaged default config to isolate tests from the actual file
MOCKED_DEFAULT_CONFIG = {
    "fs_scraper": {"ignore_patterns": ["default_ignore/", "*.log"]},
    "web_scraper": {"main_content_selectors": ["main"]},
}


@patch("web2llm.config.yaml.safe_load", return_value=MOCKED_DEFAULT_CONFIG)
@patch("importlib.resources.open_text")
def test_load_default_config_only(mock_open_text, mock_safe_load, tmp_path: Path):
    """
    Tests that only the default config is loaded when no project config exists.
    """
    # Run the test in a clean temporary directory
    os.chdir(tmp_path)

    config = load_and_merge_configs()

    mock_open_text.assert_called_once_with("web2llm", "default_config.yaml")
    assert config == MOCKED_DEFAULT_CONFIG
    assert "default_ignore/" in config["fs_scraper"]["ignore_patterns"]


@patch(
    "web2llm.config.yaml.safe_load",
    side_effect=[
        MOCKED_DEFAULT_CONFIG,
        {"fs_scraper": {"ignore_patterns": ["project_ignore/", "*.md"]}, "web_scraper": {"nav_selectors": ["nav"]}},
    ],
)
@patch("importlib.resources.open_text")
def test_load_and_merge_project_config(mock_open_text, mock_safe_load, tmp_path: Path):
    """
    Tests that a project's .web2llm.yaml is found and its settings are merged
    on top of the defaults.
    """
    # Create a dummy project config file
    (tmp_path / ".web2llm.yaml").write_text("dummy yaml")
    os.chdir(tmp_path)

    config = load_and_merge_configs()

    assert config is not None
    # Check that lists from the project config overwrite the defaults, which is the intended merge behavior.
    assert config["fs_scraper"]["ignore_patterns"] == ["project_ignore/", "*.md"]
    assert "default_ignore/" not in config["fs_scraper"]["ignore_patterns"]

    # Check that new keys are added
    assert config["web_scraper"]["nav_selectors"] == ["nav"]
    # Check that existing keys are preserved
    assert config["web_scraper"]["main_content_selectors"] == ["main"]
