"""
Custom exceptions for the web2llm library.
"""


class Web2LLMError(Exception):
    """Base exception for all errors raised by the web2llm library."""

    pass


class ContentNotFoundError(Web2LLMError):
    """
    Raised when a scraper fails to extract meaningful content.

    This can happen if CSS selectors don't match or if a page requires
    JavaScript rendering and was fetched statically. The error message provides
    guidance to the user.
    """

    pass
