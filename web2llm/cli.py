import argparse
import asyncio
import logging
import sys

from .config import load_and_merge_configs
from .errors import ContentNotFoundError
from .output import save_outputs
from .scrapers import get_scraper

# Configure a module-level logger
logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(
        description="Scrape web content into clean Markdown, optimized for LLMs.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Examples:
  # Scrape a static HTML page quickly
  web2llm 'https://example.com' -o example-static

  # Scrape a JavaScript-heavy web application by rendering it in a headless browser
  web2llm 'https://react.dev' -o react-docs --render-js

  # Scrape a URL that serves a PDF without a .pdf extension
  web2llm 'https://example.com/get-report?id=123' -o my-report --check-content-type

  # Scrape core source code of a GitHub repo
  web2llm 'https://github.com/tiangolo/fastapi' -o fastapi-core --include 'fastapi/'""",
    )
    parser.add_argument("source", help="The URL or local file/folder path to process.")

    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="The base name for the output folder and files.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode for verbose, step-by-step output to stderr.",
    )

    # --- Web Scraper Options ---
    web_group = parser.add_argument_group("Web Scraper Options")
    web_group.add_argument(
        "--render-js",
        action="store_true",
        help="Render JavaScript on the page using a headless browser. Slower but necessary for single-page applications (SPAs).",
    )
    web_group.add_argument(
        "--check-content-type",
        action="store_true",
        help="Force a network request to check the page's Content-Type header. Use for URLs that serve PDFs without a .pdf extension.",
    )

    # --- Filesystem Scraper Options ---
    fs_group = parser.add_argument_group("Filesystem Scraper Options (GitHub & Local)")
    fs_group.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="A gitignore-style pattern to exclude. Can be used multiple times.",
    )
    fs_group.add_argument(
        "--include",
        action="append",
        default=[],
        help="A gitignore-style pattern to re-include files that would otherwise be ignored.",
    )
    fs_group.add_argument(
        "--include-all",
        action="store_true",
        help="Scrape all files, ignoring default, project-level, and .gitignore ignore patterns.",
    )

    args = parser.parse_args()

    # --- Setup Logging ---
    log_level = logging.DEBUG if args.debug else logging.INFO
    log_format = "[%(levelname)s] %(message)s"
    logging.basicConfig(level=log_level, format=log_format)

    try:
        config = load_and_merge_configs()
        config["debug"] = args.debug
        config["render_js"] = args.render_js
        config["check_content_type"] = args.check_content_type
        config["include_all"] = args.include_all

        if args.include_all:
            logger.debug("--include-all flag is set. Clearing default ignore patterns and disabling .gitignore handling.")
            config["fs_scraper"]["ignore_patterns"] = []

        include_patterns = [f"!{p}" if not p.startswith("!") else p for p in args.include]

        config["fs_scraper"]["ignore_patterns"] = config["fs_scraper"]["ignore_patterns"] + args.exclude + include_patterns

        scraper = await get_scraper(args.source, config)

        if not scraper:
            logger.error(f"Could not determine how to handle source: {args.source}")
            sys.exit(1)

        logger.info(f"Using scraper: {scraper.__class__.__name__}")
        markdown_content, context_data = await scraper.scrape()
        save_outputs(args.output, markdown_content, context_data)

    except ContentNotFoundError as e:
        logger.error(e)
        sys.exit(1)
    except (ValueError, FileNotFoundError, IOError) as e:
        logger.error(e)
        sys.exit(1)
    except Exception:
        logger.exception("An unexpected error occurred:")
        sys.exit(1)


def cli_entrypoint():
    """Synchronous entrypoint to run the async main function."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.getLogger(__name__).warning("\nOperation cancelled by user.")
        sys.exit(130)


if __name__ == "__main__":
    cli_entrypoint()
