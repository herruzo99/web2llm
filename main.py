"""
The main entry point for the web_to_llm command-line application.

This script orchestrates the scraping process:
1. Parses command-line arguments.
2. Uses the scraper factory to get the right scraper for the job.
3. Calls the scraper to do the work.
4. Saves the results to the output directory.
"""
import argparse
import sys

from web_to_llm_pkg.scrapers import get_scraper
from web_to_llm_pkg.output import save_outputs

def main():
    """The main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Generate a clean Markdown file from a URL or local path, optimized for LLMs.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Examples:\n"
               "  # Scrape core source code of a GitHub repo\n"
               "  python main.py 'https://github.com/tiangolo/fastapi' -o fastapi-core --include-dirs fastapi\n\n"
               "  # Scrape a local project, excluding docs and tests\n"
               "  python main.py '~/projects/my-app' -o my-app-src --exclude-dirs docs,tests\n\n"
               "  # Scrape a specific section from a documentation page\n"
               "  python main.py 'https://nixos.org/manual/nixpkgs/stable/#rust' -o nix-rust-docs\n\n"
               "  # Scrape a local PDF\n"
               "  python main.py 'docs/research/paper.pdf' -o my-paper"
    )
    parser.add_argument("resource", help="The URL or local file/folder path to process.")

    parser.add_argument(
        "-o", "--output-base",
        required=True,
        help="The base name for the output folder and files."
    )

    # These options are only used by the GitHub and Local Folder scrapers
    parser.add_argument(
        "--include-dirs",
        type=str,
        default="",
        help="Comma-separated list of directories to include (repo/folder scrapers only)."
    )
    parser.add_argument(
        "--exclude-dirs",
        type=str,
        default="",
        help="Comma-separated list of directories to exclude (repo/folder scrapers only)."
    )

    args = parser.parse_args()

    try:
        # The factory decides which scraper to use based on the resource string.
        scraper = get_scraper(args.resource, args.include_dirs, args.exclude_dirs)

        if not scraper:
             print(f"Error: Could not determine how to handle resource: {args.resource}", file=sys.stderr)
             sys.exit(1)

        print(f"Using scraper: {scraper.__class__.__name__}")

        markdown_content, context_data = scraper.scrape()

        save_outputs(args.output_base, markdown_content, context_data)

    except (ValueError, FileNotFoundError, IOError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Catch-all for unexpected errors
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        # For debugging, you might want to re-raise or log the traceback
        # import traceback
        # traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()