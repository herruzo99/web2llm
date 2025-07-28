# Web2LLM

[![CI/CD Pipeline](https://github.com/herruzo99/web2llm/actions/workflows/ci.yml/badge.svg)](https://github.com/herruzo99/web2llm/actions/workflows/ci.yml)

A command-line tool to scrape web pages, GitHub repos, local folders, and PDFs into clean, aggregated Markdown suitable for Large Language Models.

## Description

This tool provides a unified interface to process various sources—from live websites and code repositories to local directories and PDF files—and convert them into a structured Markdown format. The clean, token-efficient output is ideal for use as context in prompts for Large Language Models, for Retrieval-Augmented Generation (RAG) pipelines, or for documentation archiving.

## Key Features

-   **Multi-Source Scraping**: Handles public web pages, GitHub repositories, local project folders, and both local and remote PDF files.
-   **Content-Aware Extraction**: For web pages, it intelligently identifies and extracts the main content, ignoring common clutter like navigation bars, sidebars, and footers.
-   **Targeted Section Scraping**: Use a URL with a hash fragment (e.g., `page.html#usage`) to scrape just that specific section of a webpage.
-   **Code-Aware Filesystem Processing**: For GitHub repos and local folders, it generates a file tree and concatenates all text-based source files into a single document, complete with syntax highlighting hints.
-   **Intelligent & Extensible Filtering**: Automatically ignores common non-source files (`.git`, `node_modules`, lockfiles, images) using a comprehensive set of default `.gitignore`-style patterns.
-   **Advanced Configuration**: Customize scraping behavior by placing a `.web2llm.yaml` file in your project root to override default settings or by using command-line flags for on-the-fly adjustments.
-   **Specialized PDF Handling**: Extracts text from PDFs and includes special logic for arXiv papers to pull structured metadata (title, abstract) from the landing page.

## Installation

```bash
pip install web2llm
```

## Usage

### Command-Line Interface

The tool is run from the command line with the following structure:

```bash
web2llm <SOURCE> -o <OUTPUT_NAME> [OPTIONS]
```

-   `<SOURCE>`: The URL or local path to scrape.
-   `-o, --output`: The base name for the output folder and the `.md` and `.json` files created inside it.

All scraped content is saved to a new directory at `output/<OUTPUT_NAME>/`.

#### Filesystem Options (For GitHub & Local Folders):

-   `--exclude <PATTERN>`: A `.gitignore`-style pattern for files/directories to exclude. This flag can be used multiple times. (e.g., `--exclude 'docs/' --exclude '*.log'`).
-   `--include <PATTERN>`: A pattern to re-include a file that would otherwise be ignored by default or by an `--exclude` rule. This is typically a negation pattern. Can be used multiple times. (e.g., `--include '!LICENSE'`).
-   `--include-all`: Disables all default and project-level ignore patterns, processing every text file encountered. Explicit `--exclude` flags are still respected.

### Configuration

`web2llm` uses a hierarchical configuration system that gives you precise control over the scraping process:

1.  **Default Config**: The tool comes with a built-in `default_config.yaml` containing a robust set of ignore patterns for common development files and selectors for web scraping.
2.  **Project-Specific Config**: You can create a `.web2llm.yaml` file in the root of your project to override or extend the default settings. This is the recommended way to manage project-specific rules (e.g., ignoring a `dist` folder or a custom log file).
3.  **CLI Arguments**: Flags like `--exclude` and `--include-all` provide the final layer of control, overriding any settings from the configuration files for a single run.

## Examples

**1. Scrape a specific directory within a GitHub repo:**
```bash
web2llm 'https://github.com/tiangolo/fastapi' -o fastapi-src --include 'fastapi/'
```

**2. Scrape a local project, excluding test and documentation folders:**
```bash
web2llm '~/dev/my-project' -o my-project-code --exclude 'tests/' --exclude 'docs/'
```

**3. Scrape a local project but re-include the `LICENSE` file, which is ignored by default:**
```bash
web2llm '.' -o my-project-with-license --include '!LICENSE'
```

**4. Scrape everything in a project except the `.git` directory:**
```bash
web2llm . -o my-project-full --include-all --exclude '.git/'
```

**5. Scrape just the "Installation" section from a webpage:**
```bash
web2llm 'https://fastapi.tiangolo.com/#installation' -o fastapi-install
```

**6. Scrape a PDF from an arXiv URL:**
```bash
web2llm 'https://arxiv.org/pdf/1706.03762.pdf' -o attention-is-all-you-need
```

## Contributing

Contributions are welcome. Please refer to the project's issue tracker and contribution guidelines for information on how to participate.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
