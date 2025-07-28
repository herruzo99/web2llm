from unittest.mock import MagicMock

import pytest

from web2llm.scrapers import GenericScraper, GitHubScraper, PDFScraper
from web2llm.scrapers.github_scraper import _process_directory

# --- Filesystem Scraper Logic Tests (`_process_directory`) ---
# This function is the core of both LocalFolderScraper and GitHubScraper,
# so we test it thoroughly here in isolation.


def test_fs_scraper_with_default_ignores(project_structure):
    """
    Given a standard set of ignore patterns, verify that the right files
    are excluded from the output.
    """
    ignore_patterns = [
        "__pycache__/",
        "node_modules/",
        "*.log",
        "*.lock",
        "*.png",
        "LICENSE",
    ]
    tree, content = _process_directory(str(project_structure), ignore_patterns)

    # Must be included
    assert "### `README.md`" in content
    assert "### `main.py`" in content
    assert "### `src/app.py`" in content
    assert "### `components/button.js`" in content

    # Must be excluded
    assert "app.log" not in content
    assert "poetry.lock" not in content
    assert "image.png" not in content
    assert "LICENSE" not in content
    assert "node_modules" not in tree
    assert "__pycache__" not in tree
    assert "app.cpython-311.pyc" not in content


def test_fs_scraper_with_project_overrides(project_structure):
    """
    Simulates a project config that adds new ignore rules.
    """
    # Defaults plus a project-specific rule to ignore all JS files and the docs folder.
    ignore_patterns = [
        "__pycache__/",
        "node_modules/",
        "*.log",
        "*.lock",
        "docs/",
        "*.js",
    ]
    tree, content = _process_directory(str(project_structure), ignore_patterns)

    # Must be included
    assert "### `README.md`" in content
    assert "### `main.py`" in content

    # Must be excluded
    assert "docs/" not in tree
    assert "index.md" not in content
    assert "button.js" not in content


def test_fs_scraper_with_negation_pattern(project_structure):
    """
    Tests that a negation pattern (`!`) correctly re-includes a file that
    would have been ignored by a broader rule.
    """
    # Ignore all markdown, but then re-include the main README.
    ignore_patterns = ["*.md", "!README.md"]

    tree, content = _process_directory(str(project_structure), ignore_patterns)

    # Must be included
    assert "### `README.md`" in content
    assert "### `main.py`" in content  # Should not be affected

    # Must be excluded
    assert "docs/index.md" not in content


def test_fs_scraper_with_directory_negation(project_structure):
    """
    Tests re-including a whole directory that would otherwise be ignored.
    """
    # Ignore the components directory, but re-include a specific file from it.
    ignore_patterns = ["components/", "!components/button.js"]

    tree, content = _process_directory(str(project_structure), ignore_patterns)

    assert "### `components/button.js`" in content
    assert "|-- components/" in tree  # The directory should appear in the tree
    assert "|-- button.js" in tree


def test_fs_scraper_empty_ignore_list_includes_all_text(project_structure):
    """
    If the ignore list is empty, all readable text files should be included.
    """
    ignore_patterns = []  # No ignores
    tree, content = _process_directory(str(project_structure), ignore_patterns)

    # Everything that is text should be here
    assert "### `README.md`" in content
    assert "### `main.py`" in content
    assert "### `src/app.py`" in content
    assert "### `.gitignore`" in content
    assert "### `poetry.lock`" in content
    assert "### `docs/index.md`" in content
    assert "### `LICENSE`" in content
    assert "### `node_modules/react/index.js`" in content

    # Binaries and non-text files should still be excluded by `is_likely_text_file`
    assert "image.png" not in content
    assert "app.cpython-311.pyc" not in content


def test_fs_scraper_file_tree_structure(project_structure):
    """
    Verifies the visual hierarchy of the generated file tree.
    """
    # Ignore node_modules and pycache to simplify the tree
    ignore_patterns = ["node_modules/", "__pycache__/"]
    tree, _ = _process_directory(str(project_structure), ignore_patterns)

    # We check for the presence of expected lines rather than exact string matching
    # to make the test less brittle to ordering differences.
    expected_lines = [
        "|-- README.md",
        "|-- app.log",
        "|-- components/",
        "|-- button.js",
        "|-- docs/",
        "|-- image.png",
        "|-- index.md",
        "|-- .gitignore",
        "|-- LICENSE",
        "|-- main.py",
        "|-- poetry.lock",
        "|-- src/",
        "|-- __init__.py",
        "|-- app.py",
        "|-- utils.py",
    ]
    for line in expected_lines:
        assert line in tree


# --- GitHubScraper Tests ---


