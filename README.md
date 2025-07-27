# Web to LLM

A simple command-line tool I built to scrape web pages, GitHub repos, and local files into clean Markdown. The goal is to create high-quality, structured text that's easy to feed into a Large Language Model for fine-tuning or RAG.

## What it does

-   **Scrape any URL:** Pulls the main content from an article or documentation page.
-   **Target specific sections:** If you use a URL with a hash (e.g., `page.html#usage`), it will try to grab just that section.
-   **Grab a whole repo:** Clones a GitHub repository and concatenates all its source files. You can specify which directories to include or exclude to get just the code you want.
-   **Process PDFs:** Extracts text from local or remote PDF files. For arXiv links, it's smart enough to find the abstract page to pull better metadata.
-   **Handle local folders:** You can point it at a local project directory and it works just like the GitHub scraper.

## Setup

1.  **Clone the repo:**
```bash
git clone https://github.com/username/web-to-llm.git
cd web-to-llm
```

2.  **Install the dependencies:**
```bash
pip install -r requirements.txt
```

## How to Use

The script is run from the command line. The basic format is:

```bash
python main.py <URL_OR_PATH> -o <OUTPUT_NAME> [OPTIONS]
```

All output is saved to the `output/` directory.

### Examples

**1. Scrape a GitHub repo (only the `fastapi` directory):**
```bash
python main.py 'https://github.com/tiangolo/fastapi' -o fastapi-src --include-dirs fastapi
```

**2. Scrape a local project (excluding `docs` and `tests`):**
```bash
python main.py '~/dev/my-project' -o my-project-code --exclude-dirs docs,tests
```

**3. Scrape just one section of a webpage:**
```bash
python main.py 'https://nixos.org/manual/nixpkgs/stable/#rust' -o nix-rust-docs
```

**4. Scrape a PDF from a URL:**
```bash
python main.py 'https://arxiv.org/pdf/1706.03762.pdf' -o attention-is-all-you-need
```

## Code Overview

For anyone interested in the internals:

-   `main.py`: The entry point. It figures out what kind of resource you passed and picks the right scraper.
-   `web_to_llm_pkg/scrapers/`: This directory holds the different scraping strategies.
    -   `generic_scraper.py`: For standard web pages.
    -   `github_scraper.py`: For GitHub repos. It handles cloning, filtering, and concatenating files.
    -   `local_folder_scraper.py`: Reuses the logic from the GitHub scraper but for a local directory.
    -   `pdf_scraper.py`: Handles remote and local PDFs.
-   `web_to_llm_pkg/config.py`: Contains static lists like files/extensions to ignore and CSS selectors for finding the "main" content on a page.

## Contributing

Feel free to open an issue or submit a pull request if you have ideas for improvements.

## License

MIT