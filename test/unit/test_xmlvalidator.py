# Copyright 2024-2025 Michael Hallik
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
Contains the unit tests for the XmlValidator class in the 
src/xmlvalidator/XmlValidator.py module.

The method validate_xml_files(), which implements the keyword, does not 
have unit tests. This method is just a thin, simple wrapper and will, as 
such, be tested in the integration tests.

See for an overview of all tests the file test/_doc/unit/overview.html.
"""

# pylint: disable=I1101 # Missing C-extension member warning.
# pylint: disable=W0212:protected-access # On account of our unit tests having to access private methods.
# pylint: disable=C0413:wrong-import-position # On account of a false positive for lines 48/49.


# === Standard library imports ===
from pathlib import Path
import re
import importlib
from unittest.mock import MagicMock, patch
from xmlschema import XMLSchemaValidationError
from xmlschema.validators import XsdValidator # Import a valid validator type
# === Third-party library imports ===
import pytest
from lxml import etree
# === Local application imports ===
# Main class under test — used directly in test cases
from xmlvalidator import XmlValidator
# Module reference (not class) used for patching module-level attributes,
#  like XMLSchema, logger, etc.
xml_validator_module = importlib.import_module("xmlvalidator.XmlValidator")
# Supporting classes used internally by XmlValidator
from xmlvalidator.xml_validator_results import ValidatorResult, ValidatorResultRecorder
from xmlvalidator.xml_validator_utils import ValidatorUtils


# === Test constants ===
TEST_DIR = Path("test/_data/unit")


# === Tests ===

def test_init_with_xsd():
    """
    Test that the XmlValidator initializes correctly when provided with 
    a valid XSD schema.

    This test mocks the file path resolution, the XMLSchema loader,
    and the logger to ensure correct schema loading behavior and logging.

    Priority: H
    """
    with patch(
        "xmlvalidator.xml_validator_utils.ValidatorUtils.get_file_paths",
        return_value=([Path("schema.xsd")], True)
    ), patch.object(
        xml_validator_module, "XMLSchema"
    ) as mock_xmlschema, patch.object(
        xml_validator_module.logger, "info"
    ) as mock_info, patch.object(
        xml_validator_module.logger, "console" # Avoid WinError 6 during tests.
    ):
        # Act: Instantiate with a valid schema path.
        validator = XmlValidator(xsd_path="schema.xsd")
        # Assert: Schema was set correctly.
        mock_schema_instance = mock_xmlschema.return_value
        mock_xmlschema.assert_called_once_with(
            Path("schema.xsd"), base_url=None
        )
        assert validator.schema is mock_schema_instance
        # Assert: Logging behavior (check 'info' calls instead of 'warn').
        mock_info.assert_any_call(
            "Collecting error facets: ['path', 'reason'].",
            also_console=True
            )
        mock_info.assert_any_call(
            "XML Validator ready for use!",
            also_console=True
            )

def test_init_without_xsd():
    """
    Test that the XmlValidator initializes correctly when no XSD
    schema is provided, ensuring informative logs are emitted.

    Priority: H
    """
    with patch.object(xml_validator_module.logger, "info") as mock_info, \
         patch.object(xml_validator_module.logger, "console"): # Avoid console errors.
        # Instantiate the validator with no schema.
        validator = XmlValidator()
        # Assert schema is explicitly set to None.
        assert validator.schema is None
        # Check expected logger.info() calls
        mock_info.assert_any_call(
            "No XSD schema set: provide schema(s) during keyword calls.",
            also_console=True
        )
        mock_info.assert_any_call(
            "Collecting error facets: ['path', 'reason'].",
            also_console=True
        )
        mock_info.assert_any_call(
            "XML Validator ready for use!",
            also_console=True
        )

def test_init_multiple_xsd():
    """
    Test that the XmlValidator raises a ValueError when multiple XSD
    files are found in a directory during initialization.

    The helper method get_file_paths() returns a list of multiple .xsd 
    files, simulating an invalid schema preloading scenario.

    Priority: H
    """
    with patch.object(
        xml_validator_module.ValidatorUtils, "get_file_paths",
        return_value=([Path("schema1.xsd"), Path("schema2.xsd")], False)
    ):
        with pytest.raises(ValueError, match="Got multiple xsd files"):
            XmlValidator(xsd_path="schemas_folder/")

def test_init_invalid_xsd_path():
    """
    Test that the XmlValidator raises a ValueError when an invalid
    XSD path is provided during initialization.

    Simulates an invalid input by making get_file_paths() raise a 
    ValueError directly.

    Priority: H
    """
    with patch.object(
        xml_validator_module.ValidatorUtils, "get_file_paths",
        side_effect=ValueError("Invalid XSD path")
    ):
        with pytest.raises(ValueError, match="Invalid XSD path"):
            XmlValidator(xsd_path="invalid_path/")

def test_init_attributes():
    """
    Test that XmlValidator initializes its attributes correctly.

    Priority: H
    """
    with patch.object(xml_validator_module.logger, "info"), \
         patch.object(xml_validator_module.logger, "console"):
        validator = XmlValidator()
        assert isinstance(validator.validator_results, ValidatorResultRecorder)
        assert isinstance(validator.validator_utils, ValidatorUtils)
        assert validator.schema is None
        assert validator.error_facets == ['path', 'reason']

def test_init_logs_correct_facets():
    """
    Test that XmlValidator logs the correct error facets when custom
    error_facets are passed during initialization.

    Priority: L
    """
    with patch.object(xml_validator_module.logger, "info") as mock_info:
        _ = XmlValidator(error_facets=["path", "message"])
        mock_info.assert_any_call(
            "Collecting error facets: ['path', 'message'].",
            also_console=True
            )
        mock_info.assert_any_call(
            "XML Validator ready for use!", also_console=True
            )

def test_init_schema_load_failure():
    """
    Test that the XmlValidator raises a SystemError when schema
    loading fails due to an invalid or unreadable XSD file.

    This test mocks get_file_paths to return a valid XSD path,
    but _load_schema to simulate a failure result.

    Priority: H
    """
    with patch.object(
        xml_validator_module.ValidatorUtils, "get_file_paths",
        return_value=([Path("invalid_schema.xsd")], True)
    ), patch.object(
        XmlValidator, "_load_schema",
        return_value=ValidatorResult(False, "Schema load error")
    ):
        with pytest.raises(SystemError, match="Loading of schema failed"):
            XmlValidator(xsd_path="invalid_schema.xsd")

def test_init_file_access_error():
    """
    Test that the XmlValidator raises an IOError when the XSD file
    cannot be accessed due to file system restrictions (e.g., permissions).

    This test mocks _load_schema to raise an IOError directly.

    Priority: M
    """
    with patch.object(
        xml_validator_module.ValidatorUtils, "get_file_paths",
        return_value=([Path("restricted_schema.xsd")], True)
    ), patch.object(
        XmlValidator, "_load_schema",
        side_effect=IOError("Permission denied")
    ):
        with pytest.raises(IOError, match="Permission denied"):
            XmlValidator(xsd_path="restricted_schema.xsd")

# _determine_validations()

def test_determine_validations_single_xsd_success():
    """
    Test that _determine_validations() correctly assigns a single XSD 
    file to all XML files when only one XSD is provided.

    The method should assign `None` as the value for each XML key, 
    signaling reuse of the already-loaded schema.

    Priority: M
    """
    # Define test XML and XSD files.
    xml_files = [Path("test1.xml"), Path("test2.xml"), Path("test3.xml")]
    xsd_file = Path("schema.xsd")

    with patch.object(
        xml_validator_module.ValidatorUtils, "get_file_paths",
        return_value=([xsd_file], True)
        ), \
         patch.object(xml_validator_module.logger, "info"): # Prevent console I/O.
        validator = XmlValidator()
        with patch.object(
            validator, "_ensure_schema",
            return_value=ValidatorResult(success=True, error=None)
        ):
            result = validator._determine_validations(
                xml_paths=xml_files,
                xsd_path=xsd_file,
                xsd_search_strategy=None
            )
            # Each XML file should be mapped to `None` (use loaded schema).
            for xml_file in xml_files:
                assert result[xml_file] is None

def test_determine_validations_namespace_matching_success():
    """
    Test that _determine_validations() correctly assigns the correct XSD 
    file to each XML file based on namespace matching.

    The test simulates a directory with multiple XSD files and uses
    a namespace-matching strategy to resolve which schema applies to
    which XML file.

    Priority: H
    """
    # Define test XML and XSD files.
    xml_files = [Path("test1.xml"), Path("test2.xml"), Path("test3.xml")]
    xsd_files = [Path("schema1.xsd"), Path("schema2.xsd"), Path("schema3.xsd")]
    # Simulated expected output from _find_schemas().
    expected_validations = {
        xml_files[0]: xsd_files[0],
        xml_files[1]: xsd_files[1],
        xml_files[2]: xsd_files[2],
    }
    with patch.object(
        xml_validator_module.ValidatorUtils, "get_file_paths",
        return_value=(xsd_files, False)
        ), \
         patch.object(
             XmlValidator, "_find_schemas",
             return_value=expected_validations
             ) as mock_find_schemas, \
         patch.object(xml_validator_module.logger, "info"): # Suppress console logging.
        validator = XmlValidator()
        result = validator._determine_validations(
            xml_paths=xml_files,
            xsd_path="mock_xsd_folder", # Simulated directory.
            xsd_search_strategy="by_namespace"
        )
        # Ensure correct delegation to _find_schemas().
        mock_find_schemas.assert_called_once_with(
            xml_files,
            xsd_files,
            "by_namespace",
            None
        )
        # Ensure returned result matches the expected mapping.
        assert result == expected_validations

def test_determine_validations_namespace_matching_failure():
    """
    Test that _determine_validations() assigns FileNotFoundError to each 
    XML file when no XSD file correctly matches the namespaces.

    Simulates a failed namespace resolution scenario where no XSD maps
    to any XML file.

    Priority: H
    """
    # Define test XML and XSD files.
    xml_files = [Path("test1.xml"), Path("test2.xml"), Path("test3.xml")]
    xsd_files = [Path("schema1.xsd"), Path("schema2.xsd"), Path("schema3.xsd")]
    # Simulate _find_schemas() returning a mapping with errors.
    expected_validations = {
        xml_file: FileNotFoundError(
            f"No matching XSD found for: {xml_file.stem}"
            )
        for xml_file in xml_files
    }
    with patch.object(
        xml_validator_module.ValidatorUtils, "get_file_paths",
        return_value=(xsd_files, False)
        ), \
         patch.object(
             XmlValidator, "_find_schemas",
             return_value=expected_validations
             ) as mock_find_schemas, \
         patch.object(xml_validator_module.logger, "info"):
        validator = XmlValidator()
        result = validator._determine_validations(
            xml_paths=xml_files,
            xsd_path="mock_xsd_folder", # Simulated directory.
            xsd_search_strategy="by_namespace"
        )
        mock_find_schemas.assert_called_once_with(
            xml_files, xsd_files, "by_namespace", None
        )
        # Each result should be a FileNotFoundError instance.
        for xml_file in xml_files:
            assert isinstance(result[xml_file], FileNotFoundError)

def test_determine_validations_filename_matching_success():
    """
    Test that _determine_validations() correctly assigns the correct XSD file
    to each XML file based on filename matching (e.g., test1.xml → test1.xsd).

    Priority: H
    """
    # Define test XML and matching XSD files.
    xml_files = [Path("test1.xml"), Path("test2.xml"), Path("test3.xml")]
    xsd_files = [Path("test1.xsd"), Path("test2.xsd"), Path("test3.xsd")]
    # Expected output from _find_schemas().
    expected_validations = {
        xml_files[0]: xsd_files[0],
        xml_files[1]: xsd_files[1],
        xml_files[2]: xsd_files[2],
    }
    with patch.object(
        xml_validator_module.ValidatorUtils, "get_file_paths",
        return_value=(xsd_files, False)
        ), \
         patch.object(
             XmlValidator, "_find_schemas",
             return_value=expected_validations
             ) as mock_find_schemas, \
         patch.object(xml_validator_module.logger, "info"):
        validator = XmlValidator()
        result = validator._determine_validations(
            xml_paths=xml_files,
            xsd_path="mock_xsd_folder", # Simulated directory.
            xsd_search_strategy="by_file_name"
        )
        mock_find_schemas.assert_called_once_with(
            xml_files, xsd_files, "by_file_name", None
        )
        assert result == expected_validations

def test_determine_validations_filename_matching_failure():
    """
    Test that _determine_validations() assigns FileNotFoundError to each 
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
        xml_validator_module.ValidatorUtils,
        "get_file_paths", return_value=(xsd_files, False)
        ), \
         patch.object(
             XmlValidator, "_find_schemas",
             return_value=expected_validations
             ) as mock_find_schemas, \
         patch.object(xml_validator_module.logger, "info"):
        validator = XmlValidator()
        result = validator._determine_validations(
            xml_paths=xml_files,
            xsd_path="mock_xsd_folder",
            xsd_search_strategy="by_file_name"
        )
        mock_find_schemas.assert_called_once_with(
            xml_files, xsd_files, "by_file_name", None
        )
        for xml_file in xml_files:
            assert isinstance(result[xml_file], FileNotFoundError)

