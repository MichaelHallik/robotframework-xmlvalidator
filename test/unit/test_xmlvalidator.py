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
Contains unit tests for the src/xmlvalidator/XmlValidator.py module.

See for an overview of all tests the file test/_doc/unit/overview.html.
"""

# Standard library imports.
import importlib
from pathlib import Path
from unittest.mock import patch

# Third-party library imports.
import pytest

# Local application imports.
from xmlvalidator import XmlValidator
from xmlvalidator.results import ValidatorResult, ValidatorResultRecorder
from xmlvalidator.schema.manager import ValidatorSchemaManager
from xmlvalidator.schema.resolver import ValidatorSchemaResolver
from xmlvalidator.validation import XmlValidationRunner

xml_validator_module = importlib.import_module("xmlvalidator.XmlValidator")
schema_manager_module = importlib.import_module("xmlvalidator.schema.manager")


# __init__()


def test_init_loads_single_xsd_schema():
    """
    Test that the XmlValidator initializes correctly when provided with
    a valid XSD schema.

    This test mocks the file path resolution, the XMLSchema loader,
    and the logger to ensure correct schema loading behavior and logging.

    Priority: H
    """
    with patch.object(
        schema_manager_module,
        "get_file_paths",
        return_value=([Path("schema.xsd")], True)
    ), patch.object(
        schema_manager_module, "XMLSchema"
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

def test_init_allows_import_without_initial_schema():
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

def test_init_rejects_multiple_initial_xsd_files():
    """
    Test that the XmlValidator raises a ValueError when multiple XSD
    files are found in a directory during initialization.

    The helper method get_file_paths() returns a list of multiple .xsd
    files, simulating an invalid schema preloading scenario.

    Priority: H
    """
    with patch.object(
        schema_manager_module, "get_file_paths",
        return_value=([Path("schema1.xsd"), Path("schema2.xsd")], False)
    ), pytest.raises(ValueError, match="Got multiple xsd files"):
        XmlValidator(xsd_path="schemas_folder/")

def test_init_propagates_invalid_initial_xsd_path():
    """
    Test that the XmlValidator raises a ValueError when an invalid
    XSD path is provided during initialization.

    Simulates an invalid input by making get_file_paths() raise a
    ValueError directly.

    Priority: H
    """
    with patch.object(
        schema_manager_module, "get_file_paths",
        side_effect=ValueError("Invalid XSD path")
    ), pytest.raises(ValueError, match="Invalid XSD path"):
        XmlValidator(xsd_path="invalid_path/")

def test_init_creates_collaborator_objects_and_default_state():
    """
    Test that XmlValidator initializes its attributes correctly.

    Priority: H
    """
    with patch.object(xml_validator_module.logger, "info"), \
         patch.object(xml_validator_module.logger, "console"):
        validator = XmlValidator()
        assert isinstance(validator.validator_results, ValidatorResultRecorder)
        assert isinstance(validator.schema_manager, ValidatorSchemaManager)
        assert isinstance(validator.schema_resolver, ValidatorSchemaResolver)
        assert isinstance(validator.validation_runner, XmlValidationRunner)
        assert validator.schema is None
        assert validator.error_facets == ['path', 'reason']

def test_init_logs_custom_error_facets():
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

def test_init_raises_system_error_when_initial_schema_loading_fails():
    """
    Test that the XmlValidator raises a SystemError when schema
    loading fails due to an invalid or unreadable XSD file.

    This test mocks get_file_paths to return a valid XSD path,
    but load_schema to simulate a failure result.

    Priority: H
    """
    with patch.object(
        schema_manager_module, "get_file_paths",
        return_value=([Path("invalid_schema.xsd")], True)
    ), patch.object(
        ValidatorSchemaManager, "load_schema",
        return_value=ValidatorResult(False, "Schema load error")
    ), pytest.raises(SystemError, match="Loading of schema failed"):
        XmlValidator(xsd_path="invalid_schema.xsd")

def test_init_propagates_initial_schema_file_access_error():
    """
    Test that the XmlValidator raises an OSError when the XSD file
    cannot be accessed due to file system restrictions (e.g., permissions).

    This test mocks load_schema to raise an OSError directly.

    Priority: M
    """
    with patch.object(
        schema_manager_module, "get_file_paths",
        return_value=([Path("restricted_schema.xsd")], True)
    ), patch.object(
        ValidatorSchemaManager, "load_schema",
        side_effect=OSError("Permission denied")
    ), pytest.raises(OSError, match="Permission denied"):
        XmlValidator(xsd_path="restricted_schema.xsd")
