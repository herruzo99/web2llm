import argparse
import sys

from .config import load_and_merge_configs
from .output import save_outputs
from .scrapers import get_scraper


def main():
    parser = argparse.ArgumentParser(
        description="Scrape web content into clean Markdown, optimized for LLMs.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Examples:
  # Scrape core source code of a GitHub repo, ignoring default files but including the 'fastapi' dir
  web2llm 'https://github.com/tiangolo/fastapi' -o fastapi-core --include 'fastapi/'

  # Scrape a local project, adding 'docs/' and 'tests/' to the ignore list
  web2llm '~/projects/my-app' -o my-app-src --exclude 'docs/' --exclude 'tests/'

  # Scrape everything in a local project, ignoring only '.git/'
  web2llm '.' -o all-files --include-all --exclude '.git/'

  # Scrape a specific section from a documentation page
  web2llm 'https://nixos.org/manual/nixpkgs/stable/#rust' -o nix-rust-docs""",
    )
    parser.add_argument("source", help="The URL or local file/folder path to process.")

    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="The base name for the output folder and files.",
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
        help="A gitignore-style pattern to re-include files that would otherwise be ignored. "
        "Useful for overriding defaults. E.g., --include '!LICENSE'",
    )
    fs_group.add_argument(
        "--include-all",
        action="store_true",
        help="Scrape all files, ignoring default and project-level ignore patterns. Explicit --exclude flags will still be respected.",
    )

    args = parser.parse_args()

    try:
        # 1. Load configuration from default and project files
        config = load_and_merge_configs()

        # 2. Apply CLI arguments to override the loaded config
        if args.include_all:
            # Wipe the default patterns, start fresh
            config["fs_scraper"]["ignore_patterns"] = []

        # CLI includes (negation patterns) should come first to have priority
        # E.g., !src/
        include_patterns = [f"!{p.strip('/')}/" if not p.startswith("!") else p for p in args.include]

        # Add CLI patterns to the config's patterns list
        config["fs_scraper"]["ignore_patterns"] = include_patterns + config["fs_scraper"]["ignore_patterns"] + args.exclude

        # 3. Get the appropriate scraper
        scraper = get_scraper(args.source, config)

        if not scraper:
            print(
                f"Error: Could not determine how to handle source: {args.source}",
                file=sys.stderr,
            )
            sys.exit(1)

        print(f"Using scraper: {scraper.__class__.__name__}")
        markdown_content, context_data = scraper.scrape()
        save_outputs(args.output, markdown_content, context_data)

    except (ValueError, FileNotFoundError, IOError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        # For debugging, you might want to uncomment these lines
        # import traceback
        # traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