def test_determine_validations_invalid_strategy():
    """
    Test that _determine_validations() raises a ValueError when an 
    invalid xsd_search_strategy is provided.

    This test bypasses schema resolution logic to trigger the validation 
    for unknown strategies directly.

    Priority: M
    """
    xml_files = [Path("file1.xml"), Path("file2.xml")]
    invalid_strategy = "invalid_strategy"
    with patch.object(
        xml_validator_module.ValidatorUtils, "get_file_paths",
        return_value=([], False) # Prevent early schema loading errors.
    ), patch.object(xml_validator_module.logger, "info"):
        validator = XmlValidator()
        with pytest.raises(
            ValueError,
            match=f"Unsupported search strategy: {invalid_strategy}"
        ):
            validator._determine_validations(
                xml_paths=xml_files,
                xsd_path="mock_xsd_folder",
                xsd_search_strategy=invalid_strategy # type: ignore
            )

# _ensure_schema()

def test_ensure_schema_keep_existing():
    """
    Test that _ensure_schema() retains an already loaded schema when 
    no new schema path is provided, ensuring the correct log message 
    is issued.

    Priority: H
    """
    with patch.object(XmlValidator, "_load_schema") as mock_load_schema, \
         patch.object(xml_validator_module.logger, "info") as mock_info:
        # Create a validator instance and simulate a pre-loaded schema.
        validator = XmlValidator()
        validator.schema = "mock_schema"
        result = validator._ensure_schema()
        # Ensure no reloading occurred.
        mock_load_schema.assert_not_called()
        assert result.success is True
        assert result.value == "mock_schema"
        # Verify correct log message.
        mock_info.assert_any_call(
            "No new schema set: keeping existing schema mock_schema."
        )

