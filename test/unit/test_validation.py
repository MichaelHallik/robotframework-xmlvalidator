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
Contains unit tests for the src/xmlvalidator/validation.py module.

See for an overview of all tests the file test/_doc/unit/overview.html.
"""

# Standard library imports.
import re
from unittest.mock import patch

# Third-party library imports.
import pytest

# Local application imports.
from xmlvalidator.schema.manager import ValidatorSchemaManager
from xmlvalidator.validation import XmlValidationRunner

validation_module = __import__(
    "xmlvalidator.validation",
    fromlist=[""]
)

DEFAULT_ERROR_FACETS = ["path", "reason"]


# validate_xml()


def test_validate_xml_valid_file(setup_test_files):
    """
    Test that validate_xml() correctly validates a well-formed XML file
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
    with patch.object(validation_module.logger, "warn"), \
         patch.object(validation_module.logger, "info"):
        validation_runner = XmlValidationRunner(ValidatorSchemaManager())
        is_valid, errors = validation_runner.validate_xml(
            xml_file,
            xsd_file,
            default_error_facets=DEFAULT_ERROR_FACETS
        )
        assert is_valid is True
        assert errors is None

def test_validate_xml_invalid_file(setup_test_files):
    """
    Test that validate_xml() returns (False, [errors]) when given an
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
    with patch.object(validation_module.logger, "warn"), \
         patch.object(validation_module.logger, "info"):
        validation_runner = XmlValidationRunner(ValidatorSchemaManager())
        is_valid, errors = validation_runner.validate_xml(
            xml_file,
            xsd_file,
            default_error_facets=DEFAULT_ERROR_FACETS
        )
        assert is_valid is False
        assert errors is not None and len(errors) > 0
        errors_str = " ".join(str(e) for e in errors)
        assert "message" in errors_str

def test_validate_xml_keeps_none_error_facets_by_default(setup_test_files):
    """
    Test that validate_xml() keeps requested error facets whose value
    is None by default and reports them as unavailable.

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
    with patch.object(validation_module.logger, "warn"), \
         patch.object(validation_module.logger, "info"):
        validation_runner = XmlValidationRunner(ValidatorSchemaManager())
        is_valid, errors = validation_runner.validate_xml(
            xml_file,
            xsd_file,
            error_facets=["path", "reason", "non_existing_facet"]
        )
        assert is_valid is False
        assert errors is not None and len(errors) > 0
        assert "non_existing_facet" in errors[0]
        assert errors[0]["non_existing_facet"] == "Unavailable"

def test_validate_xml_can_skip_none_error_facets(setup_test_files):
    """
    Test that validate_xml() can omit requested error facets whose value
    is None when explicitly requested.

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
    with patch.object(validation_module.logger, "warn"), \
         patch.object(validation_module.logger, "info"):
        validation_runner = XmlValidationRunner(ValidatorSchemaManager())
        is_valid, errors = validation_runner.validate_xml(
            xml_file,
            xsd_file,
            error_facets=["path", "reason", "non_existing_facet"],
            skip_none_error_facets=True
        )
        assert is_valid is False
        assert errors is not None and len(errors) > 0
        assert "non_existing_facet" not in errors[0]

def test_validate_xml_no_schema_provided(setup_test_files):
    """
    Test that validate_xml() raises an error when no XSD file is
    provided.

    Priority: M
    """
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <note>Hello, World!</note>"""
    xsd_content = None  # No schema provided.
    xml_file, _ = next(setup_test_files(xml_content, xsd_content))
    with patch.object(validation_module.logger, "warn"), \
         patch.object(validation_module.logger, "info"):
        validation_runner = XmlValidationRunner(ValidatorSchemaManager())
        expected_error_message = "No schema: provide an XSD path during keyword call(s)."
        with pytest.raises(ValueError, match=re.escape(expected_error_message)):
            validation_runner.validate_xml(
                xml_file,
                None,
                default_error_facets=DEFAULT_ERROR_FACETS
            )

def test_validate_xml_malformed_xml(setup_test_files):
    """
    Test that validate_xml() returns (False, [errors]) when given a
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
    with patch.object(validation_module.logger, "warn"), \
         patch.object(validation_module.logger, "info"):
        validation_runner = XmlValidationRunner(ValidatorSchemaManager())
        is_valid, errors = validation_runner.validate_xml(
            xml_file,
            xsd_file,
            default_error_facets=DEFAULT_ERROR_FACETS
        )
        assert is_valid is False
        assert errors is not None and len(errors) > 0
        errors_str = " ".join(str(e) for e in errors)
        assert "Premature end of data" in errors_str
