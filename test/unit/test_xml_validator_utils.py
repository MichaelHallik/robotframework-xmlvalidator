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
Contains the unit tests for the ValidatorUtils class in the 
src/xmlvalidator/xml_validator_utils.py module.

Four utility methods do not have unit tests:

- _resolve_path()
- get_file_paths()
- log_file_errors()
- write_errors_to_csv()

These will, however, be tested in the integration tests.

See for an overview of all tests the file test/overview_of_tests.html.
"""


# pylint: disable=C0302:too-many-lines
# pylint: disable=I1101:c-extension-no-member # On account of lxml.


# Standard library imports.
from pathlib import Path
from xml.etree.ElementTree import ParseError
# Third-party library imports.
from lxml import etree
import pytest
from xmlschema import XMLSchema
# Local application imports.
from src.xmlvalidator.xml_validator_utils import ValidatorUtils


TEST_DIR = Path("test/_data/unit")


# _resolve_path()

# extract_xml_namespaces()

def test_extract_xml_namespaces_single_namespace(setup_test_files):
    """
    Test that extract_xml_namespaces() correctly extracts a single 
    namespace.

    Priority: M
    """
    # Define XML content with a single namespace.
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns:ns1="http://example.com/ns1">
    </root>"""
    # Dynamically create the XML file (no XSD needed).
    xml_file, _ = next(setup_test_files(xml_content, None))
    # Parse the XML file before passing it to the function.
    parsed_tree = etree.parse(str(xml_file), parser=etree.XMLParser())
    xml_root = parsed_tree.getroot()
    # Call the method under test.
    extracted_namespaces_set = ValidatorUtils.extract_xml_namespaces(
        xml_root
        )
    extracted_namespaces_dict = ValidatorUtils.extract_xml_namespaces(
        xml_root, return_dict=True
        )
    # Expected outcomes.
    expected_set = {"http://example.com/ns1"}
    expected_dict = {"ns1": "http://example.com/ns1"}
    # Assertions to check correct extraction.
    assert extracted_namespaces_set == expected_set, (
        f"Expected: set {expected_set}; got {extracted_namespaces_set}."
        )
    assert extracted_namespaces_dict == expected_dict, (
        f"Expected: dict {expected_dict}; got {extracted_namespaces_dict}."
        )

def test_extract_xml_namespaces_multiple_namespaces(setup_test_files):
    """
    Test that extract_xml_namespaces() correctly extracts multiple 
    namespaces.

    Priority: M
    """
    # Define XML content with multiple namespaces.
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns:ns1="http://example.com/ns1" xmlns:ns2="http://example.com/ns2">
    </root>"""
    # Dynamically create the XML file (no XSD needed).
    xml_file, _ = next(setup_test_files(xml_content, None))
    # Parse the XML file before passing it to the function.
    parsed_tree = etree.parse(str(xml_file), parser=etree.XMLParser())
    xml_root = parsed_tree.getroot()
    # Call the method under test.
    extracted_namespaces_set = ValidatorUtils.extract_xml_namespaces(
        xml_root
        )
    extracted_namespaces_dict = ValidatorUtils.extract_xml_namespaces(
        xml_root, return_dict=True
        )
    # Expected outcomes.
    expected_set = {"http://example.com/ns1", "http://example.com/ns2"}
    expected_dict = {
        "ns1": "http://example.com/ns1",
        "ns2": "http://example.com/ns2"
        }
    # Assertions to check correct extraction.
    assert extracted_namespaces_set == expected_set, (
        f"Expected set {expected_set}; got {extracted_namespaces_set}."
        )
    assert extracted_namespaces_dict == expected_dict, (
        f"Expected dict {expected_dict}; got {extracted_namespaces_dict}."
        )

def test_extract_xml_namespaces_default_namespace(setup_test_files):
    """
    Test that extract_xml_namespaces() correctly extracts a default 
    namespace.

    Priority: M
    """
    # Define XML content with a default (no-prefix) namespace.
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns="http://example.com/default">
    </root>"""
    # Dynamically create the XML file (no XSD needed).
    xml_file, _ = next(setup_test_files(xml_content, None))
    # Parse the XML file before passing it to the function.
    parsed_tree = etree.parse(str(xml_file), parser=etree.XMLParser())
    xml_root = parsed_tree.getroot()
    # Call the method under test.
    extracted_namespaces_set = ValidatorUtils.extract_xml_namespaces(
        xml_root
        )
    extracted_namespaces_dict = ValidatorUtils.extract_xml_namespaces(
        xml_root, return_dict=True
        )
    # Expected outcomes.
    expected_set = {"http://example.com/default"}
    # Def ns has a None key in nsmap.
    expected_dict = {None: "http://example.com/default"}
    # Assertions to check correct extraction.
    assert extracted_namespaces_set == expected_set, (
        f"Expected set {expected_set}, but got {extracted_namespaces_set}."
        )
    assert extracted_namespaces_dict == expected_dict, (
        f"Expected dict {expected_dict}, but got {extracted_namespaces_dict}."
        )

