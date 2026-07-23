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
Contains unit tests for the src/xmlvalidator/paths.py module.

See for an overview of all tests the file test/_doc/unit/overview.html.
"""

# Third-party library imports.
import pytest

# Local application imports.
from xmlvalidator.paths import get_file_paths

# get_file_paths()

def test_get_file_paths_returns_single_file_path_for_file_input(tmp_path):
    """
    Test that get_file_paths() returns a single file path and True
    when the provided path points directly to a file.

    Priority: H
    """
    # Create one XML file in pytest's temporary test folder.
    xml_file = tmp_path / "single.xml"
    xml_file.write_text("<root />", encoding="utf-8")
    # Call the method under test with a string path.
    file_paths, single_file = get_file_paths(
        str(xml_file),
        "xml"
    )
    # Ensure the resolved file path is returned.
    assert file_paths == [xml_file.resolve()], (
        f"Expected {[xml_file.resolve()]}; got {file_paths}."
    )
    # Ensure the method reports that exactly one file was found.
    assert single_file is True, (
        f"Expected single_file to be True; got {single_file}."
    )

def test_get_file_paths_returns_sorted_matching_files_for_directory_input(tmp_path):
    """
    Test that get_file_paths() returns only matching files from a
    directory, sorted in deterministic order.

    Priority: H
    """
    # Create matching XML files in reverse alphabetical order.
    second_xml_file = tmp_path / "b.xml"
    second_xml_file.write_text("<root />", encoding="utf-8")
    first_xml_file = tmp_path / "a.xml"
    first_xml_file.write_text("<root />", encoding="utf-8")
    # Create a non-matching XSD file, which should be ignored.
    xsd_file = tmp_path / "schema.xsd"
    xsd_file.write_text("<schema />", encoding="utf-8")
    # Call the method under test with a directory path.
    file_paths, single_file = get_file_paths(
        tmp_path,
        "xml"
    )
    # Ensure only the XML files are returned, in sorted order.
    assert file_paths == [first_xml_file, second_xml_file], (
        f"Expected sorted XML files; got {file_paths}."
    )
    # Ensure the method reports that more than one file was found.
    assert single_file is False, (
        f"Expected single_file to be False; got {single_file}."
    )

def test_get_file_paths_reports_single_match_for_directory_with_one_matching_file(
    tmp_path
):
    """
    Test that get_file_paths() returns True when a directory contains
    exactly one file with the requested extension.

    Priority: M
    """
    # Create exactly one matching XSD file.
    xsd_file = tmp_path / "schema.xsd"
    xsd_file.write_text("<schema />", encoding="utf-8")
    # Create a non-matching XML file, which should be ignored.
    xml_file = tmp_path / "document.xml"
    xml_file.write_text("<root />", encoding="utf-8")
    # Call the method under test for XSD files.
    file_paths, single_file = get_file_paths(
        tmp_path,
        "xsd"
    )
    # Ensure only the matching XSD file is returned.
    assert file_paths == [xsd_file], (
        f"Expected only '{xsd_file}'; got {file_paths}."
    )
    # Ensure the method reports that exactly one matching file was found.
    assert single_file is True, (
        f"Expected single_file to be True; got {single_file}."
    )

def test_get_file_paths_normalizes_extension_argument(tmp_path):
    """
    Test that get_file_paths() accepts file extensions with a leading
    dot and mixed letter casing.

    Priority: M
    """
    # Create one XML file with the normalized lowercase extension.
    xml_file = tmp_path / "document.xml"
    xml_file.write_text("<root />", encoding="utf-8")
    # Call the method under test with a leading dot and mixed casing.
    file_paths, single_file = get_file_paths(
        tmp_path,
        ".XML"
    )
    # Ensure the extension argument was normalized before matching.
    assert file_paths == [xml_file], (
        f"Expected only '{xml_file}'; got {file_paths}."
    )
    # Ensure the method reports that exactly one matching file was found.
    assert single_file is True, (
        f"Expected single_file to be True; got {single_file}."
    )

def test_get_file_paths_raises_value_error_for_empty_directory_match(
    tmp_path
):
    """
    Test that get_file_paths() raises ValueError when a directory has
    no files with the requested extension.

    Priority: H
    """
    # Create a file with a different extension, so no XML files match.
    xsd_file = tmp_path / "schema.xsd"
    xsd_file.write_text("<schema />", encoding="utf-8")
    # Expect a clear error when no matching XML files are found.
    with pytest.raises(
        ValueError,
        match=r"No \.xml files found in folder:"
    ):
        _ = get_file_paths(tmp_path, "xml")

def test_get_file_paths_raises_value_error_for_missing_path(tmp_path):
    """
    Test that get_file_paths() raises ValueError when the provided
    path is neither an existing file nor an existing directory.

    Priority: H
    """
    # Create a path object that points to nothing.
    missing_path = tmp_path / "missing.xml"
    # Expect a clear error for a path that is neither file nor folder.
    with pytest.raises(
        ValueError,
        match="The provided path is neither a file nor a folder:"
    ):
        _ = get_file_paths(missing_path, "xml")
