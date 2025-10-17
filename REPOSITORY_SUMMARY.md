# Repository Summary: robotframework-xmlvalidator

## Overview

**robotframework-xmlvalidator** is a Robot Framework test library designed for validating XML files against XSD (XML Schema Definition) schemas. The library provides comprehensive XML validation capabilities with detailed error reporting, batch processing, and flexible configuration options.

**Current Version:** 2.0.0  
**License:** Apache License 2.0  
**Python Requirements:** Python 3.10+  
**Author:** Michael Hallik

## Purpose and Use Case

This library enables automated XML validation in Robot Framework test suites, making it ideal for:
- Testing XML-based APIs and services
- Validating configuration files and data exports
- Ensuring XML document compliance with defined schemas
- Quality assurance workflows requiring XML validation
- Batch processing of multiple XML files against multiple XSD schemas

## Key Features

### Core Capabilities
- **Single and Batch Validation**: Validate one or multiple XML files against one or more XSD schemas
- **Dynamic Schema Resolution**: Automatic matching of XML files to appropriate XSD schemas using:
  - Namespace-based matching (`by_namespace`)
  - Filename-based matching (`by_file_name`)
- **Comprehensive Error Detection**: Identifies multiple error types:
  - XSD schema violations (missing elements, type mismatches, pattern violations, etc.)
  - Malformed XML (syntax errors, unclosed tags, invalid characters)
  - File-level issues (missing files, empty files, format errors)
- **Customizable Error Reporting**: Configure which error attributes to collect via `error_facets`:
  - `path` - XPath location of the error
  - `reason` - Explanation of the validation failure
  - `message` - Human-readable error message
  - `validator` - XSD component that failed
  - `schema_path` - Location in the XSD schema
  - And more (value, namespaces, domain, severity, etc.)
- **Flexible Test Behavior**: Control test case pass/fail behavior with `fail_on_errors` parameter
- **CSV Export**: Export collected errors to CSV files with optional timestamping
- **Batch Processing**: Always validates entire file sets, collecting all errors before reporting

### Advanced Features
- Support for XSD includes and imports with configurable `base_url`
- Pre-parsing option for performance optimization
- Global library scope for efficient schema reuse across test cases
- Helper keywords for schema and error management

## Project Structure

```
├── src/xmlvalidator/              # Main source code (2,638 lines)
│   ├── XmlValidator.py            # Main Robot Framework library (1,682 lines)
│   ├── xml_validator_results.py   # Results recording and reporting (413 lines)
│   ├── xml_validator_utils.py     # Utility functions (483 lines)
│   └── __init__.py                # Package initialization (60 lines)
│
├── test/                          # Test suite
│   ├── unit/                      # Pytest unit tests
│   │   ├── test_xmlvalidator.py
│   │   ├── test_xml_validator_results.py
│   │   └── test_xml_validator_utils.py
│   ├── integration/               # Robot Framework integration tests
│   │   ├── 00_helper_keywords.robot
│   │   ├── 01_library_initialization.robot
│   │   ├── 02_basic_validation.robot
│   │   ├── 03_error_handling.robot
│   │   ├── 04_schema_resolution.robot
│   │   ├── 05_advanced_validation_1.robot
│   │   ├── 06_advanced_validation_2.robot
│   │   └── validation_keywords.py
│   ├── demo/                      # Demo test suite
│   │   └── demo.robot
│   └── _data/                     # Test data (XML and XSD files)
│
├── docs/                          # Documentation
│   ├── XmlValidator.html          # Generated keyword documentation
│   └── images/                    # Diagrams and screenshots
│
├── .github/                       # GitHub configuration
│   ├── workflows/
│   │   ├── test.yml               # CI/CD test workflow
│   │   └── lint.yml               # Code quality workflow
│   └── ISSUE_TEMPLATE/
│
├── README.md                      # Comprehensive project documentation (37,482 lines)
├── CHANGELOG.md                   # Version history and release notes
├── ROADMAP.md                     # Future development plans
├── CONTRIBUTING.md                # Contribution guidelines
├── CODE_OF_CONDUCT.md             # Community standards
├── pyproject.toml                 # Poetry project configuration
├── Makefile                       # Development automation tasks
└── LICENSE                        # Apache 2.0 license
```

## Code Statistics

- **Total Files:** 4 Python modules in src/
- **Total Methods:** 27 (7 are Robot Framework user keywords, ~25%)
- **Total Lines:** 2,434
  - Code: ~600 lines (24%)
  - Comments: ~205 lines (8%)
  - Documentation: ~1,629 lines (68%)

The high documentation-to-code ratio reflects the library's focus on usability and clear API documentation.

## Architecture

### Main Components

1. **XmlValidator** (Main Library Class)
   - Entry point for Robot Framework
   - Manages schema loading and validation orchestration
   - Provides 7 public keywords for test cases

2. **ValidatorResultRecorder**
   - Collects and tracks validation errors
   - Logs summaries and detailed error reports
   - Exports errors to CSV format

3. **ValidatorUtils**
   - Utility functions for file handling
   - Namespace extraction and matching
   - Sanity checking of input files

4. **ValidatorResult**
   - Simple result wrapper for success/error states
   - Used internally for error handling

## Robot Framework Keywords