def test_extract_xml_namespaces_mixed_default_and_prefixed(setup_test_files):
    """
    Test that extract_xml_namespaces() correctly extracts both a default 
    namespace and a prefixed namespace.

    Priority: M
    """
    # Define XML content with a default and a prefixed namespace.
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns="http://example.com/default" xmlns:ns1="http://example.com/ns1">
    </root>"""
    # Dynamically create the XML file (no XSD needed).
    xml_file, _ = next(setup_test_files(xml_content, None))
    # Parse the XML file before passing it to the function.
    parsed_tree = etree.parse(str(xml_file), parser=etree.XMLParser())
    xml_root = parsed_tree.getroot()
    # Call the method under test.
    extracted_namespaces_set = ValidatorUtils.extract_xml_namespaces(
        xml_root
        )
    extracted_namespaces_dict = ValidatorUtils.extract_xml_namespaces(
        xml_root, return_dict=True
        )
    # Expected outcomes.
    expected_set = {"http://example.com/default", "http://example.com/ns1"}
    expected_dict = {
        None: "http://example.com/default", "ns1": "http://example.com/ns1"
        }
    # Assertions to check correct extraction.
    assert extracted_namespaces_set == expected_set, (
        f"Expected set {expected_set}, but got {extracted_namespaces_set}."
        )
    assert extracted_namespaces_dict == expected_dict, (
        f"Expected dict {expected_dict}, but got {extracted_namespaces_dict}."
        )

def test_extract_xml_namespaces_no_namespace(setup_test_files):
    """
    Test that extract_xml_namespaces() correctly returns an empty set 
    or dictionary when no namespaces are declared.

    Priority: L
    """
    # Define XML content with no namespaces.
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root>
    </root>"""
    # Dynamically create the XML file (no XSD needed).
    xml_file, _ = next(setup_test_files(xml_content, None))
    # Parse the XML file before passing it to the function.
    parsed_tree = etree.parse(str(xml_file), parser=etree.XMLParser())
    xml_root = parsed_tree.getroot()
    # Call the method under test.
    extracted_namespaces_set = ValidatorUtils.extract_xml_namespaces(
        xml_root
        )
    extracted_namespaces_dict = ValidatorUtils.extract_xml_namespaces(
        xml_root, return_dict=True
        )
    # Expected outcomes.
    expected_set = set()  # Empty set
    expected_dict = {}  # Empty dictionary
    # Assertions to check correct extraction.
    assert extracted_namespaces_set == expected_set, (
        f"Expected empty set, but got {extracted_namespaces_set}."
        )
    assert extracted_namespaces_dict == expected_dict, (
        f"Expected empty dict, but got {extracted_namespaces_dict}."
        )

