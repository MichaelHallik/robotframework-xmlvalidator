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
Contains unit tests for the src/xmlvalidator/namespaces.py module.

See for an overview of all tests the file test/_doc/unit/overview.html.
"""

# pylint: disable=I1101:c-extension-no-member
# pylint: disable=W0212:protected-access
# pylint: disable=C0302:too-many-lines

# Standard library imports.
from xml.etree.ElementTree import ParseError

# Third-party library imports.
import pytest
from lxml import etree
from xmlschema import XMLSchema

# Local application imports.
from xmlvalidator import namespaces as namespaces_module
from xmlvalidator.namespaces import (
    _prepare_schema_namespace_matches,
    extract_namespaces,
    schema_matches_xml_namespaces,
)


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
    extracted_namespaces_set = extract_namespaces(
        xml_root
        )
    extracted_namespaces_dict = extract_namespaces(
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
    extracted_namespaces_set = extract_namespaces(
        xml_root
        )
    extracted_namespaces_dict = extract_namespaces(
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
    extracted_namespaces_set = extract_namespaces(
        xml_root
        )
    extracted_namespaces_dict = extract_namespaces(
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
    extracted_namespaces_set = extract_namespaces(
        xml_root
        )
    extracted_namespaces_dict = extract_namespaces(
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
    extracted_namespaces_set = extract_namespaces(
        xml_root
        )
    extracted_namespaces_dict = extract_namespaces(
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
    extracted_namespaces_set = extract_namespaces(
        xml_root, include_nested=True
        )
    extracted_namespaces_dict = extract_namespaces(
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
    extracted_namespaces_set = extract_namespaces(
        xml_root
        )
    extracted_namespaces_dict = extract_namespaces(
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
    extracted_namespaces_set = extract_namespaces(
        xml_root, include_nested=True
        )
    extracted_namespaces_dict = extract_namespaces(
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
        _ = extract_namespaces(xml_root)

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
    extracted_namespaces_set = extract_namespaces(
        xml_root, include_nested=True
        )
    extracted_namespaces_dict = extract_namespaces(
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


def test_schema_matches_xml_namespaces_returns_true_for_matching_target_namespace(
        setup_test_files,
        monkeypatch
        ):
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
    # Suppress Robot's console logger during direct unit testing.
    monkeypatch.setattr(namespaces_module.logger, "info", lambda *_, **__: None)
    # Extract namespaces from XML.
    parsed_tree = etree.parse(str(xml_file), parser=etree.XMLParser())
    xml_root = parsed_tree.getroot()
    extracted_namespaces = extract_namespaces(xml_root)
    # Call the method under test.
    result = schema_matches_xml_namespaces(
        xsd_schema=xsd_schema,
        xml_namespaces=extracted_namespaces # type: ignore
        )
    # Assertion: the schema should match.
    assert result is True, (
        "Expected match, but schema was not recognized as valid."
        )

def test_schema_matches_xml_namespaces_returns_false_for_non_matching_target_namespace(
    setup_test_files
):
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
    extracted_namespaces = extract_namespaces(
        xml_root, return_dict=False
        )
    # Call the method under test.
    result = schema_matches_xml_namespaces(
        xsd_schema=xsd_schema,
        xml_namespaces=extracted_namespaces # type: ignore
        )
    # Expected outcome: False because namespaces do not match.
    assert result is False, (f"Expected False, but got {result}.")

def test_schema_matches_xml_namespaces_match_with_imported_namespace(
        setup_test_files,
        monkeypatch
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
    # Suppress Robot's console logger during direct unit testing.
    monkeypatch.setattr(namespaces_module.logger, "info", lambda *_, **__: None)
    # Extract namespaces from XML.
    extracted_namespaces = extract_namespaces(xml_root)
    # Call the method under test.
    result = schema_matches_xml_namespaces(
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
    extracted_namespaces = extract_namespaces(xml_root)
    # Call the method under test.
    result = schema_matches_xml_namespaces(
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
    extracted_namespaces = extract_namespaces(xml_root)
    # Call the method under test.
    result = schema_matches_xml_namespaces(
        xsd_schema=xsd_schema,
        xml_namespaces=extracted_namespaces # type: ignore
        )
    # Expected outcome: declared-only namespaces should not be used for matching.
    assert result is False, (
        "Expected declared-only namespace to be ignored, but got a match."
        )

def test_schema_matches_xml_namespaces_allows_declared_namespace_match(
        setup_test_files,
        monkeypatch
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
    # Suppress Robot's console logger during direct unit testing.
    monkeypatch.setattr(namespaces_module.logger, "info", lambda *_, **__: None)
    # Extract namespaces from the XML.
    extracted_namespaces = extract_namespaces(xml_root)
    # Call the method under test with declared namespace fallback enabled.
    result = schema_matches_xml_namespaces(
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
    result = schema_matches_xml_namespaces(
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
    result = schema_matches_xml_namespaces(
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
        namespaces_module.logger,
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
    result = schema_matches_xml_namespaces(
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
        namespaces_module.logger,
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
    result = schema_matches_xml_namespaces(
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
    result_with_none_imports = schema_matches_xml_namespaces(
        xsd_schema=schema_with_none_imports, # type: ignore
        xml_namespaces=xml_namespaces
        )
    result_with_missing_imports = schema_matches_xml_namespaces(
        xsd_schema=schema_with_missing_imports, # type: ignore
        xml_namespaces=xml_namespaces
        )
    # Expected outcome: missing/None imports should not raise errors or match.
    assert result_with_none_imports is False
    assert result_with_missing_imports is False

def test_schema_matches_xml_namespaces_no_target_namespace_but_imported_matches(
        setup_test_files,
        monkeypatch
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
    # Suppress Robot's console logger during direct unit testing.
    monkeypatch.setattr(namespaces_module.logger, "info", lambda *_, **__: None)
    # Extract namespaces from the XML.
    extracted_namespaces = extract_namespaces(xml_root)
    # Call the method under test.
    result = schema_matches_xml_namespaces(
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
    extracted_namespaces = extract_namespaces(xml_root)
    # Call the method under test.
    result = schema_matches_xml_namespaces(
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
    extracted_namespaces = extract_namespaces(xml_root)
    # Call the method under test.
    result = schema_matches_xml_namespaces(
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
    extracted_namespaces = extract_namespaces(xml_root)
    # Call the method under test.
    result = schema_matches_xml_namespaces(
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
    extracted_namespaces = extract_namespaces(xml_root)
    # Expect an exception when trying to load a **malformed XSD schema**.
    with pytest.raises(ParseError, match="mismatched tag"):
        xsd_schema = XMLSchema(str(xsd_file))  # This should raise an error.
        # Call the method under test (should never be reached due to error).
        _ = schema_matches_xml_namespaces(
            xsd_schema=xsd_schema,
            xml_namespaces=extracted_namespaces # type: ignore
            )


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
        _prepare_schema_namespace_matches(
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
        _prepare_schema_namespace_matches(
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
        _prepare_schema_namespace_matches(
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
    none_result = _prepare_schema_namespace_matches(
        schema_with_none_imports, # type: ignore
        allow_declared_namespace_match=False
    )
    missing_result = _prepare_schema_namespace_matches(
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
