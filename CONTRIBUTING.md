# Contributing to XMLValidator

Thank you for considering contributing to this project! We welcome all contributions, whether it's bug reports, new features, documentation improvements, or anything else that enhances the project.

For general project info, setup instructions, and usage examples, see the [README](README.md).

## How to Contribute

### 1. Reporting Issues
- If you find a bug or have a feature request, open a [GitHub Issue](../../issues).
- Provide clear and detailed information, including steps to reproduce the issue (if applicable).
- Suggest a possible fix or enhancement if you have one.

### 2. Submitting Code Changes
#### Step 1: Fork & Clone
- Fork this repository.
- Clone your fork:  
  ```sh
  git clone https://github.com/MichaelHallik/robotframework-xmlvalidator.git
  ```
- Navigate into the directory:
  ```sh
  cd your-repo
  ```
- Create a new branch for your feature/fix:
  ```sh
  git checkout -b feature/schema-validation
  ```
  Use clear, descriptive branch names. Suggested prefixes:
  - `feature/<short-description>` for new features
  - `fix/<issue-id>` for bug fixes
  - `docs/<section>` for documentation updates
  - `chore/<task>` for maintenance or config changes

#### Step 2: Code & Test
- Follow the existing code structure and style.
- Ensure your code is well-documented.
- Run linters:
  ```sh
  pylint src/  
  ```
- Make sure all unit tests pass before committing.  
  See `test/_doc/unit/README.md` for details.
- Make sure all integration tests pass before committing.  
  See `test/_doc/integration/README.md` for details.

#### Step 3: Commit & Push
- Commit your changes with a meaningful message:
  ```sh
  git commit -m "Add feature XYZ."
  ```
- Push to your fork:
  ```sh
  git push origin feature-branch
  ```

#### Step 4: Open a Pull Request (PR)
If you had not done so earlier, before opening a PR:

- Ensure all tests pass (unit and integration).
- Run linters and fix issues (e.g., `pylint`, `black`).
- Update or add documentation as needed.
- Add an entry to `CHANGELOG.md` summarizing your change (under "Unreleased").
- Follow branch naming conventions.

Then:

- Open a PR against the `main` branch.
- Ensure all CI checks pass.
- Address any requested changes.
- Wait for approval & merge.

### 3. Code Style Guidelines
- Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code.
- Use `pylint` for formatting.
- Keep modules, methods/functions, and classes well-documented.

### 4. Testing
- All new functionality should include tests.
- Run both unit tests (`pytest`) and Robot Framework integration tests.

### 5. Community Guidelines
- Be respectful and constructive.
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md).
- Help improve documentation when possible.

### 6. Pre-commit Hooks (optional but recommended)
- If you have `pre-commit` installed, you can run all formatters and linters automatically before committing:
  ```sh
  pre-commit install
  ```

Thank you for your contributions!

# Makefile Usage Guide
The Makefile in this repository provides a simplified command-line interface for common development tasks such as linting, testing, cleaning, and packaging.

It is intended to streamline repetitive actions and ensure consistency across development environments.

## Available Make Targets

Below are the available targets and what they do:

- install:
  Install dependencies using Poetry.
- lint:
  Run static code analysis using ruff.
- format
  Auto-format code using ruff.
- test:
  Run all tests using pytest.
- clean:
  Remove Python cache files and compiled artifacts.
- build:
  Build the project package (wheel and tarball) via Poetry.
- help
  Show a list of available make targets with descriptions.

## Usage Examples

Run the following commands from the root of the project directory.

Install dependencies:

    make install

Lint the codebase:

    make lint

Format the code automatically:

    make format

Run all tests:

    make test

Clean up build and Python cache files:

    make clean

Package the project:

    make build

Show help:

    make help