def test_extract_xml_namespaces_nested_namespaces(setup_test_files):
    """
    Test that extract_xml_namespaces() correctly extracts namespaces 
    declared at different nesting levels.

    Priority: L
    """
    # Define XML content with namespaces at both root and nested elements.
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns:ns1="http://example.com/ns1">
        <child xmlns:ns2="http://example.com/ns2"/>
    </root>"""
    # Dynamically create the XML file (no XSD needed).
    xml_file, _ = next(setup_test_files(xml_content, None))
    # Parse the XML file before passing it to the function.
    parsed_tree = etree.parse(str(xml_file), parser=etree.XMLParser())
    xml_root = parsed_tree.getroot()
    # Call the method under test with `include_nested=True`.
    extracted_namespaces_set = ValidatorUtils.extract_xml_namespaces(
        xml_root, include_nested=True
        )
    extracted_namespaces_dict = ValidatorUtils.extract_xml_namespaces(
        xml_root, return_dict=True, include_nested=True
        )
    # Expected outcomes.
    expected_set = {"http://example.com/ns1", "http://example.com/ns2"}
    expected_dict = {
        "ns1": "http://example.com/ns1",
        "ns2": "http://example.com/ns2"
        }

    # Assertions to check correct extraction.
    assert extracted_namespaces_set == expected_set, (
        f"Expected set {expected_set}, but got {extracted_namespaces_set}."
        )
    assert extracted_namespaces_dict == expected_dict, (
        f"Expected dict {expected_dict}, but got {extracted_namespaces_dict}."
        )

def test_extract_xml_namespaces_invalid_xml(setup_test_files):
    """
    Test that extract_xml_namespaces() raises an XMLSyntaxError when 
    given an invalid XML file.

    Priority: H
    """
    # Define **malformed** XML (missing closing tag for <root>).
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns:ns1="http://example.com/ns1">
        <child> <!-- Missing closing tag -->
    """
    # Dynamically create the XML file (no XSD needed).
    xml_file, _ = next(setup_test_files(xml_content, None))
    # Expect parsing the XML file to raise an `XMLSyntaxError`.
    with pytest.raises(etree.XMLSyntaxError, match="Premature end of data"):
        # This should raise an error.
        parsed_tree = etree.parse(str(xml_file), parser=etree.XMLParser())
        # Will not be reached.
        xml_root = parsed_tree.getroot()
        # Call method under test (should not execute due to error).
        _ = ValidatorUtils.extract_xml_namespaces(xml_root)

