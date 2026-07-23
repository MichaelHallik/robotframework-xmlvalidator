# Copyright 2024-2026 Michael Hallik
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Contains unit tests for the src/xmlvalidator/files.py module.

See for an overview of all tests the file test/_doc/unit/overview.html.
"""

# pylint: disable=I1101:c-extension-no-member
# pylint: disable=W0212:protected-access

# Standard library imports.
from pathlib import Path

# Third-party library imports.
import pytest
from lxml import etree

# Local application imports.
from xmlvalidator.files import (
    _append_file_error,
    _check_file_path,
    _extract_error_details,
    _parse_file_for_sanity_check,
    sanity_check_files,
)

TEST_DIR = Path("test/_data/unit")


# sanity_check_files()


def test_sanity_check_files_accepts_valid_xml_and_xsd(setup_test_files):
    """
    Test that sanity_check_files() returns success when given valid,
    well-formed XML and XSD files.

    Priority: H
    """
    # Define a well-formed XML that conforms to the schema.
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <note>
        <message>Hello, World!</message>
    </note>"""
    # Define a well-formed XSD schema.
    xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
        <xs:element name="note">
            <xs:complexType>
                <xs:sequence>
                    <xs:element name="message" type="xs:string"/>
                </xs:sequence>
            </xs:complexType>
        </xs:element>
    </xs:schema>"""
    # Dynamically create test files.
    xml_file, xsd_file = next(
        setup_test_files(xml_content, xsd_content)
        )
    # Call `sanity_check_files()` with valid XML and XSD.
    result = sanity_check_files(
        [xml_file, xsd_file], parse_files=True
        )
    # Expect a successful validation.
    assert result.success is True
    # Ensure there are no errors.
    assert result.error is None or len(result.error) == 0

def test_sanity_check_files_reports_malformed_xml(setup_test_files):
    """
    Test that sanity_check_files() correctly detects a malformed XML
    file.

    Priority: H
    """
    # Define an XSD schema (valid).
    xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
        <xs:element name="note">
            <xs:complexType>
                <xs:sequence>
                    <xs:element name="message" type="xs:string"/>
                </xs:sequence>
            </xs:complexType>
        </xs:element>
    </xs:schema>"""
    # Define a malformed XML file (missing closing tag for <note>).
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <note>
        <message>Hello, World!</message>"""  # Missing </note>
    # Dynamically create test files.
    xml_file, _ = next( setup_test_files(xml_content, xsd_content) )
    # Call sanity_check_files() with `parse_files=True` to enable XML parsing.
    result = sanity_check_files( [xml_file], parse_files=True )
    # Expect validation failure (sanity check should detect malformed XML).
    assert result.success is False, "Expected failure due to malformed XML."
    # Ensure error is a list and contains exactly one error.
    assert isinstance(result.error, list), "Expected errors to be a list."
    assert len(result.error) == 1, (
        f"Expected 1 error; got {len(result.error)}."
        )
    # Extract the first (and only) error dictionary.
    error = result.error[0]
    assert isinstance(error, dict), "Expected error to be a dictionary."
    # Make sure the dict holds the correct nr of items.
    assert len(error) == 5, (
        f'Expected 5 keys in error dict; got {len(error)}: {list(error.keys())}'
        )
    # Assert individual fields in the error dictionary.
    ### Field 1: 'file'.
    assert "file" in error, "'file' key is missing in the error dictionary."
    assert error["file"] == str(xml_file), (
        f"Expected file path '{xml_file}'; got '{error['file']}'."
        )
    ### Field 2: 'reason'.
    assert "reason" in error, (
        "'reason' key is missing in the error dictionary."
        )
    assert error["reason"] == "File parsing failed.", (
        f"Unexpected reason: {error['reason']}."
        )
    ### Field 3: 'Error type'.
    assert "Error type" in error, (
        "'Error type' key is missing in the error dictionary."
        )
    assert error["Error type"] in ["XMLSyntaxError", "ParseError"], (
        f"Expected 'XMLSyntaxError' or 'ParseError'; got '{error['Error type']}'."
        )
    ### Field 4: 'position'.
    assert "position" in error, (
        "'position' key is missing in the error dictionary."
        )
    assert "Line " in error["position"], (
        f"Expected line number in field 'position'; got '{error['position']}'."
        )
    ### Field 5: 'msg'.
    assert "msg" in error, "'msg' key is missing in the error dictionary."
    assert isinstance(error["msg"], str) and len(error["msg"]) > 0, (
        "Expected a descriptive error message for 'msg'."
        )
    assert "Premature end of data in tag" in error["msg"], (
        f"Expected 'Premature end of data in tag' to be in 'msg'; got '{error['msg']}'."
        )

def test_sanity_check_files_reports_malformed_xsd(setup_test_files):
    """
    Test that sanity_check_files() correctly detects a malformed XSD
    file.

    Priority: H
    """
    # Define a **valid** XML file.
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <note>
        <message>Hello, World!</message>
    </note>"""
    # Define a **malformed** XSD schema (missing closing tag for <xs:schema>).
    xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
        <xs:element name="note">
            <xs:complexType>
                <xs:sequence>
                    <xs:element name="message" type="xs:string"/>
                </xs:sequence>
            </xs:complexType>
        </xs:element>"""  # Missing </xs:schema>.
    # Dynamically create test files.
    xml_file, xsd_file = next( setup_test_files(xml_content, xsd_content) )
    # Call sanity_check_files() with `parse_files=True` to enable XSD parsing.
    result = sanity_check_files(
        [xml_file, xsd_file], parse_files=True
        )
    # Expect validation failure (sanity check should detect malformed XSD).
    assert result.success is False, "Expected failure due to malformed XSD."
    # Ensure error is a list and contains exactly one error.
    assert isinstance(result.error, list), "Expected errors to be a list."
    assert len(result.error) == 1, (
        f"Expected 1 error, but got {len(result.error)}."
        )
    # Extract the first (and only) error dictionary.
    error = result.error[0]
    assert isinstance(error, dict), "Expected error to be a dictionary."
    # Ensure error dict has exactly 5 keys.
    assert len(error) == 5, (
        f"Expected 5 keys in error dict; got {len(error)}: {list(error.keys())}")
    # Assert individual fields in the error dictionary.
    ### Field 1: 'file'.
    assert "file" in error, "'file' key is missing in the error dictionary."
    assert error["file"] == str(xsd_file), (
        f"Expected file path '{xsd_file}'; got '{error['file']}'."
        )
    ### Field 2: 'reason'.
    assert "reason" in error, (
        "'reason' key is missing in the error dictionary."
        )
    assert error["reason"] == "File parsing failed.", (
        f"Unexpected reason: {error['reason']}."
        )
    ### Field 3: 'Error type'.
    assert "Error type" in error, (
        "'Error type' key is missing in the error dictionary."
        )
    assert error["Error type"] == "XMLSyntaxError", (
        f"Expected 'XMLSyntaxError'; got '{error['Error type']}'."
        )
    ### Field 4: 'position'.
    assert "position" in error, "'position' key is missing in the error dict."
    assert "Line " in error["position"], (
        f"Expected line number in field 'position'; got '{error['position']}'."
        )
    ### Field 5: 'msg'.
    assert "msg" in error, "'msg' key is missing in the error dictionary."
    assert isinstance(error["msg"], str) and len(error["msg"]) > 0, (
        "Expected a descriptive error message for 'msg'."
        )
    assert "Premature end of data in tag" in error["msg"], (
        f"Expected 'Premature end of data in tag' to be in 'msg'; got '{error['msg']}'."
        )

def test_sanity_check_files_reports_missing_file():
    """
    Test that sanity_check_files() correctly detects and reports a
    missing file.

    Priority: H
    """
    # Define a non-existent file path.
    missing_file = Path("test/files/missing.xml")
    # Call the function under test.
    result = sanity_check_files([missing_file])
    # Ensure validation has failed.
    assert result.success is False, "Expected failure due to missing file."
    # Ensure error is a list and contains exactly one error.
    assert isinstance(result.error, list), "Expected errors to be a list."
    assert len(result.error) == 1, (
        f"Expected 1 error, but got {len(result.error)}."
        )
    # Extract the first (and only) error dictionary.
    error = result.error[0]
    assert isinstance(error, dict), "Expected error to be a dictionary."
    # Make sure the dict holds the correct nr of items.
    assert len(error) == 3, (
        f"Expected 3 keys in error dict; got {len(error)}: {list(error.keys())}."
        )
    # Assert individual fields in the error dictionary.
    assert "file" in error, "'file' key is missing in the error dictionary."
    assert error["file"] == str(missing_file), (
        f"Expected file path '{missing_file}'; got '{error['file']}'."
        )
    assert "reason" in error, (
        "'reason' key is missing in the error dictionary."
        )
    assert error["reason"] == "The xml file does not exist.", (
        f"Unexpected reason: {error['reason']}."
        )
    assert "Error type" in error, (
        "'Error type' key is missing in the error dictionary."
        )
    assert error["Error type"] == "OSError", (
        f"Expected 'OSError', but got '{error['Error type']}'."
        )

def test_sanity_check_files_reports_empty_file(setup_test_files):
    """
    Test that sanity_check_files() correctly detects an empty XML or XSD
    file.

    Priority: M
    """
    # Define valid XML content.
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <note>
        <message>Hello, World!</message>
    </note>"""
    # Define an **empty** XSD file.
    xsd_content = ""
    # Dynamically create test files (valid XML + empty XSD).
    xml_file, xsd_file = next( setup_test_files(xml_content, xsd_content) )
    assert xsd_file is not None, (
        f"Expected XSD file to be created, but got {xsd_file}."
        )
    # Call sanity_check_files() to check for an empty file.
    result = sanity_check_files([xml_file, xsd_file])
    # Expect validation failure (sanity check should detect empty file).
    assert result.success is False, "Expected failure due to an empty file."
    # Ensure error is a list and contains exactly one error.
    assert isinstance(result.error, list), "Expected errors to be a list."
    assert len(result.error) == 1, (
        f"Expected 1 error, but got {len(result.error)}."
        )
    # Extract the first (and only) error dictionary.
    error = result.error[0]
    assert isinstance(error, dict), "Expected error to be a dictionary."
    # Ensure error dict has exactly 3 keys.
    assert len(error) == 3, (
        f"Expected 3 keys in error dict; got {len(error)}: {list(error.keys())}."
        )
    # Assert individual fields in the error dictionary.
    ### Field 1: 'file'.
    assert "file" in error, "'file' key is missing in the error dictionary."
    assert error["file"] == str(xsd_file), (
        f"Expected file path '{xsd_file}', but got '{error['file']}'."
        )
    ### Field 2: 'reason'.
    assert "reason" in error, (
        "'reason' key is missing in the error dictionary."
        )
    assert error["reason"] == "File is empty.", (
        f"Unexpected reason: {error['reason']}."
        )
    ### Field 3: 'Error type'.
    assert "Error type" in error, (
        "'Error type' key is missing in the error dictionary."
        )
    assert error["Error type"] == "ValueError", (
        f"Expected 'ValueError', but got '{error['Error type']}'."
        )