def test_github_scraper_assembles_correct_markdown(mocker, mock_github_api_response, default_config):
    """
    Verify the GitHub scraper correctly calls its dependencies and assembles
    the final markdown output from the processed parts.
    """
    # Mock dependencies
    mocker.patch("web2llm.scrapers.github_scraper.fetch_json", return_value=mock_github_api_response)
    mocker.patch("git.Repo.clone_from")
    mock_process_dir = mocker.patch(
        "web2llm.scrapers.github_scraper._process_directory",
        return_value=("file_tree_placeholder", "concatenated_content_placeholder"),
    )

    scraper = GitHubScraper("https://github.com/test-owner/test-repo", default_config)
    markdown, _ = scraper.scrape()

    # Assertions
    mock_process_dir.assert_called_once_with(mocker.ANY, default_config["fs_scraper"]["ignore_patterns"])
    assert 'repo_name: "test-owner/test-repo"' in markdown
    assert 'description: "A test repository for scraping."' in markdown
    assert "## Repository File Tree" in markdown
    assert "file_tree_placeholder" in markdown
    assert "## File Contents" in markdown
    assert "concatenated_content_placeholder" in markdown


# --- GenericScraper Tests ---


def run_scraper_on_html(mocker, html: str, url: str, config: dict) -> str:
    """Helper to mock fetch_html and run the GenericScraper."""
    mocker.patch("web2llm.scrapers.generic_scraper.fetch_html", return_value=html)
    scraper = GenericScraper(url, config)
    markdown, _ = scraper.scrape()
    return markdown


def test_scraper_finds_main_content(mocker, default_config):
    html = """
    <html><head><title>Test</title></head><body>
      <nav>ignore this</nav>
      <main><h1>Main Content</h1><p>This is it.</p></main>
      <footer>ignore this too</footer>
    </body></html>
    """
    markdown = run_scraper_on_html(mocker, html, "http://example.com", default_config)
    assert "Main Content" in markdown
    assert "This is it" in markdown
    assert "ignore this" not in markdown


def test_scraper_handles_missing_fragment(mocker, default_config):
    html = """
    <html><head><title>Test</title></head><body>
      <main><h1>Main Content</h1></main>
      <div id="real-id"><p>Some other content</p></div>
    </body></html>
    """
    markdown = run_scraper_on_html(mocker, html, "http://example.com#non-existent-id", default_config)
    assert "Main Content" in markdown
    assert "Some other content" not in markdown


@pytest.mark.parametrize(
    "test_id, html, fragment, expected, forbidden",
    [
        (
            "h2_to_next_h2",
            """<h1>Title</h1><h2 id="start">Section 1</h2><p>Content 1.</p><h2 id="next">Section 2</h2>""",
            "#start",
            ["Section 1", "Content 1."],
            ["Section 2"],
        ),
        (
            "h3_to_next_h3_or_h2",
            """<h2>Topic</h2><h3 id="start">Detail A</h3><p>Text A.</p><h3>Detail B</h3>""",
            "#start",
            ["Detail A", "Text A."],
            ["Detail B"],
        ),
        (
            "capture_to_end_of_container",
            """<main><h2 id="start">Last Section</h2><p>Content.</p></main><footer>Footer</footer>""",
            "#start",
            ["Last Section", "Content."],
            ["Footer"],
        ),
        (
            "target_is_a_div",
            """<p>Ignore.</p><div id="start"><h3>Div Title</h3></div><p>Also ignore.</p>""",
            "#start",
            ["Div Title"],
            ["Ignore."],
        ),
    ],
)
def test_fragment_scraping_scenarios(mocker, test_id, html, fragment, expected, forbidden, default_config):
    url = f"http://example.com/{fragment}"
    full_html = f"<html><body>{html}</body></html>"
    markdown = run_scraper_on_html(mocker, full_html, url, default_config)

    content = markdown.split("---", 2)[2]

    for text in expected:
        assert text in content, f'"{text}" was expected but not found in test "{test_id}"'
    for text in forbidden:
        assert text not in content, f'"{text}" was forbidden but found in test "{test_id}"'


# --- PDFScraper Tests ---


def test_pdf_scraper_handles_local_file(mocker):
    """
    Verifies that the PDF scraper correctly processes a mocked local file,
    extracting text and metadata.
    """
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "This is text from a PDF page."

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.metadata = {"Title": "My Test PDF"}

    # Mock the pdfplumber.open context manager
    mock_pdf_open = mocker.patch("web2llm.scrapers.pdf_scraper.pdfplumber.open")
    mock_pdf_open.return_value.__enter__.return_value = mock_pdf

    # Mock the filesystem checks and the actual file open call
    mocker.patch("os.path.isfile", return_value=True)
    mocker.patch("builtins.open", mocker.mock_open(read_data=b"dummy-pdf-bytes"))

    # The PDF scraper does not use the config, so we pass an empty dict
    scraper = PDFScraper("/fake/path/document.pdf", config={})
    markdown, _ = scraper.scrape()

    assert 'title: "My Test PDF"' in markdown
    assert 'source_path: "/fake/path/document.pdf"' in markdown
    assert "--- Page 1 ---" in markdown
    assert "This is text from a PDF page." in markdown
