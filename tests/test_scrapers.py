from unittest.mock import MagicMock

import pytest

from web2llm.scrapers import (
    GenericScraper,
    GitHubScraper,
    LocalFolderScraper,
    PDFScraper,
)


def run_scraper_on_html(mocker, html: str, url: str) -> str:
    """Helper to mock fetch_html and run the GenericScraper."""
    mocker.patch("web2llm.scrapers.generic_scraper.fetch_html", return_value=html)
    scraper = GenericScraper(url)
    markdown, _ = scraper.scrape()
    return markdown


# --- LocalFolderScraper Tests ---


def test_local_folder_scraper_captures_all_files_by_default(temp_project_dir):
    scraper = LocalFolderScraper(str(temp_project_dir), "", "")
    markdown, _ = scraper.scrape()

    assert "### `README.md`" in markdown
    assert "### `src/main.py`" in markdown
    assert "### `src/utils.py`" in markdown
    # .gitignore and docs are in the default ignore list
    assert "### `.gitignore`" not in markdown
    assert "### `docs/guide.md`" not in markdown


def test_local_folder_scraper_respects_include_dirs(temp_project_dir):
    scraper = LocalFolderScraper(str(temp_project_dir), "src", "")
    markdown, _ = scraper.scrape()

    assert "### `src/main.py`" in markdown
    assert "### `src/utils.py`" in markdown
    assert "### `README.md`" not in markdown


def test_local_folder_scraper_respects_exclude_dirs(temp_project_dir):
    scraper = LocalFolderScraper(str(temp_project_dir), "", "src")
    markdown, _ = scraper.scrape()

    assert "### `README.md`" in markdown
    assert "### `src/main.py`" not in markdown
    assert "### `src/utils.py`" not in markdown


def test_local_folder_scraper_respects_exclude_dirs_regex(temp_project_dir):
    # Exclude any directory starting with 'd' or 's'
    scraper = LocalFolderScraper(str(temp_project_dir), "", "^(d|s).*")
    markdown, _ = scraper.scrape()

    assert "### `README.md`" in markdown
    assert "### `src/main.py`" not in markdown
    assert "### `docs/guide.md`" not in markdown


def test_local_folder_scraper_invalid_regex_raises_error(temp_project_dir):
    with pytest.raises(ValueError, match="Invalid regex pattern"):
        LocalFolderScraper(str(temp_project_dir), "", "[invalid-regex")


def test_local_folder_scraper_includes_all_files_with_flag(temp_project_dir):
    scraper = LocalFolderScraper(str(temp_project_dir), "", "", include_all=True)
    markdown, _ = scraper.scrape()

    assert "### `README.md`" in markdown
    assert "### `src/main.py`" in markdown
    assert "### `src/utils.py`" in markdown
    # .gitignore and docs should now be included
    assert "### `.gitignore`" in markdown
    assert "### `docs/guide.md`" in markdown


def test_local_folder_scraper_with_include_all_respects_exclude_dirs(temp_project_dir):
    scraper = LocalFolderScraper(str(temp_project_dir), "", "docs", include_all=True)
    markdown, _ = scraper.scrape()

    assert "### `README.md`" in markdown
    assert "### `.gitignore`" in markdown  # included via --include-all
    assert "### `src/main.py`" in markdown
    assert "### `docs/guide.md`" not in markdown  # excluded via --exclude-dirs


# --- GitHubScraper Tests ---


def test_github_scraper_assembles_correct_markdown(mocker, mock_github_api_response):
    mocker.patch(
        "web2llm.scrapers.github_scraper.fetch_json",
        return_value=mock_github_api_response,
    )
    mock_clone = mocker.patch("git.Repo.clone_from")
    mocker.patch(
        "web2llm.scrapers.github_scraper._process_directory",
        return_value=("file_tree_placeholder", "concatenated_content_placeholder"),
    )

    scraper = GitHubScraper("https://github.com/test-owner/test-repo", "", "")
    markdown, _ = scraper.scrape()

    mock_clone.assert_called_once()
    assert 'repo_name: "test-owner/test-repo"' in markdown
    assert 'description: "A test repository for scraping."' in markdown
    assert "## Repository File Tree" in markdown
    assert "file_tree_placeholder" in markdown
    assert "## File Contents" in markdown
    assert "concatenated_content_placeholder" in markdown


