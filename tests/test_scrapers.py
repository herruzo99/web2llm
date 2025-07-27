import pytest
from web_to_llm_pkg.scrapers import LocalFolderScraper, GitHubScraper, GenericScraper, PDFScraper
from unittest.mock import patch, MagicMock

def run_scraper_on_html(mocker, html: str, url: str) -> str:
    """Mocks fetch_html and runs the scraper on the provided HTML."""
    mocker.patch('web_to_llm_pkg.scrapers.generic_scraper.fetch_html', return_value=html)
    scraper = GenericScraper(url)
    markdown, _ = scraper.scrape()
    return markdown


# --- LocalFolderScraper Tests ---

def test_local_folder_scraper_captures_all_files_by_default(temp_project_dir):
    """
    Check if the scraper correctly finds and includes all relevant files
    when no include/exclude filters are applied.
    """
    scraper = LocalFolderScraper(str(temp_project_dir), "", "")
    markdown, _ = scraper.scrape()

    assert "### `README.md`" in markdown
    assert "### `src/main.py`" in markdown
    assert "### `src/utils.py`" in markdown
    # .gitignore is in the default ignore list in config.py
    assert "### `.gitignore`" not in markdown
    # docs is also in the default ignore list
    assert "### `docs/guide.md`" not in markdown

def test_local_folder_scraper_respects_include_dirs(temp_project_dir):
    """
    Verify that when --include-dirs is used, only files from that
    directory are included in the output.
    """
    scraper = LocalFolderScraper(str(temp_project_dir), "src", "")
    markdown, _ = scraper.scrape()

    assert "### `src/main.py`" in markdown
    assert "### `src/utils.py`" in markdown
    assert "### `README.md`" not in markdown
    assert "### `docs/guide.md`" not in markdown

def test_local_folder_scraper_respects_exclude_dirs(temp_project_dir):
    """
    Ensure the scraper properly excludes directories specified
    in the --exclude-dirs argument.
    """
    # Let's add 'docs' back in for this test by overriding the default exclusion.
    # We can do this by creating a custom scraper instance, but for this test, let's assume
    # the user is running from a context where 'docs' isn't ignored by default.
    # For a real test, we would patch the config.
    # A simpler way: we'll just test excluding something not in the default ignore list.
    # Let's create a new dir.
    (temp_project_dir / "data").mkdir()
    (temp_project_dir / "data" / "file.csv").write_text("a,b,c")

    scraper = LocalFolderScraper(str(temp_project_dir), "", "data,src")
    markdown, _ = scraper.scrape()

    assert "### `README.md`" in markdown
    assert "### `src/main.py`" not in markdown
    assert "### `data/file.csv`" not in markdown

# --- GitHubScraper Tests ---

def test_github_scraper_assembles_correct_markdown(mocker, temp_project_dir, mock_github_api_response):
    """
    Test the full flow of the GitHub scraper: API call, git clone (mocked),
    and markdown generation.
    """
    # FIX: Patch the function where it's used (in the github_scraper module)
    mocker.patch('web_to_llm_pkg.scrapers.github_scraper.fetch_json', return_value=mock_github_api_response)

    # These mocks were correct, but let's make the git one more robust
    mock_clone = mocker.patch('git.Repo.clone_from')
    mocker.patch('web_to_llm_pkg.scrapers.github_scraper._process_directory',
                 return_value=("file_tree_placeholder", "concatenated_content_placeholder"))


    scraper = GitHubScraper("https://github.com/test-owner/test-repo", "", "")
    markdown, _ = scraper.scrape()

    # Add an assertion to make sure our mock was called correctly
    mock_clone.assert_called_once()
    assert 'repo_name: "test-owner/test-repo"' in markdown
    assert 'description: "A test repository for scraping."' in markdown
    assert "## Repository File Tree" in markdown
    assert "file_tree_placeholder" in markdown
    assert "## File Contents" in markdown
    assert "concatenated_content_placeholder" in markdown


# --- GenericScraper Tests ---

def test_scraper_finds_main_content(mocker):
    """Test that the scraper correctly uses the primary content selectors."""
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
    """Test that the scraper falls back to main content if the fragment ID doesn't exist."""
    html = """
    <html><head><title>Test</title></head><body>
      <main><h1>Main Content</h1></main>
      <div id="real-id"><p>Some other content</p></div>
    </body></html>
    """
    markdown = run_scraper_on_html(mocker, html, "http://example.com#non-existent-id")
    assert "Main Content" in markdown
    assert "Some other content" not in markdown # It should not just grab everything

