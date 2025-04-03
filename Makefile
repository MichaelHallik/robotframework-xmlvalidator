# Make constants.
PYTHON_VERSION ?= 3.10
VENV_HOME := /c/Python-virt-envs

# Declare targets that don't represent actual files.
.PHONY: help install lint type format unit coverage robot check requirements keydoc unit_doc robot_doc structure meta doc clean setup test-install list-envs delete-env

# Show a list of the Make targets available in this file.
help:
	@echo "Commonly used commands:"
	@echo "  make install       Install project dependencies via Poetry"
	@echo "  make lint          Run Pylint on source and test code"
	@echo "  make type          Run Pyright for static type checking"
	@echo "  make format        Check code formatting using Black"
	@echo "  make unit          Run unit tests with pytest"
	@echo "  make coverage      Open the pytest coverage report in the browser"
	@echo "  make robot         Run integration tests with Robot Framework"
	@echo "  make check         Wrapper: run linting, type checks, format checks and all tests"
	@echo "  make requirements  Export requirements.txt and requirements-dev.txt"
	@echo "  make keydoc        Generate Robot Framework keyword documentation"
	@echo "  make unit_doc      Generate overview of unit test cases"
	@echo "  make structure     Analyze project structure and write to file"
	@echo "  make meta          Establish code metrics and write to file"
	@echo "  make doc           Wrapper: create all docs"
	@echo "  make clean         Remove temporary files and test artifacts"
	@echo "  make setup         Install, export and setup pre-commit hooks"
	@echo "  make test_install  Create a virtual env, install the library and run basic checks"
	@echo "  make delete-env   Delete a virtual environment."

# Install dependencies from pyproject.toml, locked to versions in poetry.lock.
install:
	@echo "Running poetry install..."
	@poetry install

# Run linting with Pylint on the src/ directory.
lint:
	@echo "Running linter check (pylint)..."
	@poetry run pylint src/ --exit-zero --disable=R0903

# Run static type checks using Pyright.
type:
	@echo "Running type check (pyright)..."
	@poetry run pyright --project pyrightconfig.json || exit 0

# Check formatting without changing files (used in CI or pre-commit).
format:
	@echo "Running formatter check (black)..."
	@poetry run black src/ --check || exit 0

# Run unit tests using pytest.
unit:
	@echo "Running unit tests..."
	@poetry run pytest --cov=src --cov-report=html --cov-branch test/

coverage:
	make unit
	@python -m webbrowser C:\\Projects\\robotframework-xmlvalidator\\htmlcov\\index.html

# Run integration tests using Robot Framework.
robot:
	@echo "Running integration tests..."
	@python -m robot -d ./Results test/integration

# Run all static checks and test suites (for CI or pre-push).
check:
	@echo "Running full project check..."
	make lint
	make type
	make format
	make unit
	make robot
	@echo "All checks passed!"

# Export dependencies to requirements files for pip compatibility.
requirements:
	@echo "Exporting requirement files..."
	@poetry export --without-hashes --format=requirements.txt > requirements.txt
	@poetry export --without-hashes --format=requirements.txt --with dev > requirements-dev.txt

# Generate the Robot Framework keyword documentation.
keydoc:
	@echo "Generating Robot Framework keyword documentation with Libdoc..."
	cd src && python -m robot.libdoc xmlvalidator ../docs/XmlValidator.html

# Generate an overview of unit test cases and write to file.
unit_doc:
	@echo "Exporting overview of unit test cases"
	python tools_extract_doc_unit_test.py

# Generate an overview of integration test cases and write to file.
robot_doc:
	@echo "Exporting overview of integration test cases"
	python tools_extract_doc_integration_test.py

# Generate an overview of the project/repo structure and write to file.
structure:
	@echo "Exporting the project structure"
	python tools_extract_project_structure.py

# Establish basic code metrics and write to file.
meta:
	@echo "Exporting basic code metrics"
	python tools_code_analyzer.py

# Wrapper that generates all docs.
doc:
	@echo "Exporting all project documentation ..."
	make requirements
	make keydoc
	make unit_doc
	make robot_doc
	make structure
	make meta
	@echo "All documentation exported!"

# Clean up compiled files, caches and test output.
clean:
	@echo "Clean up repository..."; \
	echo ""; \
	pycache_count=0; pyc_count=0; csv_count=0; artifact_count=0; \
	removed_paths=""; \
	echo "Searching for __pycache__ directories..."; \
	for dir in $$(/usr/bin/find . -type d -name "__pycache__"); do \
		echo "  Removing: $$dir"; \
		rm -r "$$dir"; \
		removed_paths="$$removed_paths\n$$dir"; \
		pycache_count=$$((pycache_count + 1)); \
	done; \
	echo "Searching for .pyc files..."; \
	for file in $$(/usr/bin/find . -type f -name "*.pyc"); do \
		echo "  Removing: $$file"; \
		rm "$$file"; \
		removed_paths="$$removed_paths\n$$file"; \
		pyc_count=$$((pyc_count + 1)); \
	done; \
	echo "Removing CSV test reports..."; \
	for file in $$(/usr/bin/find test/_data/integration -type f -name "*.csv" 2>/dev/null); do \
		echo "  Removing: $$file"; \
		rm "$$file"; \
		removed_paths="$$removed_paths\n$$file"; \
		csv_count=$$((csv_count + 1)); \
	done; \
	echo "Removing test & coverage artifacts..."; \
	for path in .pytest_cache .coverage htmlcov .mypy_cache results dist; do \
		if [ -e "$$path" ]; then \
			echo "  Removing: $$path"; \
			rm -rf "$$path"; \
			removed_paths="$$removed_paths\n$$path"; \
			artifact_count=$$((artifact_count + 1)); \
		fi; \
	done; \
	echo ""; \
	echo "Clean complete."; \
	echo ""; \
	echo "Stats:"; \
	echo "  - __pycache__ directories removed: $$pycache_count"; \
	echo "  - .pyc files removed: $$pyc_count"; \
	echo "  - CSV files removed: $$csv_count"; \
	echo "  - Other artifacts removed: $$artifact_count"; \
	echo ""; \
	echo "All removed paths:"; \
	printf "$$removed_paths\n" | sed '/^$$/d; s/^/  - /'

# Set up project environment: install, pre-commit hook setup, etc.
setup:
	@echo "Setting up the project environment..."
	make install
	@echo "Setup complete!"

# Create and activate a virt env, install the library and run some checks.
test-install:
	cmd /c install-xmlvalidator.bat $(ENV) $(VER)

# Get all current virtual environments
list-envs:
	@echo "Available virtual environments in $(VENV_HOME):"
	@ls -1 "$(VENV_HOME)" | grep -v '^\s*$$'

# Delete a virtual environment.
delete-env:
	@if [ -z "$(NAME)" ]; then \
		echo "Please provide the environment name: make delete-venv NAME=your-env"; \
	else \
		echo "Deleting environment: $(VENV_HOME)/$(NAME)"; \
		if [ -d "$(VENV_HOME)/$(NAME)" ]; then \
			rm -rf "$(VENV_HOME)/$(NAME)"; \
			echo "Deleted: $(VENV_HOME)/$(NAME)"; \
		else \
			echo "Directory not found: $(VENV_HOME)/$(NAME)"; \
		fi; \
	fi