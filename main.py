import argparse
import sys

from web_to_llm_pkg.scrapers import get_scraper
from web_to_llm_pkg.output import save_outputs

def main():
    parser = argparse.ArgumentParser(
        description="Scrape web content into clean Markdown, optimized for LLMs.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Examples:\n"
               "  # Scrape core source code of a GitHub repo\n"
               "  python main.py 'https://github.com/tiangolo/fastapi' -o fastapi-core --include-dirs fastapi\n\n"
               "  # Scrape a local project, excluding docs and tests\n"
               "  python main.py '~/projects/my-app' -o my-app-src --exclude-dirs docs,tests\n\n"
               "  # Scrape a specific section from a documentation page\n"
               "  python main.py 'https://nixos.org/manual/nixpkgs/stable/#rust' -o nix-rust-docs"
    )
    parser.add_argument("source", help="The URL or local file/folder path to process.")

    parser.add_argument(
        "-o", "--output",
        required=True,
        help="The base name for the output folder and files."
    )

    parser.add_argument(
        "--include-dirs",
        type=str,
        default="",
        help="Comma-separated list of directories to include (for folder/repo scrapers)."
    )
    parser.add_argument(
        "--include-all",
        action="store_true",
        help='Ignore the default ignored list and include all files, except those in --exclude-dirs.'
    )
    parser.add_argument(
        "--exclude-dirs",
        type=str,
        default="",
        help="Comma-separated list of directories to exclude (for folder/repo scrapers)."
    )

    args = parser.parse_args()

    try:
        scraper = get_scraper(args.source, args.include_dirs, args.exclude_dirs, args.include_all)

        if not scraper:
             print(f"Error: Could not determine how to handle source: {args.source}", file=sys.stderr)
             sys.exit(1)

        print(f"Using scraper: {scraper.__class__.__name__}")

        markdown_content, context_data = scraper.scrape()

        save_outputs(args.output, markdown_content, context_data)

    except (ValueError, FileNotFoundError, IOError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        # For debugging, uncomment the following lines
        # import traceback
        # traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()