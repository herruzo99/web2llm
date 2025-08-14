from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml

from web2llm.errors import ContentNotFoundError
from web2llm.scrapers import GenericScraper, GitHubScraper, LocalFolderScraper, PDFScraper
from web2llm.utils import process_directory


# --- Filesystem Scraper Logic Tests (`process_directory`) ---
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
    tree, content = process_directory(str(project_structure), ignore_patterns)
    assert "### `README.md`" in content
    assert "### `main.py`" in content
    assert "### `src/app.py`" in content
    assert "### `components/button.js`" in content
    assert "app.log" not in content
    assert "poetry.lock" not in content
    assert "image.png" not in content
    assert "LICENSE" not in content
    assert "node_modules" not in tree
    assert "__pycache__" not in tree
    assert "app.cpython-311.pyc" not in content


def test_fs_scraper_with_project_overrides(project_structure):
    """Simulates a project config that adds new ignore rules."""
    ignore_patterns = ["__pycache__/", "node_modules/", "*.log", "*.lock", "docs/", "*.js"]
    tree, content = process_directory(str(project_structure), ignore_patterns)
    assert "### `README.md`" in content and "### `main.py`" in content
    assert "docs/" not in tree and "index.md" not in content and "button.js" not in content


def test_fs_scraper_with_negation_pattern(project_structure):
    """Tests that a negation pattern (`!`) correctly re-includes a file."""
    ignore_patterns = ["*.md", "!README.md"]
    tree, content = process_directory(str(project_structure), ignore_patterns)
    assert "### `README.md`" in content and "### `main.py`" in content
    assert "docs/index.md" not in content


def test_fs_scraper_with_directory_negation(project_structure):
    """Tests re-including a whole directory that would otherwise be ignored."""
    ignore_patterns = ["components/", "!components/button.js"]
    tree, content = process_directory(str(project_structure), ignore_patterns)
    assert "### `components/button.js`" in content
    assert "|-- components/" in tree and "|-- button.js" in tree


def test_fs_scraper_empty_ignore_list_includes_all_text(project_structure):
    """If the ignore list is empty, all readable text files should be included."""
    ignore_patterns = []  # No ignores
    tree, content = process_directory(str(project_structure), ignore_patterns)
    assert "### `README.md`" in content
    assert "### `main.py`" in content
    assert "### `node_modules/react/index.js`" in content
    assert "image.png" not in content and "app.cpython-311.pyc" not in content


@pytest.mark.asyncio
async def test_local_folder_scraper_respects_gitignore(project_structure, default_config):
    """
    Verifies that the LocalFolderScraper automatically finds and applies
    rules from a .gitignore file in the target directory, in addition to default rules.
    """
    # The `project_structure` fixture creates a .gitignore with "*.log" and ".env".
    # It also creates `app.log` and `.env` files to be ignored.
    # The default_config fixture will provide rules to ignore `poetry.lock`.
    # The new default config change also ignores `.gitignore` itself.

    # Instantiate the scraper with the test project directory and default config.
    scraper = LocalFolderScraper(str(project_structure), default_config)

    # Run the scrape
    markdown_content, _ = await scraper.scrape()

    # Assert that file content blocks for ignored files are NOT present.
    # This is more robust than checking for substrings.

    # Ignored by project's .gitignore
    assert "### `app.log`" not in markdown_content
    assert "### `.env`" not in markdown_content

    # Ignored by default config
    assert "### `poetry.lock`" not in markdown_content

    # The .gitignore file itself should now be ignored by default
    assert "### `.gitignore`" not in markdown_content

    # Assert that expected files ARE present
    assert "### `README.md`" in markdown_content
    assert "### `main.py`" in markdown_content
    assert "### `src/app.py`" in markdown_content


# --- GitHubScraper Tests ---
@pytest.mark.asyncio
async def test_github_scraper_assembles_correct_markdown(mocker, mock_github_api_response, default_config):
    mocker.patch("web2llm.scrapers.github_scraper.fetch_json", new_callable=AsyncMock, return_value=mock_github_api_response)
    mocker.patch("git.Repo.clone_from")
    mock_process_dir = mocker.patch(
        "web2llm.scrapers.github_scraper.process_directory",
        return_value=("file_tree_placeholder", "concatenated_content_placeholder"),
    )
    scraper = GitHubScraper("https://github.com/test-owner/test-repo", default_config)
    await scraper.scrape()
    # After the change to add .gitignore patterns, the second argument to process_directory
    # will be a list containing the default patterns plus any from the (mocked) repo.
    # We assert that the call was made, without being overly specific about the combined list.
    mock_process_dir.assert_called_once()
    args, _ = mock_process_dir.call_args
    assert isinstance(args[1], list)  # The ignore patterns
    assert args[2] is False  # The debug flag


# --- GenericScraper Tests ---
async def run_scraper_on_html(mocker, html: str, url: str, config: dict) -> str:
    """Helper to mock fetch_html and run the GenericScraper."""
    mocker.patch("web2llm.scrapers.generic_scraper.fetch_html", new_callable=AsyncMock, return_value=html)
    scraper = GenericScraper(url, config)
    markdown, _ = await scraper.scrape()
    return markdown