def test_sanity_check_files_reports_unsupported_file_type():
    """
    Test that sanity_check_files() correctly detects an unsupported file
    type.

    Priority: M
    """
    # Define valid XML content (for control purposes).
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <note>
        <message>Hello, World!</message>
    </note>"""
    # Define an unsupported file extension (.txt).
    unsupported_file = TEST_DIR / "invalid.txt"
    unsupported_file.write_text( xml_content, encoding="utf-8" )
    # Call sanity_check_files() with an unsupported file type.
    result = sanity_check_files([unsupported_file])
    # Expect validation failure (unsupported file type should be detected).
    assert result.success is False, (
        "Expected failure due to unsupported file type."
        )
    # Ensure error is a list and contains exactly one error.
    assert isinstance(result.error, list), "Expected errors to be a list."
    assert len(result.error) == 1, (
        f"Expected 1 error, but got {len(result.error)}."
        )
    # Extract the first (and only) error dictionary.
    error = result.error[0]
    assert isinstance(error, dict), "Expected error to be a dictionary."
    # Ensure error dict has exactly 3 keys.
    assert len(error) == 3, (
        f"Expected 3 keys in error dict; got {len(error)}: {list(error.keys())}."
        )
    # Assert individual fields in the error dictionary.
    ### Field 1: 'file'.
    assert "file" in error, "'file' key is missing in the error dictionary."
    assert error["file"] == str(unsupported_file), (
        f"Expected file path '{unsupported_file}'; got '{error['file']}'."
        )
    ### Field 2: 'reason'.
    assert "reason" in error, (
        "'reason' key is missing in the error dictionary."
        )
    assert error["reason"] == f"Unsupported file type: {unsupported_file.suffix}.", (
        f"Unexpected reason: {error['reason']}."
        )
    ### Field 3: 'Error type'.
    assert "Error type" in error, (
        "'Error type' key is missing in the error dictionary."
        )
    assert error["Error type"] == "ValueError", (
        f"Expected 'ValueError'; got '{error['Error type']}'."
        )
    # Cleanup the created unsupported file.
    unsupported_file.unlink(missing_ok=True)


# _check_file_path()


def test_check_file_path_returns_none_for_valid_file(tmp_path):
    """
    Test that _check_file_path() returns None when the file has a
    supported extension, exists and is not empty.

    Priority: M
    """
    # Create a non-empty XML file.
    xml_file = tmp_path / "valid.xml"
    xml_file.write_text("<root />", encoding="utf-8")
    # Call the helper with the lowercase file extension.
    error = _check_file_path(xml_file, ".xml")
    # Expect no error for a processable file.
    assert error is None, (
        f"Expected no file path error; got {error}."
    )

def test_check_file_path_reports_unsupported_file_type(tmp_path):
    """
    Test that _check_file_path() returns an error dictionary when the
    file extension is not supported.

    Priority: M
    """
    # Create a file with an unsupported extension.
    unsupported_file = tmp_path / "invalid.txt"
    unsupported_file.write_text("not XML or XSD", encoding="utf-8")
    # Call the helper with the unsupported file extension.
    error = _check_file_path(unsupported_file, ".txt")
    # Ensure an error dictionary was returned.
    assert error is not None, "Expected an error dictionary; got None."
    # Assert individual fields in the error dictionary.
    assert error["file"] == str(unsupported_file), (
        f"Expected file path '{unsupported_file}'; got '{error['file']}'."
    )
    assert error["reason"] == "Unsupported file type: .txt.", (
        f"Unexpected reason: {error['reason']}."
    )
    assert error["Error type"] == "ValueError", (
        f"Expected 'ValueError'; got '{error['Error type']}'."
    )

def test_check_file_path_reports_missing_file(tmp_path):
    """
    Test that _check_file_path() returns an error dictionary when the
    file does not exist.

    Priority: H
    """
    # Create a path object that points to a missing XML file.
    missing_file = tmp_path / "missing.xml"
    # Call the helper with a supported file extension.
    error = _check_file_path(missing_file, ".xml")
    # Ensure an error dictionary was returned.
    assert error is not None, "Expected an error dictionary; got None."
    # Assert individual fields in the error dictionary.
    assert error["file"] == str(missing_file), (
        f"Expected file path '{missing_file}'; got '{error['file']}'."
    )
    assert error["reason"] == "The xml file does not exist.", (
        f"Unexpected reason: {error['reason']}."
    )
    assert error["Error type"] == "OSError", (
        f"Expected 'OSError'; got '{error['Error type']}'."
    )

def test_check_file_path_reports_empty_file(tmp_path):
    """
    Test that _check_file_path() returns an error dictionary when the
    file exists but is empty.

    Priority: M
    """
    # Create an empty XSD file.
    empty_file = tmp_path / "empty.xsd"
    empty_file.write_text("", encoding="utf-8")
    # Call the helper with a supported file extension.
    error = _check_file_path(empty_file, ".xsd")
    # Ensure an error dictionary was returned.
    assert error is not None, "Expected an error dictionary; got None."
    # Assert individual fields in the error dictionary.
    assert error["file"] == str(empty_file), (
        f"Expected file path '{empty_file}'; got '{error['file']}'."
    )
    assert error["reason"] == "File is empty.", (
        f"Unexpected reason: {error['reason']}."
    )
    assert error["Error type"] == "ValueError", (
        f"Expected 'ValueError'; got '{error['Error type']}'."
    )


# _parse_file_for_sanity_check()


def test_parse_file_for_sanity_check_does_nothing_when_disabled(tmp_path):
    """
    Test that _parse_file_for_sanity_check() does not parse the file
    when parse_files is False.

    Priority: M
    """
    # Create malformed XML content that would fail if parsing happened.
    xml_file = tmp_path / "invalid.xml"
    xml_file.write_text("<root>", encoding="utf-8")
    # Call the helper with parsing disabled.
    _parse_file_for_sanity_check(
        xml_file,
        ".xml",
        None,
        False
    )

def test_parse_file_for_sanity_check_parses_valid_xml(tmp_path):
    """
    Test that _parse_file_for_sanity_check() accepts a well-formed XML
    file when parsing is enabled.

    Priority: M
    """
    # Create a well-formed XML file.
    xml_file = tmp_path / "valid.xml"
    xml_file.write_text("<root />", encoding="utf-8")
    # Call the helper with parsing enabled.
    _parse_file_for_sanity_check(
        xml_file,
        ".xml",
        None,
        True
    )

def test_parse_file_for_sanity_check_raises_for_invalid_xml(tmp_path):
    """
    Test that _parse_file_for_sanity_check() raises a parsing error for
    malformed XML content.

    Priority: H
    """
    # Create malformed XML content.
    xml_file = tmp_path / "invalid.xml"
    xml_file.write_text("<root>", encoding="utf-8")
    # Expect lxml to raise an XML parsing exception.
    with pytest.raises((etree.ParseError, etree.XMLSyntaxError)):
        _parse_file_for_sanity_check(
            xml_file,
            ".xml",
            None,
            True
        )

def test_parse_file_for_sanity_check_compiles_valid_xsd(tmp_path):
    """
    Test that _parse_file_for_sanity_check() accepts a well-formed and
    valid XSD schema when parsing is enabled.

    Priority: H
    """
    # Create a valid XSD schema.
    xsd_file = tmp_path / "valid.xsd"
    xsd_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
        <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
            <xs:element name="root" type="xs:string"/>
        </xs:schema>""",
        encoding="utf-8"
    )
    # Call the helper with parsing enabled.
    _parse_file_for_sanity_check(
        xsd_file,
        ".xsd",
        None,
        True
    )

