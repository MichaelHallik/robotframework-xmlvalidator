# Changelog

All notable changes to the project will be documented in this file.

## [1.0.0] - 2025-04-04
- Implement Robot Framework test library for XML validation against XSD schemas.
- Add unit tests using pytest.
- Add integration tests using Robot Framework.
- Add user and technical documentation.
- Add Makefile for standard development tasks.
- Add GitHub Actions for CI/CD.
- Use Poetry for dependency and release management.

## [1.0.1] - 2025-06-09
- Refactor: simplify the __init_() method of class XmlValidator

## [2.0.0] - 2025-06-14

### Breaking changes

- Changed default behavior of the `fail_on_errors` setting.
  - When using the `Validate Xml Files` keyword, test cases that detect validation errors (of any kind) will have FAIL status.
  - Previously, test cases received a PASS status, even when validation errors were found, unless `fail_on_errors=True` was explicitly set.
  - This change improves alignment with common validation expectations and was motivated by user feedback.
  - To preserve the old behavior, explicitly set `fail_on_errors=False` either during library import or per keyword call:
  
    ```robot
    Library    XmlValidator    fail_on_errors=False
    ```

    Or:

    ```robot
    Validate Xml Files    path/to/file.xml    fail_on_errors=False
    ```

Note:

The library's batch validation behavior remains unchanged. That is, `fail_on_errors=True` does *not* short-circuit the validation process in any way.

For example
- If you validate fifteen XML files and five of them contain schema violations or other errors, all files will still be processed.
- Errors are simply collected throughout the run and reported collectively, only after the final file has been (fully) processed.
- The test case will fail (assuming `fail_on_errors=True`) only after all files have been checked, ensuring comprehensive diagnostics.

### Added

- Support for setting `fail_on_errors` also at the *library import level*
  - Applies to all calls to `Validate Xml Files` unless explicitly overridden during keyword call (see also earlier/above).
  - Improves usability and test readability.

- New Robot Framework demo test suite containing 8 self-contained test cases.
  - Demonstrates key features:
    - Single and batch XML validation
    - Schema matching by filename and namespace
    - Custom error facets
    - Malformed XML handling
    - XSD includes/imports
    - CSV export
  - Serves as a quickstart reference for users exploring the library.

- `ROADMAP.md` to document planned features and/or improvements.

### Changed

- Integration test suite updated to support and validate the new `fail_on_errors` behavior.
  - Tests now reflect expected `FAIL` or `PASS` statuses depending on configuration.
  - Verifies both default (library-level) and keyword-level overrides.
- Minor changes in the Robot Framework logging (based on user feedback).
  - Changed some from level=WARN to level=INFO.
  - Some got commented out.
  - Some indentation changes as well.
- Changed documentation (READEME.md, keyword documentation, etc.) to reflect additions and changes in this version.