# We'll use parametrize to test many scenarios with one test function.
# Each tuple is (test_id, html_structure, url_fragment, expected_texts, forbidden_texts)
@pytest.mark.parametrize(
    "test_id, html, fragment, expected, forbidden",
    [
        (
            "h2_to_next_h2",
            """
            <h1>Title</h1>
            <h2 id="start">Section 1</h2><p>Content 1.</p>
            <h2 id="next">Section 2</h2><p>Content 2.</p>
            """,
            "#start",
            ["Section 1", "Content 1."],
            ["Section 2", "Content 2."],
        ),
        (
            "h2_to_higher_h1",
            """
            <h2 id="start">Section 1</h2><p>Content 1.</p>
            <div><p>Some more content.</p></div>
            <h1>Next Big Section</h1><p>Should not be here.</p>
            """,
            "#start",
            ["Section 1", "Content 1.", "Some more content."],
            ["Next Big Section"],
        ),
        (
            "h3_to_next_h3_or_h2",
            """
            <h2>Topic</h2>
            <h3 id="start">Detail A</h3><p>Text A.</p>
            <p>More Text A.</p>
            <h3>Detail B</h3><p>Text B.</p>
            <h2>Next Topic</h2>
            """,
            "#start",
            ["Detail A", "Text A.", "More Text A."],
            ["Detail B", "Next Topic"],
        ),
        (
            "capture_to_end_of_container",
            """
            <main>
                <h1>Title</h1>
                <h2 id="start">Last Section</h2>
                <p>Some content.</p>
                <p>Final paragraph.</p>
            </main>
            <footer>Footer here</footer>
            """,
            "#start",
            ["Last Section", "Some content.", "Final paragraph."],
            ["Title", "Footer here"],
        ),
        (
            "nested_stop_tag",
            """
            <h2 id="start">Section A</h2>
            <p>Content A.</p>
            <div>
                <p>Nested content.</p>
                <h2>This should stop the scraping</h2>
            </div>
            """,
            "#start",
            ["Section A", "Content A.", "Nested content."],
            ["This should stop the scraping"],
        ),
        (
            "target_is_a_div",
            """
            <p>Ignore this.</p>
            <div id="start">
                <h3>Div Title</h3>
                <p>Div content.</p>
            </div>
            <p>Also ignore this.</p>
            """,
            "#start",
            ["Div Title", "Div content."],
            ["Ignore this", "Also ignore this"],
        ),
        (
            "malformed_html_no_siblings",
            """
            <main>
                <h2 id="start">Section</h2><p>Content</p>
            </main>
            """,
            "#start",
            ["Section", "Content"],
            [],
        ),
    ],
)
def test_fragment_scraping_scenarios(mocker, test_id, html, fragment, expected, forbidden):
    """A single, powerful test for various fragment scraping edge cases."""
    url = f"http://example.com/{fragment}"
    
    # We'll use the HTML structure provided by the test case.
    # The <head> and <title> ensure the front matter is predictable.
    full_html = f"<html><head><title>Test Page</title></head><body>{html}</body></html>"
    markdown = run_scraper_on_html(mocker, full_html, url)

    # Split front matter from the content for more precise assertions.
    parts = markdown.split('---', 2)
    content = parts[2] if len(parts) > 2 else markdown

    for text in expected:
        assert text in content, f'"{text}" was expected but not found in test "{test_id}"'

    for text in forbidden:
        assert text not in content, f'"{text}" was forbidden but found in test "{test_id}"'
# --- PDFScraper Tests ---

def test_pdf_scraper_handles_local_file(mocker):
    """
    Test PDF scraper with a local file path. We'll mock pdfplumber
    to avoid dealing with actual PDF files in tests.
    """
    # A mock page object that pdfplumber would return
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "This is text from a PDF page."

    # A mock pdf object that `pdfplumber.open` would return
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.metadata = {"Title": "My Test PDF"}

    # The `with` statement support
    mock_pdf_open = mocker.patch('web_to_llm_pkg.scrapers.pdf_scraper.pdfplumber.open')
    mock_pdf_open.return_value.__enter__.return_value = mock_pdf

    mocker.patch('os.path.isfile', return_value=True)
    
    mocker.patch('builtins.open', mocker.mock_open(read_data=b"dummy data"))
    
    scraper = PDFScraper("/fake/path/document.pdf")
    markdown, _ = scraper.scrape()

    assert 'title: "My Test PDF"' in markdown
    assert 'source_path: "/fake/path/document.pdf"' in markdown
    assert "--- Page 1 ---" in markdown
    assert "This is text from a PDF page." in markdown