def test_parse_file_for_sanity_check_raises_for_invalid_xsd(tmp_path):
    """
    Test that _parse_file_for_sanity_check() raises a schema parsing
    error for a well-formed but invalid XSD schema.

    Priority: H
    """
    # Create a well-formed XML document that is not a valid XSD schema.
    xsd_file = tmp_path / "invalid.xsd"
    xsd_file.write_text("<root />", encoding="utf-8")
    # Expect lxml to reject the document as an XSD schema.
    with pytest.raises(etree.XMLSchemaParseError):
        _parse_file_for_sanity_check(
            xsd_file,
            ".xsd",
            None,
            True
        )


# _extract_error_details()


def test_extract_error_details_uses_default_facets():
    """
    Test that _extract_error_details() uses the configured default
    facets when no explicit facets are provided.

    Priority: H
    """
    # Create an exception with a custom message attribute.
    error = Exception("Parsing failed.")
    error.msg = "Opening and ending tag mismatch." # type: ignore
    # Define the default facets for the error type.
    default_facets = {
        Exception: ["msg"]
    }
    # Call the helper without explicit facets.
    error_details = _extract_error_details(
        error,
        None,
        default_facets
    )
    # Ensure the configured default facet was extracted.
    assert error_details["msg"] == "Opening and ending tag mismatch.", (
        f"Unexpected msg: {error_details['msg']}."
    )
    # Ensure the error type is always included.
    assert error_details["Error type"] == "Exception", (
        f"Expected 'Exception'; got '{error_details['Error type']}'."
    )

