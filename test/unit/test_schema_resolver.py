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
Contains unit tests for the src/xmlvalidator/schema/resolver.py module.

See for an overview of all tests the file test/_doc/unit/overview.html.
"""

# pylint: disable=I1101:c-extension-no-member
# pylint: disable=W0212:protected-access

# Standard library imports.
from pathlib import Path
from unittest.mock import MagicMock, patch

# Third-party library imports.
import pytest
from lxml import etree

# Local application imports.
from xmlvalidator.results import ValidatorResult
from xmlvalidator.schema.manager import ValidatorSchemaManager
from xmlvalidator.schema.resolver import ValidatorSchemaResolver

schema_resolver_module = __import__(
    "xmlvalidator.schema.resolver",
    fromlist=[""]
)
xml_validator_module = schema_resolver_module

TEST_DIR = Path("test/_data/unit")


# build_validation_plan()


def test_build_validation_plan_single_xsd_success():
    """
    Test that build_validation_plan() correctly assigns a single XSD
    file to all XML files when only one XSD is provided.

    The method should assign `None` as the value for each XML key,
    signaling reuse of the already-loaded schema.

    Priority: M
    """
    # Define test XML and XSD files.
    xml_files = [Path("test1.xml"), Path("test2.xml"), Path("test3.xml")]
    xsd_file = Path("schema.xsd")

    with patch.object(
        schema_resolver_module, "get_file_paths",
        return_value=([xsd_file], True)
        ), \
         patch.object(xml_validator_module.logger, "info"): # Prevent console I/O.
        schema_manager = ValidatorSchemaManager()
        resolver = ValidatorSchemaResolver(schema_manager)
        with patch.object(
            schema_manager, "ensure_schema",
            return_value=ValidatorResult(success=True, error=None)
        ):
            result = resolver.build_validation_plan(
                xml_paths=xml_files,
                xsd_path=xsd_file,
                xsd_search_strategy=None
            )
            # Each XML file should be mapped to `None` (use loaded schema).
            for xml_file in xml_files:
                assert result[xml_file] is None

def test_build_validation_plan_namespace_matching_success():
    """
    Test that build_validation_plan() correctly assigns the correct XSD
    file to each XML file based on namespace matching.

    The test simulates a directory with multiple XSD files and uses
    a namespace-matching strategy to resolve which schema applies to
    which XML file.

    Priority: H
    """
    # Define test XML and XSD files.
    xml_files = [Path("test1.xml"), Path("test2.xml"), Path("test3.xml")]
    xsd_files = [Path("schema1.xsd"), Path("schema2.xsd"), Path("schema3.xsd")]
    # Simulated expected output from match_xml_files_to_schemas().
    expected_validations = {
        xml_files[0]: xsd_files[0],
        xml_files[1]: xsd_files[1],
        xml_files[2]: xsd_files[2],
    }
    with patch.object(
        schema_resolver_module, "get_file_paths",
        return_value=(xsd_files, False)
        ), \
         patch.object(
             ValidatorSchemaResolver, "match_xml_files_to_schemas",
             return_value=expected_validations
             ) as mock_match_xml_files_to_schemas, \
         patch.object(xml_validator_module.logger, "info"): # Suppress console logging.
        resolver = ValidatorSchemaResolver(ValidatorSchemaManager())
        result = resolver.build_validation_plan(
            xml_paths=xml_files,
            xsd_path="mock_xsd_folder", # Simulated directory.
            xsd_search_strategy="by_namespace"
        )
        # Ensure correct delegation to match_xml_files_to_schemas().
        mock_match_xml_files_to_schemas.assert_called_once_with(
            xml_files,
            xsd_files,
            "by_namespace",
            None,
            False
        )
        # Ensure returned result matches the expected mapping.
        assert result == expected_validations

def test_build_validation_plan_namespace_matching_failure():
    """
    Test that build_validation_plan() assigns FileNotFoundError to each
    XML file when no XSD file correctly matches the namespaces.

    Simulates a failed namespace resolution scenario where no XSD maps
    to any XML file.

    Priority: H
    """
    # Define test XML and XSD files.
    xml_files = [Path("test1.xml"), Path("test2.xml"), Path("test3.xml")]
    xsd_files = [Path("schema1.xsd"), Path("schema2.xsd"), Path("schema3.xsd")]
    # Simulate match_xml_files_to_schemas() returning a mapping with errors.
    expected_validations = {
        xml_file: FileNotFoundError(
            f"No matching XSD found for: {xml_file.stem}"
            )
        for xml_file in xml_files
    }
    with patch.object(
        schema_resolver_module, "get_file_paths",
        return_value=(xsd_files, False)
        ), \
         patch.object(
             ValidatorSchemaResolver, "match_xml_files_to_schemas",
             return_value=expected_validations
             ) as mock_match_xml_files_to_schemas, \
         patch.object(xml_validator_module.logger, "info"):
        resolver = ValidatorSchemaResolver(ValidatorSchemaManager())
        result = resolver.build_validation_plan(
            xml_paths=xml_files,
            xsd_path="mock_xsd_folder", # Simulated directory.
            xsd_search_strategy="by_namespace"
        )
        mock_match_xml_files_to_schemas.assert_called_once_with(
            xml_files, xsd_files, "by_namespace", None, False
        )
        # Each result should be a FileNotFoundError instance.
        for xml_file in xml_files:
            assert isinstance(result[xml_file], FileNotFoundError)

def test_build_validation_plan_filename_matching_success():
    """
    Test that build_validation_plan() correctly assigns the correct XSD file
    to each XML file based on filename matching (e.g., test1.xml → test1.xsd).

    Priority: H
    """
    # Define test XML and matching XSD files.
    xml_files = [Path("test1.xml"), Path("test2.xml"), Path("test3.xml")]
    xsd_files = [Path("test1.xsd"), Path("test2.xsd"), Path("test3.xsd")]
    # Expected output from match_xml_files_to_schemas().
    expected_validations = {
        xml_files[0]: xsd_files[0],
        xml_files[1]: xsd_files[1],
        xml_files[2]: xsd_files[2],
    }
    with patch.object(
        schema_resolver_module, "get_file_paths",
        return_value=(xsd_files, False)
        ), \
         patch.object(
             ValidatorSchemaResolver, "match_xml_files_to_schemas",
             return_value=expected_validations
             ) as mock_match_xml_files_to_schemas, \
         patch.object(xml_validator_module.logger, "info"):
        resolver = ValidatorSchemaResolver(ValidatorSchemaManager())
        result = resolver.build_validation_plan(
            xml_paths=xml_files,
            xsd_path="mock_xsd_folder", # Simulated directory.
            xsd_search_strategy="by_file_name"
        )
        mock_match_xml_files_to_schemas.assert_called_once_with(
            xml_files, xsd_files, "by_file_name", None, False
        )
        assert result == expected_validations

def test_build_validation_plan_filename_matching_failure():
    """
    Test that build_validation_plan() assigns FileNotFoundError to each
    XML file when no XSD file with a matching filename exists.

    Simulates a mismatch in filenames between .xml and .xsd files,
    resulting in an error for each XML.

    Priority: M
    """
    # Define XML files and non-matching XSDs.
    xml_files = [Path("file1.xml"), Path("file2.xml"), Path("file3.xml")]
    xsd_files = [Path("schema1.xsd"), Path("schema2.xsd"), Path("schema3.xsd")]
    expected_validations = {
        xml_file: FileNotFoundError(
            f"No matching XSD found for: {xml_file.stem}"
            )
        for xml_file in xml_files
    }
    with patch.object(
        schema_resolver_module,
        "get_file_paths", return_value=(xsd_files, False)
        ), \
         patch.object(
             ValidatorSchemaResolver, "match_xml_files_to_schemas",
             return_value=expected_validations
             ) as mock_match_xml_files_to_schemas, \
         patch.object(xml_validator_module.logger, "info"):
        resolver = ValidatorSchemaResolver(ValidatorSchemaManager())
        result = resolver.build_validation_plan(
            xml_paths=xml_files,
            xsd_path="mock_xsd_folder",
            xsd_search_strategy="by_file_name"
        )
        mock_match_xml_files_to_schemas.assert_called_once_with(
            xml_files, xsd_files, "by_file_name", None, False
        )
        for xml_file in xml_files:
            assert isinstance(result[xml_file], FileNotFoundError)

def test_build_validation_plan_invalid_strategy():
    """
    Test that build_validation_plan() raises a ValueError when an
    invalid xsd_search_strategy is provided.

    This test bypasses schema resolution logic to trigger the validation
    for unknown strategies directly.

    Priority: M
    """
    xml_files = [Path("file1.xml"), Path("file2.xml")]
    invalid_strategy = "invalid_strategy"
    with patch.object(
        schema_resolver_module, "get_file_paths",
        return_value=([], False) # Prevent early schema loading errors.
    ), patch.object(xml_validator_module.logger, "info"):
        resolver = ValidatorSchemaResolver(ValidatorSchemaManager())
        with pytest.raises(
            ValueError,
            match=f"Unsupported search strategy: {invalid_strategy}"
        ):
            resolver.build_validation_plan(
                xml_paths=xml_files,
                xsd_path="mock_xsd_folder",
                xsd_search_strategy=invalid_strategy # type: ignore
            )


# _build_xsd_path_plan()


def test_build_xsd_path_plan_single_schema_reuses_loaded_schema():
    """
    Test that _build_xsd_path_plan() loads a single XSD once and maps
    all XML files to None.

    Priority: M
    """
    xml_files = [Path("first.xml"), Path("second.xml")]
    xsd_file = Path("schema.xsd")
    schema_manager = ValidatorSchemaManager()
    resolver = ValidatorSchemaResolver(schema_manager)

    with patch.object(
        schema_resolver_module,
        "get_file_paths",
        return_value=([xsd_file], True)
    ), patch.object(
        schema_manager,
        "ensure_schema",
        return_value=ValidatorResult(success=True, value=MagicMock())
    ) as mock_ensure_schema:
        result = resolver._build_xsd_path_plan(
            xml_files,
            xsd_file,
            None,
            None,
            False
        )

    mock_ensure_schema.assert_called_once_with(xsd_file, None)
    assert result == {
        xml_files[0]: None,
        xml_files[1]: None
    }


# _build_loaded_schema_plan()


def test_build_loaded_schema_plan_maps_each_xml_to_none():
    """
    Test that _build_loaded_schema_plan() maps each XML file to None.

    None signals that the validation step should reuse the schema that
    is already loaded in the schema manager.

    Priority: M
    """
    xml_files = [Path("first.xml"), Path("second.xml")]

    result = ValidatorSchemaResolver._build_loaded_schema_plan(xml_files)

    assert result == {
        xml_files[0]: None,
        xml_files[1]: None
    }


# match_xml_files_to_schemas()


def test_match_xml_files_to_schemas_namespace_matching_success():
    """
    Test that match_xml_files_to_schemas() correctly assigns an XSD file when the XML
    and XSD share the same namespace, using mocks instead of real files.

    Priority: H
    """
    xml_file = Path("test.xml")
    xsd_file = Path("schema.xsd")
    # Simulate the XML root element's namespace.
    mock_xml_root = MagicMock()
    mock_xml_root.nsmap = {"ns": "http://example.com/schema"}
    mock_schema = MagicMock()
    mock_schema.target_namespace = "http://example.com/schema"
    mock_schema.imports = {}
    mock_schema.namespaces = {}
    with patch.object(
        schema_resolver_module.etree, "parse"
    ) as mock_parse, patch.object(
        ValidatorSchemaManager, "load_schema",
        return_value=ValidatorResult(success=True, value=mock_schema)
    ), patch.object(
        schema_resolver_module, "extract_namespaces",
        return_value={"http://example.com/schema"}
    ), patch.object(
        xml_validator_module.logger, "info"
    ):
        # Configure XML parse mock to return the mocked root.
        mock_parse.return_value.getroot.return_value = mock_xml_root
        resolver = ValidatorSchemaResolver(ValidatorSchemaManager())
        result = resolver.match_xml_files_to_schemas(
            xml_file_paths=[xml_file],
            xsd_file_paths=[xsd_file],
            search_by="by_namespace"
        )
        assert result[xml_file] == xsd_file, (
            f"Expected {xsd_file}; got {result[xml_file]}"
        )

def test_match_xml_files_to_schemas_namespace_matching_failure():
    """
    Test that match_xml_files_to_schemas() returns a FileNotFoundError when no XSD
    schema matches the XML namespace.

    Priority: H
    """
    xml_file = Path("test.xml")
    xsd_file = Path("schema.xsd")

    # XML has a non-matching namespace.
    mock_xml_root = MagicMock()
    mock_xml_root.nsmap = {"ns": "http://example.com/non_matching"}
    mock_schema = MagicMock()
    mock_schema.target_namespace = "http://example.com/schema"
    mock_schema.imports = {}
    mock_schema.namespaces = {}
    with patch.object(
        schema_resolver_module.etree, "parse"
    ) as mock_parse, patch.object(
        ValidatorSchemaManager, "load_schema",
        return_value=ValidatorResult(success=True, value=mock_schema)
    ), patch.object(
        schema_resolver_module, "extract_namespaces",
        return_value={"http://example.com/non_matching"}
    ), patch.object(
        xml_validator_module.logger, "info"
    ):
        mock_parse.return_value.getroot.return_value = mock_xml_root
        resolver = ValidatorSchemaResolver(ValidatorSchemaManager())
        result = resolver.match_xml_files_to_schemas(
            xml_file_paths=[xml_file],
            xsd_file_paths=[xsd_file],
            search_by="by_namespace"
        )
        assert isinstance(result[xml_file], FileNotFoundError), (
            f"Expected FileNotFoundError but got {result[xml_file]}"
        )

def test_match_xml_files_to_schemas_filename_matching_success():
    """
    Test that match_xml_files_to_schemas() correctly assigns an XSD file when the XML
    and XSD share the same filename (excluding extension).

    Priority: H
    """
    xml_file = TEST_DIR / "test.xml"
    xsd_file = TEST_DIR / "test.xsd"
    with patch.object(xml_validator_module.logger, "info"):
        resolver = ValidatorSchemaResolver(ValidatorSchemaManager())
        result = resolver.match_xml_files_to_schemas(
            xml_file_paths=[xml_file],
            xsd_file_paths=[xsd_file],
            search_by="by_file_name"
        )
    assert result[xml_file] == xsd_file, (
        f"Expected {xsd_file}; got {result[xml_file]}"
    )

def test_match_xml_files_to_schemas_filename_matching_failure():
    """
    Test that match_xml_files_to_schemas() fails to assign an XSD file when no XSD
    file has a matching filename.

    Priority: H
    """
    xml_file = Path("test.xml")
    xsd_file = Path("different_schema.xsd")
    with patch.object(xml_validator_module.logger, "info"):
        resolver = ValidatorSchemaResolver(ValidatorSchemaManager())
        result = resolver.match_xml_files_to_schemas(
            xml_file_paths=[xml_file],
            xsd_file_paths=[xsd_file],
            search_by="by_file_name"
        )
    assert isinstance(result[xml_file], FileNotFoundError)

def test_match_xml_files_to_schemas_invalid_xml():
    """
    Test that match_xml_files_to_schemas() logs an error and fails gracefully when
    the XML file is malformed or unreadable (e.g., raises XMLSyntaxError).

    Priority: M
    """
    xml_file = Path("invalid.xml")
    xsd_file = Path("schema.xsd")
    with patch.object(
        schema_resolver_module.etree, "parse",
        side_effect=etree.XMLSyntaxError(
            "Invalid XML", "<string>", 0, 0, filename="invalid.xml"
        )
    ), patch.object(
        xml_validator_module.logger, "info"
    ) as mock_info:
        resolver = ValidatorSchemaResolver(ValidatorSchemaManager())
        result = resolver.match_xml_files_to_schemas(
            xml_file_paths=[xml_file],
            xsd_file_paths=[xsd_file],
            search_by="by_namespace"
        )
        assert isinstance(result[xml_file], Exception)
        mock_info.assert_any_call('\t\tProcessing XML file failed.')

def test_match_xml_files_to_schemas_invalid_xsd():
    """
    Test that match_xml_files_to_schemas() logs an error and stores an OSError when
    the XML file cannot be read (e.g., due to file system issues).

    Priority: M
    """
    xml_file = Path("valid.xml")
    xsd_file = Path("invalid_schema.xsd")
    with patch.object(
        schema_resolver_module.etree, "parse",
        side_effect=OSError("Error reading file 'valid.xml'")
    ), patch.object(
        xml_validator_module.logger, "info"
    ) as mock_info:
        resolver = ValidatorSchemaResolver(ValidatorSchemaManager())
        result = resolver.match_xml_files_to_schemas(
            xml_file_paths=[xml_file],
            xsd_file_paths=[xsd_file],
            search_by="by_namespace"
        )
        # Ensure the XML file is mapped to the OSError.
        assert isinstance(result[xml_file], OSError)
        # Ensure the correct log message was issued.
        mock_info.assert_any_call('\t\tProcessing XML file failed.')


# _match_xml_file_to_schema_by_namespace()


def test_match_xml_file_to_schema_by_namespace_success():
    """
    Test that _match_xml_file_to_schema_by_namespace() returns the XSD
    file whose namespace matches the XML namespace.

    Priority: M
    """
    xml_file = Path("customer.xml")
    xsd_file = Path("customer.xsd")
    schema_manager = ValidatorSchemaManager()
    resolver = ValidatorSchemaResolver(schema_manager)

    with patch.object(
        schema_resolver_module.etree,
        "parse"
    ) as mock_parse, patch.object(
        schema_resolver_module,
        "extract_namespaces",
        return_value={"http://example.com/customer"}
    ), patch.object(
        schema_manager,
        "load_schema",
        return_value=ValidatorResult(success=True, value=MagicMock())
    ), patch.object(
        schema_resolver_module,
        "schema_matches_xml_namespaces",
        return_value=True
    ), patch.object(
        xml_validator_module.logger,
        "info"
    ):
        mock_parse.return_value.getroot.return_value = MagicMock()
        result = resolver._match_xml_file_to_schema_by_namespace(
            xml_file,
            [xsd_file],
            None,
            False
        )

    assert result == xsd_file


# _match_xml_file_to_schema_by_file_name()


def test_match_xml_file_to_schema_by_file_name_success():
    """
    Test that _match_xml_file_to_schema_by_file_name() returns the XSD
    file whose stem matches the XML file's stem.

    Priority: M
    """
    xml_file = Path("customer.xml")
    matching_xsd = Path("customer.xsd")
    non_matching_xsd = Path("order.xsd")

    with patch.object(xml_validator_module.logger, "info"):
        result = ValidatorSchemaResolver._match_xml_file_to_schema_by_file_name(
            xml_file,
            [non_matching_xsd, matching_xsd]
        )

    assert result == matching_xsd

def test_match_xml_file_to_schema_by_file_name_failure():
    """
    Test that _match_xml_file_to_schema_by_file_name() returns None
    when no XSD file has the same stem as the XML file.

    Priority: M
    """
    xml_file = Path("customer.xml")
    xsd_file = Path("order.xsd")

    with patch.object(xml_validator_module.logger, "info"):
        result = ValidatorSchemaResolver._match_xml_file_to_schema_by_file_name(
            xml_file,
            [xsd_file]
        )

    assert result is None
