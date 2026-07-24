# Declare targets that don't represent actual files.
.PHONY: help lint type format unit robot check requirements keydoc

# Show a list of the Make targets available in this file.
help:
	@echo "Commonly used commands:"
	@echo "  make lint          Run Pylint on source code"
	@echo "  make type          Run Pyright for static type checking"
	@echo "  make format        Check code formatting using Black"
	@echo "  make unit          Run unit tests with pytest"
	@echo "  make robot         Run integration tests with Robot Framework"
	@echo "  make check         Wrapper: run linting, type checks, format checks and all tests"
	@echo "  make requirements  Export requirements.txt and requirements-dev.txt"
	@echo "  make keydoc        Generate Robot Framework keyword documentation"

# Run linting with Pylint on the src/ directory.
lint:
	@echo "Running linter check (pylint)..."
	@poetry run pylint src/

# Run static type checks using Pyright.
type:
	@echo "Running type check (pyright)..."
	@poetry run pyright --project pyrightconfig.json

# Check formatting without changing files (used in CI or pre-commit).
format:
	@echo "Running formatter check (black)..."
	@poetry run black src/ --check

# Run unit tests using pytest.
unit:
	@echo "Running unit tests..."
	@poetry run python -m pytest --cov=src --cov-report=html --cov-branch test/unit

# Run integration tests using Robot Framework.
robot:
	@echo "Running integration tests..."
	@poetry run python -m robot --outputdir results --exclude git-exclude test/integration

# Run all static checks and test suites (for CI or pre-push).
check:
	@echo "Running full project check..."
	make lint
	make type
	make format
	make unit
	make robot
	@echo "All checks done!"

# Export dependencies to requirements files for pip compatibility.
requirements:
	@echo "Exporting requirement files..."
	@poetry export --without-hashes --format=requirements.txt > requirements.txt
	@poetry export --without-hashes --format=requirements.txt --with dev > requirements-dev.txt

# Generate the Robot Framework keyword documentation.
keydoc:
	@echo "Generating Robot Framework keyword documentation with Libdoc..."
	cd src && python -m robot.libdoc xmlvalidator ../docs/XmlValidator.html