def test_ensure_schema_load_new_schema():
    """
    Test that _ensure_schema() correctly loads a new schema when a 
    valid XSD path is provided, ensuring the correct log message is 
    issued.

    Priority: H
    """
    with patch.object(
        XmlValidator, "_load_schema",
        return_value=ValidatorResult(success=True, value="new_schema")
    ) as mock_load_schema, patch.object(
        xml_validator_module.logger, "info"
    ) as mock_info:
        validator = XmlValidator()
        result = validator._ensure_schema(xsd_path=Path("schema.xsd"))
        mock_load_schema.assert_called_once_with(Path("schema.xsd"), None)
        assert result.success is True
        assert result.value == "new_schema"
        mock_info.assert_any_call(
            "Setting schema file: schema.xsd.", also_console=True
            )

def test_ensure_schema_no_existing_or_new_schema():
    """
    Test that _ensure_schema() raises a ValueError when neither an 
    existing schema nor a new schema path is available.

    Priority: M
    """
    with patch.object(xml_validator_module.logger, "info"):
        validator = XmlValidator()
        with pytest.raises(ValueError, match="No schema: provide an XSD path"):
            validator._ensure_schema()

def test_ensure_schema_replace_existing_schema():
    """
    Test that _ensure_schema() replaces an existing schema when a new 
    valid XSD path is provided, ensuring the correct log message is 
    issued.

    Priority: H
    """
    with patch.object(
        XmlValidator,
        "_load_schema",
        return_value=ValidatorResult(success=True, value="new_schema")
    ) as mock_load_schema, patch.object(
        xml_validator_module.logger, "info"
    ) as mock_info:
        validator = XmlValidator()
        validator.schema = "old_schema"
        result = validator._ensure_schema(xsd_path=Path("new_schema.xsd"))
        mock_load_schema.assert_called_once_with(Path("new_schema.xsd"), None)
        assert result.success is True
        assert result.value == "new_schema"
        mock_info.assert_any_call(
            "Setting new schema file: new_schema.xsd.", also_console=True
            )