def test_extract_xml_namespaces_redundant_declarations(setup_test_files):
    """
    Test that extract_xml_namespaces() correctly extracts unique 
    namespaces even when they are declared redundantly.

    Priority: L
    """
    # Define XML content with redundant namespace declarations.
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns:ns1="http://example.com/ns1">
        <child xmlns:ns1="http://example.com/ns1"/>  <!-- Redundant declaration -->
    </root>"""
    # Dynamically create the XML file (no XSD needed).
    xml_file, _ = next( setup_test_files(xml_content, None) )
    # Parse the XML file before passing it to the function.
    parsed_tree = etree.parse(str(xml_file), parser=etree.XMLParser())
    xml_root = parsed_tree.getroot()
    # Call the method under test with `include_nested=True`.
    extracted_namespaces_set = ValidatorUtils.extract_xml_namespaces(
        xml_root, include_nested=True
        )
    extracted_namespaces_dict = ValidatorUtils.extract_xml_namespaces(
        xml_root, return_dict=True, include_nested=True
        )
    # Expected outcomes.
    expected_set = {"http://example.com/ns1"} # No duplicates.
    expected_dict = {
        "ns1": "http://example.com/ns1" # No redundant declarations.
        }
    # Assertions to check correct extraction.
    assert extracted_namespaces_set == expected_set, (
        f"Expected set {expected_set}, but got {extracted_namespaces_set}."
        )
    assert extracted_namespaces_dict == expected_dict, (
        f"Expected dict {expected_dict}, but got {extracted_namespaces_dict}."
        )

# get_file_paths()

# log_file_errors()

# match_namespace_to_schema()

def test_match_namespace_to_schema_valid_target_namespace(setup_test_files):
    """
    Test that match_namespace_to_schema() correctly identifies a valid 
    namespace match between an XML file and an XSD schema.

    Priority: H
    """
    # Define a valid XML file with a matching namespace.
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns="http://example.com/schema">
        <child>Valid content</child>
    </root>"""
    # Define an XSD schema with the same target namespace.
    xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
               targetNamespace="http://example.com/schema"
               xmlns="http://example.com/schema">
        <xs:element name="root">
            <xs:complexType>
                <xs:sequence>
                    <xs:element name="child" type="xs:string"/>
                </xs:sequence>
            </xs:complexType>
        </xs:element>
    </xs:schema>"""
    # Dynamically create test files (valid XML + XSD).
    xml_file, xsd_file = next(setup_test_files(xml_content, xsd_content))
    # Load the schema using XMLSchema.
    xsd_schema = XMLSchema(str(xsd_file))
    # Extract namespaces from XML.
    parsed_tree = etree.parse(str(xml_file), parser=etree.XMLParser())
    xml_root = parsed_tree.getroot()
    extracted_namespaces = ValidatorUtils.extract_xml_namespaces(xml_root)
    # Call the method under test.
    result = ValidatorUtils.match_namespace_to_schema(
        xsd_schema=xsd_schema,
        xml_namespaces=extracted_namespaces # type: ignore
        )
    # Assertion: the schema should match.
    assert result is True, (
        "Expected match, but schema was not recognized as valid."
        )

def test_match_namespace_to_schema_invalid_target_namespace(setup_test_files):
    """
    Test that match_namespace_to_schema() returns False when the XSD's
    target namespace does not match any declared XML namespace.

    Priority: H
    """
    # Define XML content with a non-matching namespace.
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns="http://wrong.com/schema">
        <child>Content</child>
    </root>"""

    # Define XSD content with a different target namespace.
    xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
               targetNamespace="http://example.com/schema"
               xmlns="http://example.com/schema">
        <xs:element name="root">
            <xs:complexType>
                <xs:sequence>
                    <xs:element name="child" type="xs:string"/>
                </xs:sequence>
            </xs:complexType>
        </xs:element>
    </xs:schema>"""

    # Dynamically create test files (valid XML + XSD).
    xml_file, xsd_file = next(setup_test_files(xml_content, xsd_content))

    # Parse the XML and XSD.
    parsed_tree = etree.parse(str(xml_file), parser=etree.XMLParser())
    xml_root = parsed_tree.getroot()
    schema_tree = etree.parse(str(xsd_file), parser=etree.XMLParser())
    xsd_schema = XMLSchema(schema_tree)  # Create schema object

    # Extract namespaces from XML.
    extracted_namespaces = ValidatorUtils.extract_xml_namespaces(
        xml_root, return_dict=False
        )
    # Call the method under test.
    result = ValidatorUtils.match_namespace_to_schema(
        xsd_schema=xsd_schema,
        xml_namespaces=extracted_namespaces # type: ignore
        )
    # Expected outcome: False because namespaces do not match.
    assert result is False, (f"Expected False, but got {result}.")

def test_match_namespace_to_schema_match_with_imported_namespace(
        setup_test_files
        ):
    """
    Test that match_namespace_to_schema() correctly identifies a match
    when the XML file's namespace aligns with an imported namespace
    in the XSD.

    Priority: H
    """
    # Define XML with a namespace that matches an imported ns in the XSD.
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns="http://example.com/imported">
        <child>Valid content</child>
    </root>"""
    # XSD where `targetNamespace` doesn't match, but it imports a ns that does.
    xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
               targetNamespace="http://example.com/schema"
               xmlns:imported="http://example.com/imported">
        <xs:import namespace="http://example.com/imported" />
        <xs:element name="root" />
    </xs:schema>"""
    # Dynamically create test files (valid XML + XSD).
    xml_file, xsd_file = next(setup_test_files(xml_content, xsd_content))
    # Parse the XML and XSD.
    parsed_tree = etree.parse(str(xml_file), parser=etree.XMLParser())
    xml_root = parsed_tree.getroot()
    schema_tree = etree.parse(str(xsd_file), parser=etree.XMLParser())
    xsd_schema = XMLSchema(schema_tree)  # Load schema object
    # Extract namespaces from XML.
    extracted_namespaces = ValidatorUtils.extract_xml_namespaces(xml_root)
    # Call the method under test.
    result = ValidatorUtils.match_namespace_to_schema(
        xsd_schema=xsd_schema,
        xml_namespaces=extracted_namespaces # type: ignore
        )
    # Validate the schema is correctly matched based on the imported namespace.
    assert result, (
        "Expected schema to match based on imported namespace, but it did not."
        )

def test_match_namespace_to_schema_no_matching_namespace(setup_test_files):
    """
    Test that match_namespace_to_schema() correctly returns False when 
    no namespace in the XML matches the XSD's target or imported 
    namespaces.

    Priority: H
    """
    # Define XML content with a non-matching namespace.
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns="http://wrong.com/schema">
        <child>Invalid match</child>
    </root>"""
    # Define schema with a different target namespace and an imported ns.
    xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
               targetNamespace="http://example.com/schema"
               xmlns="http://example.com/schema">
        <xs:import namespace="http://example.com/imported"/>
        <xs:element name="root">
            <xs:complexType>
                <xs:sequence>
                    <xs:element name="child" type="xs:string"/>
                </xs:sequence>
            </xs:complexType>
        </xs:element>
    </xs:schema>"""
    # Create test XML and XSD files dynamically.
    xml_file, xsd_file = next(setup_test_files(xml_content, xsd_content))
    # Parse the XML and XSD files.
    parsed_tree = etree.parse(str(xml_file), parser=etree.XMLParser())
    xml_root = parsed_tree.getroot()
    schema_tree = etree.parse(str(xsd_file), parser=etree.XMLParser())
    # Load XSD schema.
    xsd_schema = XMLSchema(schema_tree)
    # Extract namespaces from the XML.
    extracted_namespaces = ValidatorUtils.extract_xml_namespaces(xml_root)
    # Call the method under test.
    result = ValidatorUtils.match_namespace_to_schema(
        xsd_schema=xsd_schema,
        xml_namespaces=extracted_namespaces # type: ignore
        )
    # Expected outcome: no matching namespace; function returns False.
    assert result is False, (
        "Expected match_namespace_to_schema() to return False, but got True."
        )

def test_match_namespace_to_schema_no_target_namespace_but_imported_matches(
        setup_test_files
        ):
    """
    Test that match_namespace_to_schema() correctly returns True when 
    the XSD has no target namespace but an imported namespace matches 
    the XML's namespace.

    Priority: H
    """
    # Define XML with a namespace that matches an imported ns in the XSD.
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns="http://example.com/imported">
        <child>Valid match</child>
    </root>"""
    # Define an XSD with no target namespace but with an imported ns.
    xsd_main_content = """<?xml version="1.0" encoding="UTF-8"?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
        <xs:import namespace="http://example.com/imported" schemaLocation="imported.xsd"/>
        <xs:element name="root">
            <xs:complexType>
                <xs:sequence>
                    <xs:element name="child" type="xs:string"/>
                </xs:sequence>
            </xs:complexType>
        </xs:element>
    </xs:schema>"""
    # Define the imported XSD schema file (this file should define the ns).
    xsd_imported_content = """<?xml version="1.0" encoding="UTF-8"?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
               targetNamespace="http://example.com/imported"
               xmlns="http://example.com/imported">
        <xs:element name="child" type="xs:string"/>
    </xs:schema>"""
    # Create test XML and XSD files dynamically.
    xml_file, xsd_main_file = next(
        setup_test_files(xml_content, xsd_main_content)
        )
    _, _ = next(setup_test_files(None, xsd_imported_content))
    # Parse the XML and XSD files.
    parsed_tree = etree.parse(str(xml_file), parser=etree.XMLParser())
    xml_root = parsed_tree.getroot()
    # Load XSD schema (now with a real import)
    xsd_schema = XMLSchema(str(xsd_main_file))
    # Extract namespaces from the XML.
    extracted_namespaces = ValidatorUtils.extract_xml_namespaces(xml_root)
    # Call the method under test.
    result = ValidatorUtils.match_namespace_to_schema(
        xsd_schema=xsd_schema,
        xml_namespaces=extracted_namespaces # type: ignore
        )
    # Expected: should return True since the imported namespace matches.
    assert result is True, (
        "Expected match_namespace_to_schema() to return True, but got False."
        )

