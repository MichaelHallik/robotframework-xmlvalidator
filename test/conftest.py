"""
conftest.py - Shared pytest fixtures for XML Validator tests.

This module defines reusable pytest fixtures for setting up test files 
and other common test utilities used across multiple test modules.

Pytest automatically discovers fixtures defined in `conftest.py`, making 
them available in all test modules within the same directory (and 
subdirectories) without requiring explicit imports.

Fixtures:

- `setup_test_files`
   Creates temporary XML and XSD files for testing:
   - Generates test files dynamically based on provided content.
   - Ensures test directory (`test/files/`) exists before file creation.
   - Yields file paths for use in test functions.
   - Cleans up files after each test to prevent conflicts.

Usage Example in a Test:

    def test_example(setup_test_files):
        xml_content = "<root><element>Hello</element></root>"
        xsd_content = "<xs:schema>...</xs:schema>"
        xml_file, xsd_file = next(
            setup_test_files(xml_content, xsd_content)
            )
        assert xml_file.exists()
        assert xsd_file.exists()

Notes:
- This file should only contain **test-related setup logic** (e.g., 
  fixtures, hooks).
- Avoid including actual test functions here.
"""


# Standard library imports.
from pathlib import Path
from typing import Optional
# Third-party library imports.
import pytest


# Define a directory for test files.
TEST_DIR = Path("test/_data/unit")


@pytest.fixture
def setup_test_files():
    """
    Creates XML and XSD files dynamically based on provided content.
    Ensures cleanup after the test.
    """
    TEST_DIR.mkdir(parents=True, exist_ok=True)

    def _create_files(
        xml_content: str,
        xsd_content: Optional[str],
        create_empty_xml_file: bool = False,
        create_empty_xsd_file: bool = False
        ):
        """
        Inner function that allows dynamic creation of test XML and XSD 
        files. Allows optional creation of an empty file instead of 
        treating it as missing.
        """
        # Set up the file paths.
        xml_path = TEST_DIR / "test.xml"
        xsd_path = TEST_DIR / "test.xsd"
        # Handle XML file creation based on parameters.
        if xml_content is not None:
            # Create a file if explicitly requested.
            xml_path.write_text(xml_content, encoding="utf-8")
        elif create_empty_xml_file:
            # Create an empty file if explicitly requested.
            xml_path.touch()
        else:
            # Facilitate expecting a missing file.
            xml_path = None
        # Handle XSD file creation based on parameters.
        if xsd_content is not None:
            # Create a file if explicitly requested.
            xsd_path.write_text(xsd_content, encoding="utf-8")
        elif create_empty_xsd_file:
            # Create an empty file if explicitly requested.
            xsd_path.touch()
        else:
            # Facilitate expecting a missing file.
            xsd_path = None
        # Yield file paths to the test function.
        yield xml_path, xsd_path
        # Cleanup after the test.
        if xml_path and xml_path.exists():
            xml_path.unlink(missing_ok=True)
        if xsd_path and xsd_path.exists():
            xsd_path.unlink(missing_ok=True)
    # Return the function reference.
    return _create_files