def test_ensure_schema_load_failure():
    """
    Test that _ensure_schema() returns a failure result when schema 
    loading fails, ensuring the correct log message is issued.

    Priority: M
    """
    with patch.object(
        XmlValidator, "_load_schema",
        return_value=ValidatorResult(success=False, error="Schema load error")
    ) as mock_load_schema, patch.object(
        xml_validator_module.logger, "info"
    ) as mock_info:
        validator = XmlValidator()
        result = validator._ensure_schema(xsd_path=Path("invalid.xsd"))
        mock_load_schema.assert_called_once_with(Path("invalid.xsd"), None)
        assert result.success is False
        assert result.error == "Schema load error"
        mock_info.assert_any_call(
            "Setting schema file: invalid.xsd.", also_console=True
            )

# _find_schemas()

def test_find_schemas_namespace_matching_success():
    """
    Test that _find_schemas() correctly assigns an XSD file when the XML 
    and XSD share the same namespace, using mocks instead of real files.

    Priority: H
    """
    xml_file = Path("test.xml")
    xsd_file = Path("schema.xsd")
    # Simulate the XML root element's namespace.
    mock_xml_root = MagicMock()
    mock_xml_root.nsmap = {"ns": "http://example.com/schema"}
    with patch.object(
        xml_validator_module.etree, "parse"
    ) as mock_parse, patch.object(
        xml_validator_module, "XMLSchema"
    ) as mock_xsd_schema, patch.object(
        xml_validator_module.ValidatorUtils, "extract_xml_namespaces",
        return_value={"http://example.com/schema"}
    ), patch.object(
        xml_validator_module.logger, "info"
    ):
        # Configure XML parse mock to return the mocked root.
        mock_parse.return_value.getroot.return_value = mock_xml_root
        # Simulate a schema with a matching namespace.
        mock_xsd_schema.return_value.target_namespace = "http://example.com/schema"
        validator = XmlValidator()
        result = validator._find_schemas(
            xml_file_paths=[xml_file],
            xsd_file_paths=[xsd_file],
            search_by="by_namespace"
        )
        assert result[xml_file] == xsd_file, f"Expected {xsd_file}; got {result[xml_file]}"