def test_match_namespace_to_schema_no_target_namespace_and_no_match(
        setup_test_files
        ):
    """
    Test that match_namespace_to_schema() correctly returns False when 
    the XSD has no target namespace and none of the imported namespaces 
    match the XML's declared namespaces.

    Priority: H
    """
    # Define XML with a namespace that does not match any in the XSD.
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns="http://wrong.com/schema">
        <child>No match</child>
    </root>"""
    # Define a schema with no target namespace and an imported namespace.
    xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
        <xs:import namespace="http://example.com/imported"/>
        <xs:element name="root">
            <xs:complexType>
                <xs:sequence>
                    <xs:element name="child" type="xs:string"/>
                </xs:sequence>
            </xs:complexType>
        </xs:element>
    </xs:schema>"""
    # Create test XML and XSD files dynamically.
    xml_file, xsd_file = next(setup_test_files(xml_content, xsd_content))
    # Parse the XML and XSD files.
    parsed_tree = etree.parse(str(xml_file), parser=etree.XMLParser())
    xml_root = parsed_tree.getroot()
    schema_tree = etree.parse(str(xsd_file), parser=etree.XMLParser())
    # Load XSD schema.
    xsd_schema = XMLSchema(schema_tree)
    # Extract namespaces from the XML.
    extracted_namespaces = ValidatorUtils.extract_xml_namespaces(xml_root)
    # Call the method under test.
    result = ValidatorUtils.match_namespace_to_schema(
        xsd_schema=xsd_schema,
        xml_namespaces=extracted_namespaces # type: ignore
        )
    # Expected: should return False since no namespace matches.
    assert result is False, (
        "Expected match_namespace_to_schema() to return False, but got True."
        )

