# Contributing to Web-to-LLM

First off, thank you for considering contributing! This project is made better by the community.

## Ways to Contribute

-   Reporting bugs
-   Suggesting enhancements
-   Submitting pull requests with new features or bug fixes
-   Improving documentation

## Setting up the Development Environment

To get started, you'll need a recent version of Python (3.9+).

1.  **Clone the repository:**
    ___bash
    git clone https://github.com/herruzo99/web-to-llm.git
    cd web-to-llm
    ___

2.  **Create and activate a virtual environment:**
    ___bash
    # For Unix/macOS
    python3 -m venv .venv
    source .venv/bin/activate

    # For Windows
    python -m venv .venv
    .venv\Scripts\activate
    ___

3.  **Install the project in editable mode with development dependencies:**
    This will install the project and all the tools needed for development, testing, and quality checks.
    ___bash
    pip install -e ".[dev,test]"
    ___

## Running Quality Checks

To maintain code quality, we use `ruff` for linting/formatting and `pytest` for testing. The most professional and standard way to use these tools is with **pre-commit hooks**, which automatically run checks before you create a commit.

### The Recommended Way: Pre-Commit Hooks

This is the "set it and forget it" approach. Once installed, it will run on every commit automatically.

1.  **Install pre-commit hooks:**
    After setting up the environment (which installs `pre-commit` via `pip`), run this command once:
    ___bash
    pre-commit install
    ___

2.  **Commit your code:**
    Now, when you run `git commit`, `ruff` and other checks will run automatically on the files you've staged. If an issue is found (like a formatting error), the commit will be aborted, and `ruff` might fix the file for you automatically. Just `git add` the fixed file and try your commit again.

### The Manual Way

You can also run the checks manually at any time.

#### Running the Linter (`ruff`)

-   To check for linting errors and formatting issues:
    ___bash
    ruff check .
    ruff format --check .
    ___

-   To automatically fix linting and formatting issues:
    ___bash
    ruff check . --fix
    ruff format .
    ___

#### Running Tests (`pytest`)

To run the full test suite:
___bash
pytest
___

## Submitting a Pull Request

1.  Create a new branch for your feature or bug fix: `git checkout -b feature/your-amazing-feature`.
2.  Make your changes and commit them (the pre-commit hooks will ensure quality).
3.  Push your branch to your fork on GitHub.
4.  Open a pull request from your fork to the `main` branch of the original repository.
5.  In the pull request description, please describe your changes and reference any related issues.

Thank you for your contribution!