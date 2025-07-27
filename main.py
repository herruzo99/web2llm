"""
The main entry point for the web_to_llm command-line application.

This script handles parsing command-line arguments, determining if the target
is a local path or a remote URL, selecting the appropriate scraper,
orchestrating the scraping process, and saving the results to disk.
"""
import argparse
import os
import sys

from web_to_llm_pkg.scrapers import get_scraper_for_url
from web_to_llm_pkg.scrapers.local_folder_scraper import LocalFolderScraper
from web_to_llm_pkg.scrapers.local_pdf_scraper import LocalPDFScraper
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
    
    parser.add_argument(
        "--include-dirs",
        type=str,
        default="",
        help="Comma-separated list of top-level directories to exclusively include.\n(for local folders or GitHub repos). This takes precedence over --exclude-dirs."
    )
    
    parser.add_argument(
        "--exclude-dirs",
        type=str,
        default="",
        help="Comma-separated list of top-level directories to exclude.\n(for local folders or GitHub repos)."
    )

    args = parser.parse_args()
    
    scraper = None
    resource_path = os.path.expanduser(args.resource)

    include_dirs = [d.strip() for d in args.include_dirs.split(',') if d.strip()]
    exclude_dirs = [d.strip() for d in args.exclude_dirs.split(',') if d.strip()]

    if os.path.exists(resource_path):
        if os.path.isdir(resource_path):
            scraper = LocalFolderScraper(
                resource_path, 
                include_dirs=include_dirs,
                exclude_dirs=exclude_dirs
            )
        elif resource_path.lower().endswith('.pdf'):
            scraper = LocalPDFScraper(resource_path)
        else:
            print(f"Error: Unsupported local file type: {resource_path}", file=sys.stderr)
            sys.exit(1)
    else:
        scraper = get_scraper_for_url(args.resource, args.include_dirs, args.exclude_dirs)
    
    if not scraper:
         print(f"Error: Could not determine how to handle resource: {args.resource}", file=sys.stderr)
         sys.exit(1)
    
    print(f"Using scraper: {scraper.__class__.__name__}")
    
    try:
        markdown_content, context_data = scraper.scrape()
    except Exception as e:
        print(f"An error occurred during scraping: {e}", file=sys.stderr)
        return
        
    save_outputs(args.output_base, markdown_content, context_data)

if __name__ == "__main__":
    main()