def test_match_namespace_to_schema_empty_namespaces_in_xml(setup_test_files):
    """
    Test that match_namespace_to_schema() correctly returns False when 
    the XML does not declare any namespaces, but the XSD does.

    Priority: H
    """
    # Define XML content with no namespaces declared.
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <child>No namespace declared</child>
    </root>"""
    # Define an XSD schema with a target namespace.
    xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
               targetNamespace="http://example.com/schema">
        <xs:element name="root">
            <xs:complexType>
                <xs:sequence>
                    <xs:element name="child" type="xs:string"/>
                </xs:sequence>
            </xs:complexType>
        </xs:element>
    </xs:schema>"""
    # Create test XML and XSD files dynamically.
    xml_file, xsd_file = next(setup_test_files(xml_content, xsd_content))
    # Parse the XML and XSD files.
    parsed_tree = etree.parse(str(xml_file), parser=etree.XMLParser())
    xml_root = parsed_tree.getroot()
    schema_tree = etree.parse(str(xsd_file), parser=etree.XMLParser())
    # Load XSD schema.
    xsd_schema = XMLSchema(schema_tree)
    # Extract namespaces from the XML.
    extracted_namespaces = ValidatorUtils.extract_xml_namespaces(xml_root)
    # Call the method under test.
    result = ValidatorUtils.match_namespace_to_schema(
        xsd_schema=xsd_schema,
        xml_namespaces=extracted_namespaces  # type: ignore
        )
    # Expected: should return False since the XML has no namespaces.
    assert result is False, (
        "Expected match_namespace_to_schema() to return False, but got True."
        )