def test_extract_error_details_uses_explicit_facets():
    """
    Test that _extract_error_details() uses explicit facets when they
    are provided.

    Priority: H
    """
    # Create an exception with two custom attributes.
    error = Exception("Parsing failed.")
    error.msg = "Opening and ending tag mismatch." # type: ignore
    error.filename = "invalid.xml" # type: ignore
    # Define defaults that should be ignored because explicit facets are used.
    default_facets = {
        Exception: ["msg"]
    }
    # Call the helper with an explicit facet list.
    error_details = _extract_error_details(
        error,
        ["filename"],
        default_facets
    )
    # Ensure the explicit facet was extracted.
    assert error_details["filename"] == "invalid.xml", (
        f"Unexpected filename: {error_details['filename']}."
    )
    # Ensure the default facet was not extracted.
    assert "msg" not in error_details, (
        f"Unexpected default facet in error details: {error_details}."
    )
    # Ensure the error type is always included.
    assert error_details["Error type"] == "Exception", (
        f"Expected 'Exception'; got '{error_details['Error type']}'."
    )

def test_extract_error_details_formats_tuple_values():
    """
    Test that _extract_error_details() formats tuple values such as
    parser positions in a readable way.

    Priority: M
    """
    # Create an exception with a tuple-valued position attribute.
    error = Exception("Parsing failed.")
    error.position = (7, 15) # type: ignore
    # Define the default facets for the error type.
    default_facets = {
        Exception: ["position"]
    }
    # Call the helper without explicit facets.
    error_details = _extract_error_details(
        error,
        None,
        default_facets
    )
    # Ensure the tuple-valued facet was formatted consistently.
    assert error_details["position"] == "Line 7, Column 15.", (
        f"Unexpected position: {error_details['position']}."
    )
    # Ensure the error type is always included.
    assert error_details["Error type"] == "Exception", (
        f"Expected 'Exception'; got '{error_details['Error type']}'."
    )

