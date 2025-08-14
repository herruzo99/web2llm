# Web2LLM

[![CI/CD Pipeline](https://github.com/herruzo99/web2llm/actions/workflows/ci.yml/badge.svg)](https://github.com/herruzo99/web2llm/actions/workflows/ci.yml)

A command-line tool to scrape web pages, GitHub repos, local folders, and PDFs into clean, aggregated Markdown suitable for Large Language Models.

## Description

This tool provides a unified interface to process various sources—from live websites and code repositories to local directories and PDF files—and convert them into a structured Markdown format. The clean, token-efficient output is ideal for use as context in prompts for Large Language Models, for Retrieval-Augmented Generation (RAG) pipelines, or for documentation archiving.

## Installation

For standard scraping of static websites, local files, and GitHub repositories, install the base package:
___bash
pip install web2llm
___
To enable JavaScript rendering for Single-Page Applications (SPAs) and other dynamic websites, you must install the `[js]` extra, which includes Playwright:
___bash
pip install "web2llm[js]"
___
After installing the `js` extra, you must also download the necessary browser binaries for Playwright to function:
___bash
playwright install
___
## Usage

### Command-Line Interface

The tool is run from the command line with the following structure:

___bash
web2llm <SOURCE> -o <OUTPUT_NAME> [OPTIONS]
___
-   `<SOURCE>`: The URL or local path to scrape.
-   `-o, --output`: The base name for the output folder and the `.md` and `.json` files created inside it.

All scraped content is saved to a new directory at `output/<OUTPUT_NAME>/`.

#### General Options:
- `--debug`: Enable debug mode for verbose, step-by-step output to stderr.

#### Web Scraper Options (For URLs):
- `--render-js`: Render JavaScript using a headless browser. Slower but necessary for SPAs. Requires installation with the `[js]` extra.
- `--check-content-type`: Force a network request to check the page's `Content-Type` header. Use for URLs that serve PDFs without a `.pdf` extension.

#### Filesystem Options (For GitHub & Local Folders):
When scraping a local folder or a GitHub repository, `web2llm` will automatically find and respect the rules in the project's `.gitignore` file. This ensures that the scrape accurately reflects the intended source code of the project.

-   `--exclude <PATTERN>`: A `.gitignore`-style pattern for files/directories to exclude. Can be used multiple times.
-   `--include <PATTERN>`: A pattern to re-include a file that would otherwise be ignored by default or by an `--exclude` rule. Can be used multiple times.
-   `--include-all`: Disables all default, project-level, and `.gitignore` ignore patterns, providing a complete scrape of all text-based files. Explicit `--exclude` flags are still respected.

### Configuration

`web2llm` uses a hierarchical configuration system that gives you precise control over the scraping process:

1.  **Default Config**: The tool comes with a built-in `default_config.yaml` containing a robust set of ignore patterns for common development files and selectors for web scraping.
2.  **Project-Specific Config**: You can create a `.web2llm.yaml` file in the root of your project to override or extend the default settings. This is the recommended way to manage project-specific rules.
3.  **CLI Arguments**: Command-line flags provide the final layer of control, overriding any settings from the configuration files for a single run.

## Examples

**1. Scrape a specific directory within a GitHub repo:**
___bash
web2llm 'https://github.com/tiangolo/fastapi' -o fastapi-src --include 'fastapi/'
___

**2. Scrape a local project, excluding test and documentation folders:**
___bash
web2llm '~/dev/my-project' -o my-project-code --exclude 'tests/' --exclude 'docs/'
___

**3. Scrape a local project but re-include the `LICENSE` file, which is ignored by default:**
___bash
web2llm '.' -o my-project-with-license --include '!LICENSE'
___

**4. Scrape everything in a project, including files normally ignored by `.gitignore`:**
___bash
web2llm . -o my-project-full --include-all --exclude '.git/'
___

**5. Scrape just the "Installation" section from a webpage:**
___bash
web2llm 'https://fastapi.tiangolo.com/#installation' -o fastapi-install
___

**6. Scrape a PDF from an arXiv URL:**
___bash
web2llm 'https://arxiv.org/pdf/1706.03762.pdf' -o attention-is-all-you-need
___

## Contributing

Contributions are welcome. Please refer to the project's issue tracker and `CONTRIBUTING.md` file for information on how to participate.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
