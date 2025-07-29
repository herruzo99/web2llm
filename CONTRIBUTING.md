# Contributing to web2llm

First off, thank you for considering contributing to `web2llm`. Your help is appreciated.

This document provides guidelines for contributing to the project.

## Development Setup

We recommend using a Python virtual environment to manage dependencies for local development. This project supports Python 3.10 and newer.

1.  **Clone the repository:**
    ___bash
    git clone https://github.com/herruzo99/web2llm.git
    cd web2llm
    ___

2.  **Create and activate a virtual environment:**
    ___bash
    # Create the environment
    python3 -m venv .venv

    # Activate it (on macOS/Linux)
    source .venv/bin/activate

    # On Windows (PowerShell)
    # .\.venv\Scripts\Activate.ps1
    ___

3.  **Install dependencies in editable mode:**
    The project uses `setuptools` and optional dependencies. The `[dev]` extra includes all dependencies needed for development, testing, and optional features like JavaScript rendering.

    ___bash
    pip install -e ".[dev]"
    ___
    This command installs the package itself in "editable" mode (`-e`), so changes you make to the source code are immediately effective.

4.  **Install pre-commit hooks:**
    This project uses `pre-commit` to automatically run linters and formatters (`ruff`) on every commit. This ensures code style consistency.

    ___bash
    pre-commit install
    ___
    Now, `ruff` will check and format your code each time you run `git commit`.

## Running Tests

The test suite uses `pytest`. To run all tests, execute the following command from the project root:

___bash
pytest
___

Before submitting a contribution, please ensure all tests pass.

## Code Style

Code style is enforced by **Ruff**. The pre-commit hook will automatically format your code. However, you can also run the formatter and linter manually:

___bash
# To format all files
ruff format .

# To check for linting errors
ruff check .
___

## Submitting Changes

1.  **Fork the repository** on GitHub.
2.  **Create a new branch** for your feature or bugfix from the `main` branch.
    ___bash
    git checkout -b feature/my-awesome-feature
    ___
3.  **Make your changes** and commit them with a clear, descriptive message.
4.  **Ensure all tests and linters pass** locally.
5.  **Push your branch** to your fork on GitHub.
    ___bash
    git push origin feature/my-awesome-feature
    ___
6.  **Open a Pull Request** to the `main` branch of the original repository.
    - Provide a clear title for your PR (e.g., "Feat: Add support for XYZ" or "Fix: Correctly parse ABC").
    - In the description, explain the "why" behind your changes and link to any relevant issues.
