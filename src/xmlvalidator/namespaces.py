# Copyright 2024-2026 Michael Hallik
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
#
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Provides namespace extraction and XML/XSD namespace matching helpers.
"""

# pylint: disable=I1101:c-extension-no-member

# Standard library imports.
from typing import TYPE_CHECKING

# Third party library imports.
from lxml import etree
from robot.api import logger

if TYPE_CHECKING:
    from xmlschema import XMLSchema


INFRASTRUCTURE_SCHEMA_NAMESPACES = {
    "",
    "http://www.w3.org/2000/xmlns/",
    "http://www.w3.org/2001/XMLSchema",
    "http://www.w3.org/XML/1998/namespace",
}


def extract_namespaces(
    xml_root: etree.ElementBase,
    include_nested: bool | None = False,
    return_dict: bool | None = False
) -> set[str] | dict[str | None, str]:
    """
    Extracts XML namespaces from an XML root element.

    Namespaces can be returned as a set of namespace URIs or as a
    dictionary mapping prefixes to URIs. Nested namespace declarations
    are included only when `include_nested` is True.
    """
    if include_nested:
        namespaces = _extract_nested_namespaces(xml_root)
    else:
        namespaces = {
            k.replace("xmlns:", "") if k else None: v
            for k, v in (xml_root.nsmap or {}).items()
        }
    return namespaces if return_dict else set(namespaces.values())


def _extract_nested_namespaces(
    element: etree.ElementBase
) -> dict[str | None, str]:
    """
    Recursively extracts namespaces from all elements in an XML tree.
    """
    all_namespaces = {}
    for el in element.iter(None):
        all_namespaces.update(
            {
                k.replace("xmlns:", "") if k else None: v
                for k, v in (el.nsmap or {}).items()
            }
        )
    return all_namespaces


def schema_matches_xml_namespaces(
    xsd_schema: "XMLSchema",
    xml_namespaces: set[str],
    allow_declared_namespace_match: bool = False
) -> bool:
    """
    Matches an XSD schema to an XML document based on namespace rules.
    """
    (
        target_namespace,
        imported_namespaces,
        declared_match_namespaces
    ) = _prepare_schema_namespace_matches(
        xsd_schema,
        allow_declared_namespace_match
    )
    if target_namespace and target_namespace in xml_namespaces:
        logger.info(
            f"Schema matched by target namespace: '{target_namespace}'.",
            also_console=True
        )
        return True
    matching_imported_namespaces = imported_namespaces & xml_namespaces
    if matching_imported_namespaces:
        namespace = next(iter(matching_imported_namespaces))
        logger.info(
            f"Schema matched by imported namespace: '{namespace}'.",
            also_console=True
        )
        return True
    matching_declared_namespaces = declared_match_namespaces & xml_namespaces
    if matching_declared_namespaces:
        namespace = next(iter(matching_declared_namespaces))
        logger.info(
            f"Schema matched by declared namespace: '{namespace}'.",
            also_console=True
        )
        return True
    return False


def _prepare_schema_namespace_matches(
    xsd_schema: "XMLSchema",
    allow_declared_namespace_match: bool
) -> tuple[str | None, set[str], set[str]]:
    """
    Collects and filters schema namespaces used for XML matching.
    """
    target_namespace = xsd_schema.target_namespace
    imports = getattr(xsd_schema, "imports", None) or {}
    imported_namespaces = set(imports.keys())
    declared_namespaces = {
        ns
        for ns in getattr(xsd_schema, "namespaces", {}).values()
        if ns
    }
    declared_match_namespaces = (
        declared_namespaces if allow_declared_namespace_match else set()
    )
    all_candidate_namespaces = (
        ({target_namespace} if target_namespace else set())
        | imported_namespaces
        | declared_match_namespaces
    )
    infrastructure_namespaces = (
        all_candidate_namespaces & INFRASTRUCTURE_SCHEMA_NAMESPACES
    )
    target_namespace = (
        target_namespace
        if target_namespace not in INFRASTRUCTURE_SCHEMA_NAMESPACES
        else None
    )
    imported_namespaces -= INFRASTRUCTURE_SCHEMA_NAMESPACES
    declared_match_namespaces -= INFRASTRUCTURE_SCHEMA_NAMESPACES
    ignored_namespaces = (
        declared_namespaces
        - (
            ({target_namespace} if target_namespace else set())
            | imported_namespaces
            | declared_match_namespaces
        )
    ) | infrastructure_namespaces
    for namespace in sorted(ignored_namespaces):
        logger.info(
            f"Schema namespace ignored during matching: '{namespace}'.",
            also_console=False
        )
    return target_namespace, imported_namespaces, declared_match_namespaces
