"""Common utility functions, mostly for network requests."""

import sys

import requests

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def fetch_html(url: str) -> str:
    """Fetches the HTML content of a given URL."""
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        raise IOError(f"Network error fetching URL '{url}': {e}")


def fetch_json(url: str) -> dict:
    """Fetches and parses JSON data from a URL."""
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise IOError(f"Network error fetching API '{url}': {e}")
    except requests.exceptions.JSONDecodeError:
        raise ValueError(f"Failed to decode JSON from API response at '{url}'.")


def get_url_content_type(url: str) -> str | None:
    """Checks the Content-Type of a URL using a lightweight HEAD request."""
    try:
        response = requests.head(url, headers=REQUEST_HEADERS, timeout=10, allow_redirects=True)
        response.raise_for_status()
        return response.headers.get("Content-Type")
    except requests.exceptions.RequestException as e:
        print(f"Warning: Could not determine content type for {url}: {e}", file=sys.stderr)
        return None
