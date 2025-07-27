# Web to LLM

A simple command-line tool to scrape web pages, GitHub repos, and local files into clean Markdown, suitable for feeding into a Large Language Model.

## Features

-   **Scrape any URL:** Pulls the main content from an article or documentation page.
-   **Target specific sections:** If you use a URL with a hash (e.g., `page.html#usage`), it will try to grab just that section.
-   **Scrape GitHub repos:** Clones a repository and concatenates its source files. You can specify which directories to include or exclude.
-   **Process local folders:** Works just like the GitHub scraper but on your local machine.
-   **Process PDFs:** Extracts text from local or remote PDF files. It can also pull metadata from arXiv abstract pages.

## Setup

```bash
git clone https://github.com/username/web-to-llm.git
cd web-to-llm
pip install -r requirements.txt
```

## How to Use

The script is run from the command line. All output is saved to the output/ directory.
```bash
python main.py <URL_OR_PATH> -o <OUTPUT_NAME> [OPTIONS]
```
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

 - main.py: CLI entry point. Chooses the right scraper for the job.
 - web_to_llm_pkg/scrapers/: Contains the different scraping strategies.
  - generic_scraper.py: For standard web pages.
  - github_scraper.py: For GitHub repos.
  - local_folder_scraper.py: For local project directories.
  - pdf_scraper.py: For local and remote PDFs.
  - web_to_llm_pkg/config.py: Static configuration, like files to ignore and CSS selectors.

## Contributing

Feel free to open an issue or submit a pull request if you have ideas for improvements.

## License

MIT