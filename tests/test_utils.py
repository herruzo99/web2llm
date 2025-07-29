from unittest.mock import AsyncMock

import httpx
import pytest

from web2llm.utils import fetch_html, fetch_json


@pytest.mark.asyncio
async def test_fetch_html_uses_httpx_by_default(mocker):
    """Verify fetch_html dispatcher calls the httpx helper when render_js is False."""
    mock_httpx = mocker.patch("web2llm.utils._fetch_html_httpx", new_callable=AsyncMock, return_value="httpx_content")
    mock_playwright = mocker.patch("web2llm.utils._fetch_html_playwright", new_callable=AsyncMock)

    content = await fetch_html("http://example.com", debug=False)

    assert content == "httpx_content"
    # Assert with positional arguments to match the actual call signature
    mock_httpx.assert_awaited_once_with("http://example.com", False)
    mock_playwright.assert_not_awaited()


@pytest.mark.asyncio
async def test_fetch_html_uses_playwright_when_render_js_is_true(mocker):
    """Verify fetch_html dispatcher calls the Playwright helper when render_js is True."""
    mock_httpx = mocker.patch("web2llm.utils._fetch_html_httpx", new_callable=AsyncMock)
    mock_playwright = mocker.patch("web2llm.utils._fetch_html_playwright", new_callable=AsyncMock, return_value="playwright_content")
    selectors = ["#main"]

    content = await fetch_html("http://example.com", render_js=True, wait_for_selectors=selectors, debug=True)

    assert content == "playwright_content"
    # Assert with positional arguments
    mock_playwright.assert_awaited_once_with("http://example.com", selectors, True)
    mock_httpx.assert_not_awaited()


@pytest.mark.asyncio
async def test_fetch_json_parses_response(mocker):
    """Verify fetch_json correctly uses the shared httpx helper and parses the response."""
    mock_response = httpx.Response(200, json={"key": "value"})
    mock_make_request = mocker.patch("web2llm.utils._make_httpx_request", new_callable=AsyncMock, return_value=mock_response)

    data = await fetch_json("http://api.example.com", debug=True)

    assert data == {"key": "value"}
    # Assert with positional arguments
    mock_make_request.assert_awaited_once_with("http://api.example.com", True)


@pytest.mark.asyncio
async def test_fetch_json_raises_for_invalid_json(mocker):
    """Verify fetch_json raises a ValueError on malformed JSON content."""
    mock_response = httpx.Response(200, text="not-json-at-all")
    mocker.patch("web2llm.utils._make_httpx_request", new_callable=AsyncMock, return_value=mock_response)

    with pytest.raises(ValueError, match="Failed to decode JSON"):
        await fetch_json("http://api.example.com")