def test_extract_error_details_keeps_none_values_by_default():
    """
    Test that _extract_error_details() keeps facets whose value is None
    by default and reports them as unavailable.

    Priority: H
    """
    # Create an exception with a None-valued custom attribute.
    error = Exception("Parsing failed.")
    error.filename = None # type: ignore
    # Define the default facets for the error type.
    default_facets = {
        Exception: ["filename"]
    }
    # Call the helper without overriding the default behavior.
    error_details = _extract_error_details(
        error,
        None,
        default_facets
    )
    # Ensure the None-valued facet was preserved as a user-friendly value.
    assert "filename" in error_details, (
        f"Expected filename facet in error details: {error_details}."
    )
    assert error_details["filename"] == "Unavailable", (
        f"Expected filename to be Unavailable; got {error_details['filename']}."
    )
    # Ensure the error type is still included.
    assert error_details["Error type"] == "Exception", (
        f"Expected 'Exception'; got '{error_details['Error type']}'."
    )

def test_extract_error_details_can_skip_none_values():
    """
    Test that _extract_error_details() can omit facets whose value is
    None when explicitly requested.

    Priority: H
    """
    # Create an exception with a None-valued custom attribute.
    error = Exception("Parsing failed.")
    error.filename = None # type: ignore
    # Define the default facets for the error type.
    default_facets = {
        Exception: ["filename"]
    }
    # Call the helper and explicitly skip None-valued facets.
    error_details = _extract_error_details(
        error,
        None,
        default_facets,
        skip_none_error_facets=True
    )
    # Ensure the None-valued facet was omitted.
    assert "filename" not in error_details, (
        f"Unexpected None-valued facet in error details: {error_details}."
    )
    # Ensure the error type is still included.
    assert error_details["Error type"] == "Exception", (
        f"Expected 'Exception'; got '{error_details['Error type']}'."
    )


