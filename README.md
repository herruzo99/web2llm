# Web2LLM

[![CI/CD Pipeline](https://github.com/herruzo99/web2llm/actions/workflows/ci.yml/badge.svg)](https://github.com/herruzo99/web2llm/actions/workflows/ci.yml)

A command-line tool to scrape web pages, GitHub repos, local folders, and PDFs into clean Markdown, optimized for Large Language Models.

## Description

This tool provides a unified interface to process various sources, from live websites and code repositories to local files, and convert them into a structured Markdown format. The clean output is ideal for use as context in prompts for Large Language Models, for RAG (Retrieval-Augmented Generation) pipelines, or for documentation archiving. As it reduces dramatically the number of tokens compared to raw html.

## Key Features

-   **Scrape Any URL**: Pulls the main content from an article or documentation page, intelligently ignoring clutter like navbars and footers.
-   **Target Specific Sections**: Use a URL with a hash (e.g., `page.html#usage`) to grab just that specific section of a webpage.
-   **Scrape GitHub Repos**: Clones a repository and concatenates its source files into a single Markdown document, complete with a file tree.
-   **Process Local Folders**: Scans a local directory and processes its contents just like the GitHub scraper.
-   **Handle PDFs**: Extracts text from both local and remote PDF files. It includes special handling for arXiv papers to pull rich metadata from the abstract page.
-   **Intelligent Filtering**: For codebases, the tool automatically ignores common non-source files (`.git`, `node_modules`, lockfiles, images), but you can customize this behavior with include/exclude flags.

## Installation

You can install `web2llm` directly from PyPI (once published) or from source:
```bash
pip install web2llm
```

## Usage

The tool is run from the command line. The basic syntax is:
```bash
web2llm <SOURCE> -o <OUTPUT_NAME> [OPTIONS]
```
-   `<SOURCE>`: The URL or local path to scrape.
-   `-o, --output`: The base name for the output folder and files (e.g., `my-project`).
-   All scraped content is saved to a new directory at `output/<OUTPUT_NAME>/`.

### Examples

**1. Scrape a GitHub repo (only the `fastapi` directory):**
```bash
web2llm 'https://github.com/tiangolo/fastapi' -o fastapi-src --include-dirs fastapi
```

**2. Scrape a local project (excluding `docs` and `tests`):**
```bash
web2llm '~/dev/my-project' -o my-project-code --exclude-dirs "docs,tests"
```

**3. Scrape just one section of a webpage:**
```bash
web2llm 'https://nixos.org/manual/nixpkgs/stable/#rust' -o nix-rust-docs
```

**4. Scrape a PDF from an arXiv URL:**
```bash
web2llm 'https://arxiv.org/pdf/1706.03762.pdf' -o attention-is-all-you-need
```

## Contributing

Contributions are welcome! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to set up the development environment and submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