def test_find_schemas_namespace_matching_failure():
    """
    Test that _find_schemas() returns a FileNotFoundError when no XSD 
    schema matches the XML namespace.

    Priority: H
    """
    xml_file = Path("test.xml")
    xsd_file = Path("schema.xsd")

    # XML has a non-matching namespace.
    mock_xml_root = MagicMock()
    mock_xml_root.nsmap = {"ns": "http://example.com/non_matching"}
    with patch.object(
        xml_validator_module.etree, "parse"
    ) as mock_parse, patch.object(
        xml_validator_module, "XMLSchema"
    ) as mock_xsd_schema, patch.object(
        xml_validator_module.ValidatorUtils, "extract_xml_namespaces",
        return_value={"http://example.com/non_matching"}
    ), patch.object(
        xml_validator_module.logger, "info"
    ):
        mock_parse.return_value.getroot.return_value = mock_xml_root
        # XSD schema has a different target namespace.
        mock_xsd_schema.return_value.target_namespace = "http://example.com/schema"
        validator = XmlValidator()
        result = validator._find_schemas(
            xml_file_paths=[xml_file],
            xsd_file_paths=[xsd_file],
            search_by="by_namespace"
        )
        assert isinstance(result[xml_file], FileNotFoundError), (
            f"Expected FileNotFoundError but got {result[xml_file]}"
        )