# _append_file_error()


def test_append_file_error_adds_required_error_fields():
    """
    Test that _append_file_error() appends an error dictionary with
    the required file and reason fields.

    Priority: M
    """
    # Create an empty error list, mirroring sanity_check_files().
    errors: list[dict[str, str | None]] = []
    # Create a sample path. The file does not need to exist for this helper.
    file_path = Path("sample.xml")
    # Call the helper with only the required error information.
    _append_file_error(
        errors,
        file_path,
        "File is empty."
    )
    # Ensure exactly one error was appended.
    assert len(errors) == 1, (
        f"Expected exactly one error; got {len(errors)}."
    )
    # Extract the generated error dictionary.
    error = errors[0]
    # Ensure the generated error contains exactly the required fields.
    assert len(error) == 2, (
        f"Expected 2 keys in error dict; got {len(error)}: {list(error.keys())}."
    )
    ### Field 1: 'file'.
    assert "file" in error, "'file' key is missing in the error dictionary."
    assert error["file"] == str(file_path), (
        f"Expected file path '{file_path}'; got '{error['file']}'."
    )
    ### Field 2: 'reason'.
    assert "reason" in error, (
        "'reason' key is missing in the error dictionary."
    )
    assert error["reason"] == "File is empty.", (
        f"Unexpected reason: {error['reason']}."
    )