| Keyword                  | Purpose                                                         |
|--------------------------|----------------------------------------------------------------|
| `Validate Xml Files`     | Main validation keyword - validates XML against XSD            |
| `Reset Schema`           | Clears the currently loaded XSD schema                         |
| `Reset Errors`           | Clears collected errors                                        |
| `Get Schema`             | Retrieves current schema name or object                        |
| `Log Schema`             | Logs the currently loaded schema                               |
| `Get Error Facets`       | Returns active error facets                                    |
| `Reset Error Facets`     | Resets error facets to defaults                                |

## Installation Methods

```bash
# From PyPI
pip install robotframework-xmlvalidator

# From GitHub
pip install git+https://github.com/MichaelHallik/robotframework-xmlvalidator.git

# Using Poetry (for development)
poetry install
```

## Usage Example

```robotframework
*** Settings ***
Library    XmlValidator    xsd_path=path/to/schema.xsd    error_facets=path, reason

*** Test Cases ***
Validate Single XML File
    Validate Xml Files    path/to/file.xml

Validate Multiple Files With Schema Resolution
    Validate Xml Files    path/to/xml_folder/    
    ...                   path/to/xsd_folder/
    ...                   xsd_search_strategy=by_namespace
    ...                   write_to_csv=True
```

## Dependencies

### Runtime Dependencies
- **lxml** ^5.1.0 - XML processing
- **pandas** ^2.2.0 - CSV export functionality
- **robotframework** ^7.0.0 - Test framework
- **xmlschema** ^3.4.3 - XSD validation engine

### Development Dependencies
- **pytest** ^8.3.1 - Unit testing
- **pylint** ^3.1.0 - Code linting
- **pyright** ^1.1.357 - Static type checking
- **black** ^25.1.0 - Code formatting

## Development Workflow

### Running Tests
```bash
# Unit tests (pytest)
make unit
pytest test/unit/

# Integration tests (Robot Framework)
make robot
robot -d ./Results test/integration

# All tests and checks
make check
```

### Code Quality
```bash
# Linting
make lint
pylint src/ --exit-zero

# Type checking
make type
pyright --project pyrightconfig.json

# Format checking
make format
black src/ --check
```

### Generate Documentation
```bash
make keydoc
# Generates docs/XmlValidator.html
```

## Recent Changes (v2.0.0)

### Breaking Changes
- **Changed default `fail_on_errors` behavior**: Now defaults to `True`
  - Test cases with validation errors now FAIL by default
  - Previously defaulted to `False` (PASS even with errors)
  - Set `fail_on_errors=False` to preserve old behavior

### New Features
- `fail_on_errors` can now be set at library import level
- New demo test suite with 8 example test cases
- Added ROADMAP.md for planned features

### Improvements
- Updated integration tests for new fail_on_errors behavior
- Refined Robot Framework logging levels
- Enhanced documentation

## Continuous Integration

The project uses GitHub Actions for automated testing:
- **test.yml** - Runs unit and integration tests on multiple Python versions
- **lint.yml** - Enforces code quality with pylint, pyright, and black

## Future Plans (from ROADMAP.md)

### Ideas Under Consideration
- Separate error facets for malformed XML vs. XSD violations
- XSD 1.1 support (assertions, conditional types)
- Support for additional schema types (RelaxNG, Schematron)
- CLI runner for validation outside Robot Framework
- Additional export formats (JSON, XML)
- HTML table embedding in Robot Framework logs
- GUI frontend for non-technical users

## Contributing

The project welcomes contributions! See CONTRIBUTING.md for guidelines.

### Contribution Templates
- Bug reports: `.github/ISSUE_TEMPLATE/bug_report.md`
- Feature requests: `.github/ISSUE_TEMPLATE/feature_request.md`
- Pull requests: `.github/PULL_REQUEST_TEMPLATE.md`

### Code of Conduct
Contributors are expected to follow the project's Code of Conduct (CODE_OF_CONDUCT.md).

## Links and Resources

- **PyPI Package**: https://pypi.org/project/robotframework-xmlvalidator/
- **Repository**: https://github.com/MichaelHallik/robotframework-xmlvalidator
- **Keyword Documentation**: https://michaelhallik.github.io/robotframework-xmlvalidator/XmlValidator.html
- **Issues**: https://github.com/MichaelHallik/robotframework-xmlvalidator/issues
- **Author LinkedIn**: https://www.linkedin.com/in/michaelhallik/

## Key Differentiators

1. **Batch Processing**: Unlike many validation tools, this library processes all files before failing, providing comprehensive diagnostics
2. **Robot Framework Integration**: Native support for RF syntax and logging
3. **Flexible Error Reporting**: Customizable error facets allow tailored reporting for different use cases
4. **Dynamic Schema Matching**: Automatic XML-to-XSD pairing reduces manual configuration
5. **Production Ready**: Comprehensive test coverage (unit + integration), CI/CD, and thorough documentation

## Summary

The robotframework-xmlvalidator library is a mature, well-documented XML validation solution specifically designed for Robot Framework test automation. With its comprehensive error detection, flexible configuration, batch processing capabilities, and extensive documentation, it serves as a robust tool for teams needing reliable XML validation in their test suites. The project demonstrates strong engineering practices with good test coverage, automated CI/CD, clear contribution guidelines, and active maintenance.
