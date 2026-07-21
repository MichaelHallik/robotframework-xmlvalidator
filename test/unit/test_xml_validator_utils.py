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

See for an overview of all tests the file test/overview_of_tests.html.
"""

# pylint: disable=C0302:too-many-lines
# pylint: disable=I1101:c-extension-no-member
# pylint: disable=W0212:protected-access

# Standard library imports.
from pathlib import Path
from xml.etree.ElementTree import ParseError

import pytest

# Third-party library imports.
from lxml import etree
from xmlschema import XMLSchema

# Local application imports.
from xmlvalidator import xml_validator_utils as validator_utils_module
from xmlvalidator.xml_validator_utils import ValidatorUtils

TEST_DIR = Path("test/_data/unit")


class SchemaNamespaceStub:  # pylint: disable=R0903:too-few-public-methods
    """
    Minimal schema-like object for namespace matching edge-case tests.
    """

    def __init__(
        self,
        target_namespace: str | None = None,
        imports: dict[str, None] | None = None,
        namespaces: dict[str, str] | None = None
    ) -> None:
        self.target_namespace = target_namespace
        self.imports = imports or {}
        self.namespaces = namespaces or {}


# extract_namespaces()

def test_extract_namespaces_single_namespace(setup_test_files):
    """
    Test that extract_namespaces() correctly extracts a single
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
    extracted_namespaces_set = ValidatorUtils.extract_namespaces(
        xml_root
        )
    extracted_namespaces_dict = ValidatorUtils.extract_namespaces(
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

def test_extract_namespaces_multiple_namespaces(setup_test_files):
    """
    Test that extract_namespaces() correctly extracts multiple
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
    extracted_namespaces_set = ValidatorUtils.extract_namespaces(
        xml_root
        )
    extracted_namespaces_dict = ValidatorUtils.extract_namespaces(
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

def test_extract_namespaces_default_namespace(setup_test_files):
    """
    Test that extract_namespaces() correctly extracts a default
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
    extracted_namespaces_set = ValidatorUtils.extract_namespaces(
        xml_root
        )
    extracted_namespaces_dict = ValidatorUtils.extract_namespaces(
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

def test_extract_namespaces_mixed_default_and_prefixed(setup_test_files):
    """
    Test that extract_namespaces() correctly extracts both a default
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
    extracted_namespaces_set = ValidatorUtils.extract_namespaces(
        xml_root
        )
    extracted_namespaces_dict = ValidatorUtils.extract_namespaces(
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

def test_extract_namespaces_no_namespace(setup_test_files):
    """
    Test that extract_namespaces() correctly returns an empty set
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
    extracted_namespaces_set = ValidatorUtils.extract_namespaces(
        xml_root
        )
    extracted_namespaces_dict = ValidatorUtils.extract_namespaces(
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

def test_extract_namespaces_nested_namespaces(setup_test_files):
    """
    Test that extract_namespaces() correctly extracts namespaces
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
    extracted_namespaces_set = ValidatorUtils.extract_namespaces(
        xml_root, include_nested=True
        )
    extracted_namespaces_dict = ValidatorUtils.extract_namespaces(
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

def test_extract_namespaces_excludes_nested_namespaces_by_default(
    setup_test_files
    ):
    """
    Test that extract_namespaces() only extracts root namespaces
    by default.

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
    # Call the method under test without `include_nested=True`.
    extracted_namespaces_set = ValidatorUtils.extract_namespaces(
        xml_root
        )
    extracted_namespaces_dict = ValidatorUtils.extract_namespaces(
        xml_root, return_dict=True
        )
    # Expected outcomes: only the root namespace should be extracted.
    expected_set = {"http://example.com/ns1"}
    expected_dict = {
        "ns1": "http://example.com/ns1"
        }

    # Assertions to check that nested namespaces are excluded by default.
    assert extracted_namespaces_set == expected_set, (
        f"Expected set {expected_set}, but got {extracted_namespaces_set}."
        )
    assert extracted_namespaces_dict == expected_dict, (
        f"Expected dict {expected_dict}, but got {extracted_namespaces_dict}."
        )

def test_extract_namespaces_nested_default_namespaces(setup_test_files):
    """
    Test that extract_namespaces() correctly handles default
    namespaces declared at different nesting levels.

    Priority: L
    """
    # Define XML content with different default namespaces on nested elements.
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns="http://example.com/root">
        <child xmlns="http://example.com/child"/>
    </root>"""
    # Dynamically create the XML file (no XSD needed).
    xml_file, _ = next(setup_test_files(xml_content, None))
    # Parse the XML file before passing it to the function.
    parsed_tree = etree.parse(str(xml_file), parser=etree.XMLParser())
    xml_root = parsed_tree.getroot()
    # Call the method under test with `include_nested=True`.
    extracted_namespaces_set = ValidatorUtils.extract_namespaces(
        xml_root, include_nested=True
        )
    extracted_namespaces_dict = ValidatorUtils.extract_namespaces(
        xml_root, return_dict=True, include_nested=True
        )
    # Expected set outcome: the nested default namespace overwrites the root
    # default namespace because both use the same `None` key internally.
    expected_set = {
        "http://example.com/child"
        }
    # Expected dict outcome: the nested default namespace overwrites the
    # root default namespace because both use the same `None` key.
    expected_dict = {
        None: "http://example.com/child"
        }

    # Assertions to check correct default namespace extraction.
    assert extracted_namespaces_set == expected_set, (
        f"Expected set {expected_set}, but got {extracted_namespaces_set}."
        )
    assert extracted_namespaces_dict == expected_dict, (
        f"Expected dict {expected_dict}, but got {extracted_namespaces_dict}."
        )

def test_extract_namespaces_invalid_xml(setup_test_files):
    """
    Test that extract_namespaces() raises an XMLSyntaxError when
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
        _ = ValidatorUtils.extract_namespaces(xml_root)

def test_extract_namespaces_redundant_declarations(setup_test_files):
    """
    Test that extract_namespaces() correctly extracts unique
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
    extracted_namespaces_set = ValidatorUtils.extract_namespaces(
        xml_root, include_nested=True
        )
    extracted_namespaces_dict = ValidatorUtils.extract_namespaces(
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

# schema_matches_xml_namespaces()

def test_schema_matches_xml_namespaces_valid_target_namespace(setup_test_files):
    """
    Test that schema_matches_xml_namespaces() correctly identifies a valid
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
    extracted_namespaces = ValidatorUtils.extract_namespaces(xml_root)
    # Call the method under test.
    result = ValidatorUtils.schema_matches_xml_namespaces(
        xsd_schema=xsd_schema,
        xml_namespaces=extracted_namespaces # type: ignore
        )
    # Assertion: the schema should match.
    assert result is True, (
        "Expected match, but schema was not recognized as valid."
        )

def test_schema_matches_xml_namespaces_invalid_target_namespace(setup_test_files):
    """
    Test that schema_matches_xml_namespaces() returns False when the XSD's
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
    extracted_namespaces = ValidatorUtils.extract_namespaces(
        xml_root, return_dict=False
        )
    # Call the method under test.
    result = ValidatorUtils.schema_matches_xml_namespaces(
        xsd_schema=xsd_schema,
        xml_namespaces=extracted_namespaces # type: ignore
        )
    # Expected outcome: False because namespaces do not match.
    assert result is False, (f"Expected False, but got {result}.")

def test_schema_matches_xml_namespaces_match_with_imported_namespace(
        setup_test_files
        ):
    """
    Test that schema_matches_xml_namespaces() correctly identifies a match
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
    extracted_namespaces = ValidatorUtils.extract_namespaces(xml_root)
    # Call the method under test.
    result = ValidatorUtils.schema_matches_xml_namespaces(
        xsd_schema=xsd_schema,
        xml_namespaces=extracted_namespaces # type: ignore
        )
    # Validate the schema is correctly matched based on the imported namespace.
    assert result, (
        "Expected schema to match based on imported namespace, but it did not."
        )

def test_schema_matches_xml_namespaces_no_matching_namespace(setup_test_files):
    """
    Test that schema_matches_xml_namespaces() correctly returns False when
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
    extracted_namespaces = ValidatorUtils.extract_namespaces(xml_root)
    # Call the method under test.
    result = ValidatorUtils.schema_matches_xml_namespaces(
        xsd_schema=xsd_schema,
        xml_namespaces=extracted_namespaces # type: ignore
        )
    # Expected outcome: no matching namespace; function returns False.
    assert result is False, (
        "Expected schema_matches_xml_namespaces() to return False, but got True."
        )

def test_schema_matches_xml_namespaces_ignores_declared_only_namespace(
        setup_test_files
        ):
    """
    Test that schema_matches_xml_namespaces() ignores namespaces that are
    merely declared in the XSD, but not targeted or imported.

    Priority: H
    """
    # Define XML content with a namespace that is only declared in the XSD.
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns="http://example.com/declared-only">
        <child>Invalid match</child>
    </root>"""
    # Define an XSD that declares the namespace, but does not target or import it.
    xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
               targetNamespace="http://example.com/schema"
               xmlns:declared="http://example.com/declared-only">
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
    extracted_namespaces = ValidatorUtils.extract_namespaces(xml_root)
    # Call the method under test.
    result = ValidatorUtils.schema_matches_xml_namespaces(
        xsd_schema=xsd_schema,
        xml_namespaces=extracted_namespaces # type: ignore
        )
    # Expected outcome: declared-only namespaces should not be used for matching.
    assert result is False, (
        "Expected declared-only namespace to be ignored, but got a match."
        )

def test_schema_matches_xml_namespaces_allows_declared_namespace_match(
        setup_test_files
        ):
    """
    Test that schema_matches_xml_namespaces() can optionally match against
    namespaces that are declared in the XSD only.

    Priority: H
    """
    # Define XML content with a namespace that is only declared in the XSD.
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns="http://example.com/declared-only">
        <child>Valid fallback match</child>
    </root>"""
    # Define an XSD that declares the namespace, but does not target or import it.
    xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
               targetNamespace="http://example.com/schema"
               xmlns:declared="http://example.com/declared-only">
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
    extracted_namespaces = ValidatorUtils.extract_namespaces(xml_root)
    # Call the method under test with declared namespace fallback enabled.
    result = ValidatorUtils.schema_matches_xml_namespaces(
        xsd_schema=xsd_schema,
        xml_namespaces=extracted_namespaces, # type: ignore
        allow_declared_namespace_match=True
        )
    # Expected outcome: declared-only namespaces may match when explicitly enabled.
    assert result is True, (
        "Expected declared-only namespace to match when fallback is enabled."
        )

def test_schema_matches_xml_namespaces_ignores_infrastructure_namespace_in_xml():
    """
    Test that schema_matches_xml_namespaces() does not match an
    infrastructure namespace, even if the XML declares it.

    Priority: H
    """
    # Define a schema-like object using the XML Schema infrastructure namespace.
    xsd_schema = SchemaNamespaceStub(
        target_namespace="http://www.w3.org/2001/XMLSchema",
        namespaces={"xs": "http://www.w3.org/2001/XMLSchema"}
        )
    # Define XML namespaces containing only that infrastructure namespace.
    xml_namespaces = {"http://www.w3.org/2001/XMLSchema"}
    # Call the method under test.
    result = ValidatorUtils.schema_matches_xml_namespaces(
        xsd_schema=xsd_schema, # type: ignore
        xml_namespaces=xml_namespaces
        )
    # Expected outcome: infrastructure namespaces should never match.
    assert result is False, (
        "Expected infrastructure namespace to be ignored, but got a match."
        )

def test_schema_matches_xml_namespaces_ignores_declared_infrastructure_namespace():
    """
    Test that schema_matches_xml_namespaces() filters declared
    infrastructure namespaces, even when declared matching is enabled.

    Priority: H
    """
    # Define a schema-like object with only a declared infrastructure namespace.
    xsd_schema = SchemaNamespaceStub(
        namespaces={"xs": "http://www.w3.org/2001/XMLSchema"}
        )
    # Define XML namespaces containing the same infrastructure namespace.
    xml_namespaces = {"http://www.w3.org/2001/XMLSchema"}
    # Call the method under test with declared namespace fallback enabled.
    result = ValidatorUtils.schema_matches_xml_namespaces(
        xsd_schema=xsd_schema, # type: ignore
        xml_namespaces=xml_namespaces,
        allow_declared_namespace_match=True
        )
    # Expected outcome: declared infrastructure namespaces should not match.
    assert result is False, (
        "Expected declared infrastructure namespace to be ignored."
        )

def test_schema_matches_xml_namespaces_prefers_target_namespace(
        monkeypatch
        ):
    """
    Test that schema_matches_xml_namespaces() reports a target namespace
    match before considering imported or declared namespace matches.

    Priority: H
    """
    # Collect log messages produced by the method under test.
    log_messages = []
    monkeypatch.setattr(
        validator_utils_module.logger,
        "info",
        lambda message, **_: log_messages.append(message)
        )
    # Define a schema-like object with target, imported and declared namespaces.
    xsd_schema = SchemaNamespaceStub(
        target_namespace="http://example.com/target",
        imports={"http://example.com/imported": None},
        namespaces={"declared": "http://example.com/declared"}
        )
    # Define XML namespaces matching all possible schema namespace categories.
    xml_namespaces = {
        "http://example.com/target",
        "http://example.com/imported",
        "http://example.com/declared"
        }
    # Call the method under test with declared namespace fallback enabled.
    result = ValidatorUtils.schema_matches_xml_namespaces(
        xsd_schema=xsd_schema, # type: ignore
        xml_namespaces=xml_namespaces,
        allow_declared_namespace_match=True
        )
    # Extract the actual match-reason log entries.
    match_logs = [
        message for message in log_messages if message.startswith("Schema matched")
        ]
    # Expected outcome: target namespace is the highest-priority match.
    assert result is True
    assert match_logs[0] == (
        "Schema matched by target namespace: 'http://example.com/target'."
        )

def test_schema_matches_xml_namespaces_prefers_imported_over_declared_namespace(
        monkeypatch
        ):
    """
    Test that schema_matches_xml_namespaces() reports an imported
    namespace match before considering declared namespace fallback.

    Priority: H
    """
    # Collect log messages produced by the method under test.
    log_messages = []
    monkeypatch.setattr(
        validator_utils_module.logger,
        "info",
        lambda message, **_: log_messages.append(message)
        )
    # Define a schema-like object with a non-matching target namespace.
    xsd_schema = SchemaNamespaceStub(
        target_namespace="http://example.com/target",
        imports={"http://example.com/imported": None},
        namespaces={"declared": "http://example.com/declared"}
        )
    # Define XML namespaces matching imported and declared namespaces only.
    xml_namespaces = {
        "http://example.com/imported",
        "http://example.com/declared"
        }
    # Call the method under test with declared namespace fallback enabled.
    result = ValidatorUtils.schema_matches_xml_namespaces(
        xsd_schema=xsd_schema, # type: ignore
        xml_namespaces=xml_namespaces,
        allow_declared_namespace_match=True
        )
    # Extract the actual match-reason log entries.
    match_logs = [
        message for message in log_messages if message.startswith("Schema matched")
        ]
    # Expected outcome: imported namespace is preferred over declared fallback.
    assert result is True
    assert match_logs[0] == (
        "Schema matched by imported namespace: 'http://example.com/imported'."
        )

def test_schema_matches_xml_namespaces_handles_missing_or_none_imports():
    """
    Test that schema_matches_xml_namespaces() handles missing or None
    `imports` attributes defensively.

    Priority: H
    """
    # Define a schema-like object where `imports` exists but is None.
    schema_with_none_imports = SchemaNamespaceStub(
        target_namespace=None,
        namespaces={"declared": "http://example.com/declared"}
        )
    schema_with_none_imports.imports = None # type: ignore
    # Define a schema-like object where `imports` is missing entirely.
    schema_with_missing_imports = SchemaNamespaceStub(
        target_namespace=None,
        namespaces={"declared": "http://example.com/declared"}
        )
    del schema_with_missing_imports.imports
    # Define XML namespaces that do not match target or declared namespaces.
    xml_namespaces = {"http://example.com/unmatched"}
    # Call the method under test for both edge cases.
    result_with_none_imports = ValidatorUtils.schema_matches_xml_namespaces(
        xsd_schema=schema_with_none_imports, # type: ignore
        xml_namespaces=xml_namespaces
        )
    result_with_missing_imports = ValidatorUtils.schema_matches_xml_namespaces(
        xsd_schema=schema_with_missing_imports, # type: ignore
        xml_namespaces=xml_namespaces
        )
    # Expected outcome: missing/None imports should not raise errors or match.
    assert result_with_none_imports is False
    assert result_with_missing_imports is False


# _prepare_schema_namespace_matches()

def test_prepare_schema_namespace_matches_excludes_declared_by_default():
    """
    Test that _prepare_schema_namespace_matches() does not include
    declared namespaces as matching candidates by default.

    Priority: H
    """
    # Define a schema-like object with target, imported and declared namespaces.
    xsd_schema = SchemaNamespaceStub(
        target_namespace="http://example.com/target",
        imports={"http://example.com/imported": None},
        namespaces={"declared": "http://example.com/declared"}
        )
    # Call the helper with declared fallback disabled.
    target_namespace, imported_namespaces, declared_match_namespaces = (
        ValidatorUtils._prepare_schema_namespace_matches(
            xsd_schema, # type: ignore
            allow_declared_namespace_match=False
        )
    )
    # Expected outcome: target/imported namespaces are candidates.
    assert target_namespace == "http://example.com/target"
    assert imported_namespaces == {"http://example.com/imported"}
    # Expected outcome: declared namespaces are not candidates by default.
    assert declared_match_namespaces == set()


def test_prepare_schema_namespace_matches_includes_declared_when_enabled():
    """
    Test that _prepare_schema_namespace_matches() includes declared
    namespaces when declared namespace matching is enabled.

    Priority: H
    """
    # Define a schema-like object with a declared namespace.
    xsd_schema = SchemaNamespaceStub(
        namespaces={"declared": "http://example.com/declared"}
        )
    # Call the helper with declared fallback enabled.
    target_namespace, imported_namespaces, declared_match_namespaces = (
        ValidatorUtils._prepare_schema_namespace_matches(
            xsd_schema, # type: ignore
            allow_declared_namespace_match=True
        )
    )
    # Expected outcome: there is no target or imported namespace.
    assert target_namespace is None
    assert imported_namespaces == set()
    # Expected outcome: declared namespace is elevated to candidate status.
    assert declared_match_namespaces == {"http://example.com/declared"}


def test_prepare_schema_namespace_matches_filters_infrastructure_namespaces():
    """
    Test that _prepare_schema_namespace_matches() removes
    infrastructure namespaces from all matching candidate groups.

    Priority: H
    """
    # Define a schema-like object with infrastructure namespaces in all groups.
    xsd_schema = SchemaNamespaceStub(
        target_namespace="http://www.w3.org/2001/XMLSchema",
        imports={"http://www.w3.org/XML/1998/namespace": None},
        namespaces={"xs": "http://www.w3.org/2001/XMLSchema"}
        )
    # Call the helper with declared fallback enabled.
    target_namespace, imported_namespaces, declared_match_namespaces = (
        ValidatorUtils._prepare_schema_namespace_matches(
            xsd_schema, # type: ignore
            allow_declared_namespace_match=True
        )
    )
    # Expected outcome: infrastructure namespaces are not match candidates.
    assert target_namespace is None
    assert imported_namespaces == set()
    assert declared_match_namespaces == set()


def test_prepare_schema_namespace_matches_handles_missing_or_none_imports():
    """
    Test that _prepare_schema_namespace_matches() handles missing or
    None imports defensively.

    Priority: H
    """
    # Define a schema-like object where `imports` exists but is None.
    schema_with_none_imports = SchemaNamespaceStub(
        target_namespace="http://example.com/target"
        )
    schema_with_none_imports.imports = None # type: ignore
    # Define a schema-like object where `imports` is missing entirely.
    schema_with_missing_imports = SchemaNamespaceStub(
        target_namespace="http://example.com/target"
        )
    del schema_with_missing_imports.imports
    # Call the helper for both edge cases.
    none_result = ValidatorUtils._prepare_schema_namespace_matches(
        schema_with_none_imports, # type: ignore
        allow_declared_namespace_match=False
    )
    missing_result = ValidatorUtils._prepare_schema_namespace_matches(
        schema_with_missing_imports, # type: ignore
        allow_declared_namespace_match=False
    )
    # Expected outcome: missing/None imports behave as an empty import mapping.
    assert none_result == (
        "http://example.com/target",
        set(),
        set()
    )
    assert missing_result == (
        "http://example.com/target",
        set(),
        set()
    )


def test_schema_matches_xml_namespaces_no_target_namespace_but_imported_matches(
        setup_test_files
        ):
    """
    Test that schema_matches_xml_namespaces() correctly returns True when
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
    extracted_namespaces = ValidatorUtils.extract_namespaces(xml_root)
    # Call the method under test.
    result = ValidatorUtils.schema_matches_xml_namespaces(
        xsd_schema=xsd_schema,
        xml_namespaces=extracted_namespaces # type: ignore
        )
    # Expected: should return True since the imported namespace matches.
    assert result is True, (
        "Expected schema_matches_xml_namespaces() to return True, but got False."
        )

def test_schema_matches_xml_namespaces_no_target_namespace_and_no_match(
        setup_test_files
        ):
    """
    Test that schema_matches_xml_namespaces() correctly returns False when
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
    extracted_namespaces = ValidatorUtils.extract_namespaces(xml_root)
    # Call the method under test.
    result = ValidatorUtils.schema_matches_xml_namespaces(
        xsd_schema=xsd_schema,
        xml_namespaces=extracted_namespaces # type: ignore
        )
    # Expected: should return False since no namespace matches.
    assert result is False, (
        "Expected schema_matches_xml_namespaces() to return False, but got True."
        )

def test_schema_matches_xml_namespaces_empty_namespaces_in_xml(setup_test_files):
    """
    Test that schema_matches_xml_namespaces() correctly returns False when
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
    extracted_namespaces = ValidatorUtils.extract_namespaces(xml_root)
    # Call the method under test.
    result = ValidatorUtils.schema_matches_xml_namespaces(
        xsd_schema=xsd_schema,
        xml_namespaces=extracted_namespaces  # type: ignore
        )
    # Expected: should return False since the XML has no namespaces.
    assert result is False, (
        "Expected schema_matches_xml_namespaces() to return False, but got True."
        )

def test_schema_matches_xml_namespaces_no_namespaces_anywhere(setup_test_files):
    """
    Test that schema_matches_xml_namespaces() correctly returns False when
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
    extracted_namespaces = ValidatorUtils.extract_namespaces(xml_root)
    # Call the method under test.
    result = ValidatorUtils.schema_matches_xml_namespaces(
        xsd_schema=xsd_schema,
        xml_namespaces=extracted_namespaces # type: ignore
        )
    # Expected: should return False since neither XML nor XSD have namespaces.
    assert result is False, (
        "Expected schema_matches_xml_namespaces() to return False, but got True."
        )

def test_schema_matches_xml_namespaces_handles_unexpected_exceptions(
        setup_test_files
        ):
    """
    Test that schema_matches_xml_namespaces() raises an exception when an
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
    extracted_namespaces = ValidatorUtils.extract_namespaces(xml_root)
    # Expect an exception when trying to load a **malformed XSD schema**.
    with pytest.raises(ParseError, match="mismatched tag"):
        xsd_schema = XMLSchema(str(xsd_file))  # This should raise an error.
        # Call the method under test (should never be reached due to error).
        _ = ValidatorUtils.schema_matches_xml_namespaces(
            xsd_schema=xsd_schema,
            xml_namespaces=extracted_namespaces # type: ignore
            )

# get_file_paths()

def test_get_file_paths_single_file_returns_file_and_true(tmp_path):
    """
    Test that get_file_paths() returns a single file path and True
    when the provided path points directly to a file.
    """
    # Create one XML file in pytest's temporary test folder.
    xml_file = tmp_path / "single.xml"
    xml_file.write_text("<root />", encoding="utf-8")
    # Call the method under test with a string path.
    file_paths, single_file = ValidatorUtils.get_file_paths(
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

def test_get_file_paths_directory_returns_sorted_matching_files(tmp_path):
    """
    Test that get_file_paths() returns only matching files from a
    directory, sorted in deterministic order.
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
    file_paths, single_file = ValidatorUtils.get_file_paths(
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

def test_get_file_paths_directory_single_matching_file_returns_true(tmp_path):
    """
    Test that get_file_paths() returns True when a directory contains
    exactly one file with the requested extension.
    """
    # Create exactly one matching XSD file.
    xsd_file = tmp_path / "schema.xsd"
    xsd_file.write_text("<schema />", encoding="utf-8")
    # Create a non-matching XML file, which should be ignored.
    xml_file = tmp_path / "document.xml"
    xml_file.write_text("<root />", encoding="utf-8")
    # Call the method under test for XSD files.
    file_paths, single_file = ValidatorUtils.get_file_paths(
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

def test_get_file_paths_normalizes_file_extension_argument(tmp_path):
    """
    Test that get_file_paths() accepts file extensions with a leading
    dot and mixed letter casing.
    """
    # Create one XML file with the normalized lowercase extension.
    xml_file = tmp_path / "document.xml"
    xml_file.write_text("<root />", encoding="utf-8")
    # Call the method under test with a leading dot and mixed casing.
    file_paths, single_file = ValidatorUtils.get_file_paths(
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

def test_get_file_paths_empty_directory_for_extension_raises_value_error(
    tmp_path
):
    """
    Test that get_file_paths() raises ValueError when a directory has
    no files with the requested extension.
    """
    # Create a file with a different extension, so no XML files match.
    xsd_file = tmp_path / "schema.xsd"
    xsd_file.write_text("<schema />", encoding="utf-8")
    # Expect a clear error when no matching XML files are found.
    with pytest.raises(
        ValueError,
        match=r"No \.xml files found in folder:"
    ):
        _ = ValidatorUtils.get_file_paths(tmp_path, "xml")

def test_get_file_paths_invalid_path_raises_value_error(tmp_path):
    """
    Test that get_file_paths() raises ValueError when the provided
    path is neither an existing file nor an existing directory.
    """
    # Create a path object that points to nothing.
    missing_path = tmp_path / "missing.xml"
    # Expect a clear error for a path that is neither file nor folder.
    with pytest.raises(
        ValueError,
        match="The provided path is neither a file nor a folder:"
    ):
        _ = ValidatorUtils.get_file_paths(missing_path, "xml")

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

# _check_file_path()

def test_check_file_path_returns_none_for_valid_file(tmp_path):
    """
    Test that _check_file_path() returns None when the file has a
    supported extension, exists and is not empty.
    """
    # Create a non-empty XML file.
    xml_file = tmp_path / "valid.xml"
    xml_file.write_text("<root />", encoding="utf-8")
    # Call the helper with the lowercase file extension.
    error = ValidatorUtils._check_file_path(xml_file, ".xml")
    # Expect no error for a processable file.
    assert error is None, (
        f"Expected no file path error; got {error}."
    )

def test_check_file_path_reports_unsupported_file_type(tmp_path):
    """
    Test that _check_file_path() returns an error dictionary when the
    file extension is not supported.
    """
    # Create a file with an unsupported extension.
    unsupported_file = tmp_path / "invalid.txt"
    unsupported_file.write_text("not XML or XSD", encoding="utf-8")
    # Call the helper with the unsupported file extension.
    error = ValidatorUtils._check_file_path(unsupported_file, ".txt")
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
    """
    # Create a path object that points to a missing XML file.
    missing_file = tmp_path / "missing.xml"
    # Call the helper with a supported file extension.
    error = ValidatorUtils._check_file_path(missing_file, ".xml")
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
    """
    # Create an empty XSD file.
    empty_file = tmp_path / "empty.xsd"
    empty_file.write_text("", encoding="utf-8")
    # Call the helper with a supported file extension.
    error = ValidatorUtils._check_file_path(empty_file, ".xsd")
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
    """
    # Create malformed XML content that would fail if parsing happened.
    xml_file = tmp_path / "invalid.xml"
    xml_file.write_text("<root>", encoding="utf-8")
    # Call the helper with parsing disabled.
    ValidatorUtils._parse_file_for_sanity_check(
        xml_file,
        ".xml",
        None,
        False
    )
    # No assertion is needed: reaching this line means no parsing occurred.

def test_parse_file_for_sanity_check_parses_valid_xml(tmp_path):
    """
    Test that _parse_file_for_sanity_check() accepts a well-formed XML
    file when parsing is enabled.
    """
    # Create a well-formed XML file.
    xml_file = tmp_path / "valid.xml"
    xml_file.write_text("<root />", encoding="utf-8")
    # Call the helper with parsing enabled.
    ValidatorUtils._parse_file_for_sanity_check(
        xml_file,
        ".xml",
        None,
        True
    )
    # No assertion is needed: reaching this line means parsing succeeded.

def test_parse_file_for_sanity_check_raises_for_invalid_xml(tmp_path):
    """
    Test that _parse_file_for_sanity_check() raises a parsing error for
    malformed XML content.
    """
    # Create malformed XML content.
    xml_file = tmp_path / "invalid.xml"
    xml_file.write_text("<root>", encoding="utf-8")
    # Expect lxml to raise an XML parsing exception.
    with pytest.raises((etree.ParseError, etree.XMLSyntaxError)):
        ValidatorUtils._parse_file_for_sanity_check(
            xml_file,
            ".xml",
            None,
            True
        )

def test_parse_file_for_sanity_check_compiles_valid_xsd(tmp_path):
    """
    Test that _parse_file_for_sanity_check() accepts a well-formed and
    valid XSD schema when parsing is enabled.
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
    ValidatorUtils._parse_file_for_sanity_check(
        xsd_file,
        ".xsd",
        None,
        True
    )
    # No assertion is needed: reaching this line means schema parsing succeeded.

def test_parse_file_for_sanity_check_raises_for_invalid_xsd(tmp_path):
    """
    Test that _parse_file_for_sanity_check() raises a schema parsing
    error for a well-formed but invalid XSD schema.
    """
    # Create a well-formed XML document that is not a valid XSD schema.
    xsd_file = tmp_path / "invalid.xsd"
    xsd_file.write_text("<root />", encoding="utf-8")
    # Expect lxml to reject the document as an XSD schema.
    with pytest.raises(etree.XMLSchemaParseError):
        ValidatorUtils._parse_file_for_sanity_check(
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
    """
    # Create an exception with a custom message attribute.
    error = Exception("Parsing failed.")
    error.msg = "Opening and ending tag mismatch." # type: ignore
    # Define the default facets for the error type.
    default_facets = {
        Exception: ["msg"]
    }
    # Call the helper without explicit facets.
    error_details = ValidatorUtils._extract_error_details(
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
    error_details = ValidatorUtils._extract_error_details(
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
    """
    # Create an exception with a tuple-valued position attribute.
    error = Exception("Parsing failed.")
    error.position = (7, 15) # type: ignore
    # Define the default facets for the error type.
    default_facets = {
        Exception: ["position"]
    }
    # Call the helper without explicit facets.
    error_details = ValidatorUtils._extract_error_details(
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


def test_extract_error_details_skips_none_values_by_default():
    """
    Test that _extract_error_details() omits facets whose value is None
    by default.
    """
    # Create an exception with a None-valued custom attribute.
    error = Exception("Parsing failed.")
    error.filename = None # type: ignore
    # Define the default facets for the error type.
    default_facets = {
        Exception: ["filename"]
    }
    # Call the helper without overriding the default skip behavior.
    error_details = ValidatorUtils._extract_error_details(
        error,
        None,
        default_facets
    )
    # Ensure the None-valued facet was omitted.
    assert "filename" not in error_details, (
        f"Unexpected None-valued facet in error details: {error_details}."
    )
    # Ensure the error type is still included.
    assert error_details["Error type"] == "Exception", (
        f"Expected 'Exception'; got '{error_details['Error type']}'."
    )


def test_extract_error_details_can_keep_none_values():
    """
    Test that _extract_error_details() can preserve facets whose value
    is None when explicitly requested.
    """
    # Create an exception with a None-valued custom attribute.
    error = Exception("Parsing failed.")
    error.filename = None # type: ignore
    # Define the default facets for the error type.
    default_facets = {
        Exception: ["filename"]
    }
    # Call the helper and explicitly preserve None-valued facets.
    error_details = ValidatorUtils._extract_error_details(
        error,
        None,
        default_facets,
        skip_none_error_facets=False
    )
    # Ensure the None-valued facet was preserved.
    assert "filename" in error_details, (
        f"Expected filename facet in error details: {error_details}."
    )
    assert error_details["filename"] is None, (
        f"Expected filename to be None; got {error_details['filename']}."
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
    """
    # Create an empty error list, mirroring sanity_check_files().
    errors: list[dict[str, str | None]] = []
    # Create a sample path. The file does not need to exist for this helper.
    file_path = Path("sample.xml")
    # Call the helper with only the required error information.
    ValidatorUtils._append_file_error(
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
    ValidatorUtils._append_file_error(
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