def test_append_file_error_adds_optional_error_details():
    """
    Test that _append_file_error() appends optional error details to
    the generated error dictionary.

    Priority: M
    """
    # Create an empty error list, mirroring sanity_check_files().
    errors: list[dict[str, str | None]] = []
    # Create a sample path. The file does not need to exist for this helper.
    file_path = Path("sample.xsd")
    # Define optional details that should be merged into the error dict.
    additional_details: dict[str, str | None] = {
        "Error type": "XMLSyntaxError",
        "msg": "Opening and ending tag mismatch."
    }
    # Call the helper with required and optional error information.
    _append_file_error(
        errors,
        file_path,
        "File parsing failed.",
        additional_details
    )
    # Ensure exactly one error was appended.
    assert len(errors) == 1, (
        f"Expected exactly one error; got {len(errors)}."
    )
    # Extract the generated error dictionary.
    error = errors[0]
    # Ensure the generated error contains the required and optional fields.
    assert len(error) == 4, (
        f"Expected 4 keys in error dict; got {len(error)}: {list(error.keys())}."
    )
    ### Field 1: 'file'.
    assert "file" in error, "'file' key is missing in the error dictionary."
    assert error["file"] == str(file_path), (
        f"Expected file path '{file_path}'; got '{error['file']}'."
    )
    ### Field 2: 'reason'.
    assert "reason" in error, (
        "'reason' key is missing in the error dictionary."
    )
    assert error["reason"] == "File parsing failed.", (
        f"Unexpected reason: {error['reason']}."
    )
    ### Field 3: 'Error type'.
    assert "Error type" in error, (
        "'Error type' key is missing in the error dictionary."
    )
    assert error["Error type"] == "XMLSyntaxError", (
        f"Expected 'XMLSyntaxError'; got '{error['Error type']}'."
    )
    ### Field 4: 'msg'.
    assert "msg" in error, "'msg' key is missing in the error dictionary."
    assert error["msg"] == "Opening and ending tag mismatch.", (
        f"Unexpected msg: {error['msg']}."
    )
