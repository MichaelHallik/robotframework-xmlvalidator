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
Contains unit tests for the src/xmlvalidator/schema/manager.py module.

See for an overview of all tests the file test/_doc/unit/overview.html.
"""

# Standard library imports.
from pathlib import Path
from unittest.mock import MagicMock, patch

# Third-party library imports.
import pytest
from xmlschema import XMLSchemaValidationError
from xmlschema.validators import XsdValidator

# Local application imports.
from xmlvalidator.results import ValidatorResult
from xmlvalidator.schema.manager import ValidatorSchemaManager

schema_manager_module = __import__(
    "xmlvalidator.schema.manager",
    fromlist=[""]
)
xml_validator_module = schema_manager_module


# ensure_schema()


def test_ensure_schema_keep_existing():
    """
    Test that ensure_schema() retains an already loaded schema when
    no new schema path is provided, ensuring the correct log message
    is issued.

    Priority: H
    """
    with patch.object(ValidatorSchemaManager, "load_schema") as mock_load_schema, \
         patch.object(xml_validator_module.logger, "info"):
        # Create a schema manager and simulate a pre-loaded schema.
        schema_manager = ValidatorSchemaManager()
        mock_schema = MagicMock()
        schema_manager.schema = mock_schema
        result = schema_manager.ensure_schema()
        # Ensure no reloading occurred.
        mock_load_schema.assert_not_called()
        assert result.success is True
        assert result.value is mock_schema

def test_ensure_schema_load_new_schema():
    """
    Test that ensure_schema() correctly loads a new schema when a
    valid XSD path is provided, ensuring the correct log message is
    issued.

    Priority: H
    """
    with patch.object(
        ValidatorSchemaManager, "load_schema",
        return_value=ValidatorResult(success=True, value="new_schema")
    ) as mock_load_schema, patch.object(
        xml_validator_module.logger, "info"
    ) as mock_info:
        schema_manager = ValidatorSchemaManager()
        result = schema_manager.ensure_schema(xsd_path=Path("schema.xsd"))
        mock_load_schema.assert_called_once_with(Path("schema.xsd"), None)
        assert result.success is True
        assert result.value == "new_schema"
        mock_info.assert_any_call(
            "Setting schema file: schema.xsd.", also_console=True
            )

def test_ensure_schema_no_existing_or_new_schema():
    """
    Test that ensure_schema() raises a ValueError when neither an
    existing schema nor a new schema path is available.

    Priority: M
    """
    with patch.object(xml_validator_module.logger, "info"):
        schema_manager = ValidatorSchemaManager()
        with pytest.raises(ValueError, match="No schema: provide an XSD path"):
            schema_manager.ensure_schema()

def test_ensure_schema_replace_existing_schema():
    """
    Test that ensure_schema() replaces an existing schema when a new
    valid XSD path is provided, ensuring the correct log message is
    issued.

    Priority: H
    """
    with patch.object(
        ValidatorSchemaManager,
        "load_schema",
        return_value=ValidatorResult(success=True, value="new_schema")
    ) as mock_load_schema, patch.object(
        xml_validator_module.logger, "info"
    ) as mock_info:
        schema_manager = ValidatorSchemaManager()
        schema_manager.schema = MagicMock()
        result = schema_manager.ensure_schema(xsd_path=Path("new_schema.xsd"))
        mock_load_schema.assert_called_once_with(Path("new_schema.xsd"), None)
        assert result.success is True
        assert result.value == "new_schema"
        mock_info.assert_any_call(
            "\tUsing schema: new_schema.xsd.", also_console=True
            )

def test_ensure_schema_load_failure():
    """
    Test that ensure_schema() returns a failure result when schema
    loading fails, ensuring the correct log message is issued.

    Priority: M
    """
    with patch.object(
        ValidatorSchemaManager, "load_schema",
        return_value=ValidatorResult(success=False, error="Schema load error")
    ) as mock_load_schema, patch.object(
        xml_validator_module.logger, "info"
    ) as mock_info:
        schema_manager = ValidatorSchemaManager()
        result = schema_manager.ensure_schema(xsd_path=Path("invalid.xsd"))
        mock_load_schema.assert_called_once_with(Path("invalid.xsd"), None)
        assert result.success is False
        assert result.error == "Schema load error"
        mock_info.assert_any_call(
            "Setting schema file: invalid.xsd.", also_console=True
            )


# load_schema()


def test_load_schema_invalid_xsd():
    """
    Test that load_schema() returns a failure result when an invalid
    XSD is provided.

    Priority: H
    """
    # Provide a valid validator to pass into the error.
    mock_validator = XsdValidator("strict")
    with patch.object(
        schema_manager_module, "XMLSchema",
        side_effect=XMLSchemaValidationError(
            mock_validator,
            obj="mock_xsd",
            reason="Invalid XSD"
        )
    ), patch.object(xml_validator_module.logger, "info"):
        schema_manager = ValidatorSchemaManager()
        result = schema_manager.load_schema(Path("invalid_schema.xsd"))
        assert result.success is False
        assert isinstance(result.error, dict)
        assert "XMLSchemaValidationError" in result.error
        assert isinstance(
            result.error["XMLSchemaValidationError"],
            XMLSchemaValidationError
        )

def test_load_schema_valid_xsd():
    """
    Test that load_schema() successfully loads a valid XSD schema.

    Priority: H
    """
    with patch.object(
        schema_manager_module, "XMLSchema"
    ) as mock_xmlschema, patch.object(
        xml_validator_module.logger, "info"
    ):
        # Simulated return from XMLSchema.
        mock_schema_instance = mock_xmlschema.return_value
        schema_manager = ValidatorSchemaManager()
        result = schema_manager.load_schema(Path("valid_schema.xsd"))
        mock_xmlschema.assert_called_once_with(
            Path("valid_schema.xsd"), base_url=None
            )
        assert result.success is True
        assert result.value is mock_schema_instance