# --- GenericScraper Tests ---


def test_scraper_finds_main_content(mocker):
    html = """
    <html><head><title>Test</title></head><body>
      <nav>ignore this</nav>
      <main><h1>Main Content</h1><p>This is it.</p></main>
      <footer>ignore this too</footer>
    </body></html>
    """
    markdown = run_scraper_on_html(mocker, html, "http://example.com")
    assert "Main Content" in markdown
    assert "This is it" in markdown
    assert "ignore this" not in markdown


def test_scraper_handles_missing_fragment(mocker):
    html = """
    <html><head><title>Test</title></head><body>
      <main><h1>Main Content</h1></main>
      <div id="real-id"><p>Some other content</p></div>
    </body></html>
    """
    markdown = run_scraper_on_html(mocker, html, "http://example.com#non-existent-id")
    assert "Main Content" in markdown
    assert "Some other content" not in markdown


@pytest.mark.parametrize(
    "test_id, html, fragment, expected, forbidden",
    [
        (
            "h2_to_next_h2",
            """<h1>Title</h1><h2 id="start">Section 1</h2><p>Content 1.</p><h2 id="next">Section 2</h2><p>Content 2.</p>""",
            "#start",
            ["Section 1", "Content 1."],
            ["Section 2", "Content 2."],
        ),
        (
            "h2_to_higher_h1",
            """<h2 id="start">Section 1</h2><p>Content 1.</p><div><p>Some more content.</p></div><h1>Next Big Section</h1>""",
            "#start",
            ["Section 1", "Content 1.", "Some more content."],
            ["Next Big Section"],
        ),
        (
            "h3_to_next_h3_or_h2",
            """<h2>Topic</h2><h3 id="start">Detail A</h3><p>Text A.</p><p>More Text A.</p><h3>Detail B</h3><h2>Next Topic</h2>""",
            "#start",
            ["Detail A", "Text A.", "More Text A."],
            ["Detail B", "Next Topic"],
        ),
        (
            "capture_to_end_of_container",
            """<main><h1>Title</h1><h2 id="start">Last Section</h2><p>Some content.</p></main><footer>Footer here</footer>""",
            "#start",
            ["Last Section", "Some content."],
            ["Title", "Footer here"],
        ),
        (
            "nested_stop_tag",
            """<h2 id="start">Section A</h2><p>Content A.</p><div><p>Nested content.</p><h2>This stops it</h2></div>""",
            "#start",
            ["Section A", "Content A.", "Nested content."],
            ["This stops it"],
        ),
        (
            "target_is_a_div",
            """<p>Ignore this.</p><div id="start"><h3>Div Title</h3><p>Div content.</p></div><p>Also ignore this.</p>""",
            "#start",
            ["Div Title", "Div content."],
            ["Ignore this", "Also ignore this"],
        ),
    ],
)
def test_fragment_scraping_scenarios(mocker, test_id, html, fragment, expected, forbidden):
    url = f"http://example.com/{fragment}"
    full_html = f"<html><head><title>Test Page</title></head><body>{html}</body></html>"
    markdown = run_scraper_on_html(mocker, full_html, url)

    # Split front matter from the content for more precise assertions
    content = markdown.split("---", 2)[2]

    for text in expected:
        assert text in content, f'"{text}" was expected but not found in test "{test_id}"'

    for text in forbidden:
        assert text not in content, f'"{text}" was forbidden but found in test "{test_id}"'


# --- PDFScraper Tests ---


def test_pdf_scraper_handles_local_file(mocker):
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "This is text from a PDF page."

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.metadata = {"Title": "My Test PDF"}

    mock_pdf_open = mocker.patch("web2llm.scrapers.pdf_scraper.pdfplumber.open")
    mock_pdf_open.return_value.__enter__.return_value = mock_pdf

    mocker.patch("os.path.isfile", return_value=True)
    mocker.patch("builtins.open", mocker.mock_open(read_data=b"dummy pdf data"))

    scraper = PDFScraper("/fake/path/document.pdf")
    markdown, _ = scraper.scrape()

    assert 'title: "My Test PDF"' in markdown
    assert 'source_path: "/fake/path/document.pdf"' in markdown
    assert "--- Page 1 ---" in markdown
    assert "This is text from a PDF page." in markdown