def test_match_namespace_to_schema_no_namespaces_anywhere(setup_test_files):
    """
    Test that match_namespace_to_schema() correctly returns False when 
    neither the XML nor the XSD define any namespaces.

    Priority: H
    """
    # Define XML content with no namespaces declared.
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <child>No namespaces anywhere</child>
    </root>"""
    # Define an XSD schema with no target namespace and no imported namespaces.
    xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
        <xs:element name="root">
            <xs:complexType>
                <xs:sequence>
                    <xs:element name="child" type="xs:string"/>
                </xs:sequence>
            </xs:complexType>
        </xs:element>
    </xs:schema>"""
    # Create test XML and XSD files dynamically.
    xml_file, xsd_file = next(setup_test_files(xml_content, xsd_content))
    # Parse the XML and XSD files.
    parsed_tree = etree.parse(str(xml_file), parser=etree.XMLParser())
    xml_root = parsed_tree.getroot()
    schema_tree = etree.parse(str(xsd_file), parser=etree.XMLParser())
    # Load XSD schema.
    xsd_schema = XMLSchema(schema_tree)
    # Extract namespaces from the XML.
    extracted_namespaces = ValidatorUtils.extract_xml_namespaces(xml_root)
    # Call the method under test.
    result = ValidatorUtils.match_namespace_to_schema(
        xsd_schema=xsd_schema,
        xml_namespaces=extracted_namespaces # type: ignore
        )
    # Expected: should return False since neither XML nor XSD have namespaces.
    assert result is False, (
        "Expected match_namespace_to_schema() to return False, but got True."
        )

def test_match_namespace_to_schema_handles_unexpected_exceptions(
        setup_test_files
        ):
    """
    Test that match_namespace_to_schema() raises an exception when an
    unexpected error occurs (e.g., malformed XSD schema).

    Priority: H
    """
    # Define XML content with a valid namespace.
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns="http://example.com/schema">
        <child>Valid content</child>
    </root>"""
    # Define a malformed XSD schema (intentionally invalid XML).
    xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
               targetNamespace="http://example.com/schema">
        <xs:element name="root">
            <xs:complexType>
                <xs:sequence>
                    <xs:element name="child" type="xs:string"/>
                <!-- Missing closing tags for xs:complexType and xs:element -->
    </xs:schema>"""
    # Create test XML and XSD files dynamically.
    xml_file, xsd_file = next(setup_test_files(xml_content, xsd_content))
    # Parse the XML file.
    parsed_tree = etree.parse(str(xml_file), parser=etree.XMLParser())
    xml_root = parsed_tree.getroot()
    # Extract namespaces from the XML.
    extracted_namespaces = ValidatorUtils.extract_xml_namespaces(xml_root)
    # Expect an exception when trying to load a **malformed XSD schema**.
    with pytest.raises(ParseError, match="mismatched tag"):
        xsd_schema = XMLSchema(str(xsd_file))  # This should raise an error.
        # Call the method under test (should never be reached due to error).
        _ = ValidatorUtils.match_namespace_to_schema(
            xsd_schema=xsd_schema,
            xml_namespaces=extracted_namespaces # type: ignore
            )

# sanity_check_files()

def test_sanity_check_files_valid_xml_xsd(setup_test_files):
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
    result = ValidatorUtils.sanity_check_files(
        [xml_file, xsd_file], parse_files=True
        )
    # Expect a successful validation.
    assert result.success is True
    # Ensure there are no errors.
    assert result.error is None or len(result.error) == 0

def test_sanity_check_files_invalid_xml(setup_test_files):
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
    result = ValidatorUtils.sanity_check_files( [xml_file], parse_files=True )
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

def test_sanity_check_files_invalid_xsd(setup_test_files):
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
    result = ValidatorUtils.sanity_check_files(
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

def test_sanity_check_files_missing_file():
    """
    Test that sanity_check_files() correctly detects and reports a 
    missing file.

    Priority: H
    """
    # Define a non-existent file path.
    missing_file = Path("test/files/missing.xml")
    # Call the function under test.
    result = ValidatorUtils.sanity_check_files([missing_file])
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

def test_sanity_check_files_empty_file(setup_test_files):
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
    result = ValidatorUtils.sanity_check_files([xml_file, xsd_file])
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

def test_sanity_check_files_unsupported_file_type():
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
    result = ValidatorUtils.sanity_check_files([unsupported_file])
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

# write_errors_to_csv()