@pytest.mark.asyncio
async def test_scraper_finds_main_content(mocker, default_config):
    html = """<html><body><main><h1>Main Content</h1><p>This is it.</p></main></body></html>"""
    markdown = await run_scraper_on_html(mocker, html, "http://example.com", default_config)
    assert "Main Content" in markdown and "This is it" in markdown


@pytest.mark.asyncio
async def test_scraper_raises_content_not_found_without_render_js(mocker, default_config):
    mocker.patch("web2llm.scrapers.generic_scraper.fetch_html", new_callable=AsyncMock, return_value="<html><body></body></html>")
    scraper = GenericScraper("http://example.com", {**default_config, "render_js": False})
    with pytest.raises(
        ContentNotFoundError,
        match="Main content found but empty. The page structure may be unsupported or the selectors in your config are incorrect.",
    ):
        await scraper.scrape()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_id, html, fragment, expected, forbidden",
    [
        (
            "h2_to_next_h2",
            """<h1>Title</h1><h2 id="start">Section 1</h2><p>Content 1.</p><h2 id="next">Section 2</h2>""",
            "#start",
            ["Section 1", "Content 1."],
            ["Section 2", "Title"],
        ),
        (
            "h3_to_next_h3_or_h2",
            """<h2>Topic</h2><h3 id="start">Detail A</h3><p>Text A.</p><h3>Detail B</h3>""",
            "#start",
            ["Detail A", "Text A."],
            ["Detail B", "Topic"],
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
        (
            "deeply_nested_id_on_heading",
            """<div><div class="sw"><div class="tw"><h2 id="start">Nested</h2></div>
            <div class="cb"><p>Content.</p></div></div><div class="ns"><h2>Next</h2></div></div>""",
            "#start",
            ["Nested", "Content."],
            ["Next"],
        ),
        (
            "stop_on_sibling_containing_heading",
            """<h3 id="start">A</h3><p>Content A.</p><div><h3>B</h3><p>Content B.</p></div>""",
            "#start",
            ["A", "Content A."],
            ["B"],
        ),
        (
            "id_on_inline_element",
            """<h2>T</h2><p>text <span id="start">keyword</span> inside.</p>""",
            "#start",
            ["keyword"],
            ["T", "text", "inside"],
        ),
    ],
)
async def test_fragment_scraping_scenarios(mocker, test_id, html, fragment, expected, forbidden, default_config):
    url = f"http://example.com/{fragment}"
    full_html = f"<html><body>{html}</body></html>"
    config = {**default_config, "debug": True}
    markdown = await run_scraper_on_html(mocker, full_html, url, config)
    content = markdown.split("---", 2)[-1]
    for text in expected:
        assert text in content, f'"{text}" was expected in test "{test_id}"'
    for text in forbidden:
        assert text not in content, f'"{text}" was forbidden in test "{test_id}"'


# --- PDFScraper Tests ---
@pytest.mark.asyncio
async def test_pdf_scraper_handles_local_file(mocker):
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "This is text from a PDF page."
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.metadata = {"Title": "My Test PDF"}
    mock_pdf_open = mocker.patch("web2llm.scrapers.pdf_scraper.pdfplumber.open")
    mock_pdf_open.return_value.__enter__.return_value = mock_pdf
    mocker.patch("os.path.isfile", return_value=True)
    mocker.patch("builtins.open", mocker.mock_open(read_data=b"dummy-pdf-bytes"))
    scraper = PDFScraper("/fake/path/document.pdf", config={})
    markdown, _ = await scraper.scrape()

    front_matter_str = markdown.split("---")[1]
    front_matter_data = yaml.safe_load(front_matter_str)

    assert front_matter_data["title"] == "My Test PDF"
    assert "--- Page 1 ---" in markdown


@pytest.mark.asyncio
async def test_pdf_scraper_handles_remote_arxiv_url(mocker):
    mock_response = AsyncMock()
    mock_response.content = b"dummy-pdf-bytes"
    mock_response.raise_for_status = MagicMock()
    mock_client_context = AsyncMock()
    mock_client_context.__aenter__.return_value.get.return_value = mock_response
    mocker.patch("httpx.AsyncClient", return_value=mock_client_context)
    arxiv_html = (
        '<html><h1 class="title">Title:My Arxiv Paper</h1><blockquote class="abstract">Abstract: This is the abstract.</blockquote></html>'
    )
    mock_fetch_html = mocker.patch("web2llm.scrapers.pdf_scraper.fetch_html", new_callable=AsyncMock, return_value=arxiv_html)
    mock_page = MagicMock(extract_text=lambda **kwargs: "PDF content")
    mock_pdf = MagicMock(pages=[mock_page], metadata={})
    mocker.patch("web2llm.scrapers.pdf_scraper.pdfplumber.open").return_value.__enter__.return_value = mock_pdf
    scraper = PDFScraper("https://arxiv.org/pdf/1234.5678.pdf", config={})
    markdown, _ = await scraper.scrape()

    front_matter_str = markdown.split("---")[1]
    front_matter_data = yaml.safe_load(front_matter_str)

    mock_fetch_html.assert_awaited_once_with("https://arxiv.org/abs/1234.5678.pdf", render_js=False, debug=False)
    assert front_matter_data["title"] == "My Arxiv Paper"
    assert front_matter_data["description"] == "This is the abstract."
    assert "PDF content" in markdown