def test_find_schemas_filename_matching_success():
    """
    Test that _find_schemas() correctly assigns an XSD file when the XML 
    and XSD share the same filename (excluding extension).

    Priority: H
    """
    xml_file = TEST_DIR / "test.xml"
    xsd_file = TEST_DIR / "test.xsd"
    with patch.object(xml_validator_module.logger, "info"):
        validator = XmlValidator()
        result = validator._find_schemas(
            xml_file_paths=[xml_file],
            xsd_file_paths=[xsd_file],
            search_by="by_file_name"
        )
    assert result[xml_file] == xsd_file, f"Expected {xsd_file}; got {result[xml_file]}"

def test_find_schemas_filename_matching_failure():
    """
    Test that _find_schemas() fails to assign an XSD file when no XSD 
    file has a matching filename.

    Priority: H
    """
    xml_file = Path("test.xml")
    xsd_file = Path("different_schema.xsd")
    with patch.object(xml_validator_module.logger, "info"):
        validator = XmlValidator()
        result = validator._find_schemas(
            xml_file_paths=[xml_file],
            xsd_file_paths=[xsd_file],
            search_by="by_file_name"
        )
    assert isinstance(result[xml_file], FileNotFoundError)

def test_find_schemas_invalid_xml():
    """
    Test that _find_schemas() logs an error and fails gracefully when 
    the XML file is malformed or unreadable (e.g., raises XMLSyntaxError).

    Priority: M
    """
    xml_file = Path("invalid.xml")
    xsd_file = Path("schema.xsd")
    with patch.object(
        xml_validator_module.etree, "parse",
        side_effect=etree.XMLSyntaxError(
            "Invalid XML", "<string>", 0, 0, filename="invalid.xml"
        )
    ), patch.object(
        xml_validator_module.logger, "warn"
    ) as mock_warn, patch.object(
        xml_validator_module.logger, "info"
    ):
        validator = XmlValidator()
        result = validator._find_schemas(
            xml_file_paths=[xml_file],
            xsd_file_paths=[xsd_file],
            search_by="by_namespace"
        )
        # Ensure an exception was captured for the failing XML file.
        assert isinstance(result[xml_file], Exception)
        # Ensure an appropriate warning was logged.
        mock_warn.assert_any_call("Processing XML file failed.")

def test_find_schemas_invalid_xsd():
    """
    Test that _find_schemas() logs an error and stores an OSError when 
    the XML file cannot be read (e.g., due to file system issues).

    Priority: M
    """
    xml_file = Path("valid.xml")
    xsd_file = Path("invalid_schema.xsd")
    with patch.object(
        xml_validator_module.etree, "parse",
        side_effect=OSError("Error reading file 'valid.xml'")
    ), patch.object(
        xml_validator_module.logger, "warn"
    ) as mock_warn, patch.object(
        xml_validator_module.logger, "info"
    ):
        validator = XmlValidator()
        result = validator._find_schemas(
            xml_file_paths=[xml_file],
            xsd_file_paths=[xsd_file],
            search_by="by_namespace"
        )
        # Ensure the XML file is mapped to the OSError.
        assert isinstance(result[xml_file], OSError)
        # Ensure the correct log message was issued.
        mock_warn.assert_any_call("Processing XML file failed.")

# _load_schema()

def test_load_schema_invalid_xsd():
    """
    Test that _load_schema() returns a failure result when an invalid 
    XSD is provided.

    Priority: H
    """
    # Provide a valid validator to pass into the error.
    mock_validator = XsdValidator("strict")
    with patch.object(
        xml_validator_module, "XMLSchema",
        side_effect=XMLSchemaValidationError(
            mock_validator,
            obj="mock_xsd",
            reason="Invalid XSD"
        )
    ), patch.object(xml_validator_module.logger, "info"):
        validator = XmlValidator()
        result = validator._load_schema(Path("invalid_schema.xsd"))
        assert result.success is False
        assert isinstance(result.error, dict)
        assert "XMLSchemaValidationError" in result.error
        assert isinstance(
            result.error["XMLSchemaValidationError"],
            XMLSchemaValidationError
        )

def test_load_schema_valid_xsd():
    """
    Test that _load_schema() successfully loads a valid XSD schema.

    Priority: H
    """
    with patch.object(
        xml_validator_module, "XMLSchema"
    ) as mock_xmlschema, patch.object(
        xml_validator_module.logger, "info"
    ):
        # Simulated return from XMLSchema.
        mock_schema_instance = mock_xmlschema.return_value
        validator = XmlValidator()
        result = validator._load_schema(Path("valid_schema.xsd"))
        mock_xmlschema.assert_called_once_with(
            Path("valid_schema.xsd"), base_url=None
            )
        assert result.success is True
        assert result.value is mock_schema_instance

# _validate_xml()

def test_validate_xml_valid_file(setup_test_files):
    """
    Test that _validate_xml() correctly validates a well-formed XML file 
    against a matching XSD.

    Priority: H
    """
    xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
        <xs:element name="note" type="xs:string"/>
    </xs:schema>"""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <note>Hello, World!</note>"""
    xml_file, xsd_file = next(setup_test_files(xml_content, xsd_content))
    with patch.object(xml_validator_module.logger, "warn"), \
         patch.object(xml_validator_module.logger, "info"):
        validator = XmlValidator()
        is_valid, errors = validator._validate_xml(xml_file, xsd_file)
        assert is_valid is True
        assert errors is None

def test_validate_xml_invalid_file(setup_test_files):
    """
    Test that _validate_xml() returns (False, [errors]) when given an 
    XML file that does not conform to the schema.

    Priority: H
    """
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
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <note></note>"""
    xml_file, xsd_file = next(setup_test_files(xml_content, xsd_content))
    with patch.object(xml_validator_module.logger, "warn"), \
         patch.object(xml_validator_module.logger, "info"):
        validator = XmlValidator()
        is_valid, errors = validator._validate_xml(xml_file, xsd_file)
        assert is_valid is False
        assert errors is not None and len(errors) > 0
        errors_str = " ".join(str(e) for e in errors)
        assert "message" in errors_str

def test_validate_xml_no_schema_provided(setup_test_files):
    """
    Test that _validate_xml() raises an error when no XSD file is 
    provided.

    Priority: M
    """
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <note>Hello, World!</note>"""
    xsd_content = None  # No schema provided.
    xml_file, _ = next(setup_test_files(xml_content, xsd_content))
    with patch.object(xml_validator_module.logger, "warn"), \
         patch.object(xml_validator_module.logger, "info"):
        validator = XmlValidator()
        expected_error_message = "No schema: provide an XSD path during keyword call(s)."
        with pytest.raises(ValueError, match=re.escape(expected_error_message)):
            validator._validate_xml(xml_file, None)

def test_validate_xml_malformed_xml(setup_test_files):
    """
    Test that _validate_xml() returns (False, [errors]) when given a
    malformed XML file (e.g., missing a closing tag).

    Priority: M
    """
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
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <note>
        <message>Hello, World!</message>""" # Missing </note>.
    xml_file, xsd_file = next(setup_test_files(xml_content, xsd_content))
    with patch.object(xml_validator_module.logger, "warn"), \
         patch.object(xml_validator_module.logger, "info"):
        validator = XmlValidator()
        is_valid, errors = validator._validate_xml(xml_file, xsd_file)
        assert is_valid is False
        assert errors is not None and len(errors) > 0
        errors_str = " ".join(str(e) for e in errors)
        assert "Premature end of data" in errors_str

# validate_xml_files()
