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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Provides utility functions to support XML and XSD validation tasks.

This module is used internally by the XmlValidator library to assist
with sanity checks, file resolution, namespace extraction and schema
matching.
"""

# pylint: disable=I1101:c-extension-no-member

# Standard library imports.
from pathlib import Path
from typing import TYPE_CHECKING

# Third party library imports.
from lxml import etree
from robot.api import logger

# Local application imports.
from .xml_validator_results import ValidatorResult

# Keep XMLSchema available to type checkers without importing it at runtime.
if TYPE_CHECKING:
    from xmlschema import XMLSchema


class ValidatorUtils:
    """
    A stateless utility class for common XML and XSD validation
    support operations.

    `ValidatorUtils` provides static methods used internally by the
    the `XmlValidator` class and its supporting modules. It handles
    tasks such as:

    - Extracting namespaces from XML documents.
    - Resolving and validating file and directory paths.
    - Performing well-formedness and sanity checks on files.
    - Matching XML namespaces to candidate XSD schemas.

    All methods are static: the class maintains no internal state.
    """

    INFRASTRUCTURE_SCHEMA_NAMESPACES = {
        "",
        "http://www.w3.org/2000/xmlns/",
        "http://www.w3.org/2001/XMLSchema",
        "http://www.w3.org/XML/1998/namespace",
    }

    DEFAULT_ERROR_FACETS: dict[type, list[str]] = {
        OSError: ["strerror"],
        etree.ParseError: ["msg", "position"],
        etree.XMLSchemaParseError: ["msg", "position"],
        etree.XMLSyntaxError: ["msg", "position"]
    }

    # Namespace handling

    @staticmethod
    def extract_namespaces(
        xml_root: etree.ElementBase,
        include_nested: bool | None = False,
        return_dict: bool | None = False
    ) -> set[str] | dict[str | None, str]:
        """
        Extracts XML namespaces from an XML root element.

        This method retrieves namespaces declared in the `xmlns`
        attributes of an XML document.

        Namespaces can be returned as:

        - A *set* of namespace URIs (default).
        - A *dictionary*, mapping prefixes to URIs (`return_dict=True`).

        The method can optionally search nested elements for additional
        namespace declarations (`include_nested=True`).

        Args:

        - xml_root (etree.ElementBase):
          The root element of the parsed XML document.
        - include_nested (bool, optional):
          If True, also includes namespaces declared in nested elements.
          Defaults to False.
        - return_dict (bool, optional):
          If True, returns a dict, mapping namespace prefixes to URIs.
          If False, returns a set of URIs.
          Defaults to False.

        Returns:

        - set[str] | dict[str | None, str]:
          A set of namespace URIs or a dict mapping prefixes to URIs.
          Any default namespace (no prefix) are represented as `None`.

        Raises:

        - Exception:
          Any unexpected namespace extraction error is propagated
          unchanged to the caller.

        Notes:

        - If no namespaces are found, an empty set or dict is returned.
        - The nested helper `_extract_nested_namespaces` performs a
          recursive search of the XML tree when `include_nested` is
          enabled.
        - This method intentionally does not handle namespace extraction
          errors. Any exception is allowed to propagate to the caller,
          which can decide how to report or recover from it.

        Example Usage:

        >>> xml_root = etree.fromstring('<root xmlns:ns1=\"http://example.com/ns1\"/>')
        >>> extract_namespaces(xml_root)
        {'http://example.com/ns1'}
        >>> extract_namespaces(xml_root, return_dict=True)
        {'ns1': 'http://example.com/ns1'}
        """
        # Collect all namespaces, including root.
        if include_nested:
            namespaces = ValidatorUtils._extract_nested_namespaces(xml_root)
        # Extract namespaces explicitly from the root element.
        else:
            namespaces = {
                k.replace("xmlns:", "") if k else None: v
                # lxml provides namespaces through the nsmap attr.
                # Iterate over declared namespaces,
                # falling back to an empty mapping.
                for k, v in ( xml_root.nsmap or {} ).items() # Ensure dict.
            }
        # Determine the return type based on `return_dict`.
        return namespaces if return_dict else set(namespaces.values())

    @staticmethod
    def _extract_nested_namespaces(
        element: etree.ElementBase
    ) -> dict[str | None, str]:
        """
        Recursively extracts namespaces from all elements in the XML
        tree.

        Each lxml element can expose a namespace map through its
        `nsmap` attribute. That map contains namespace prefixes as
        keys and namespace URIs as values. For example, a prefixed
        namespace may look like:

        `{"abc": "https://example.com/abc"}`

        The XML default namespace has no prefix. lxml represents
        that case with `None` as the key, so this helper keeps that
        convention in the returned dictionary.

        The method walks over the provided element and every nested
        child element by using `element.iter(None)`. For each
        element, it reads the element's `nsmap`, safely treats a
        missing map as an empty dictionary, (defensively) normalizes any
        namespace prefix text, and merges the discovered namespaces into
        one result dictionary.

        Args:
        - element (etree.ElementBase):
          The starting element for extraction.

        Returns:
        - dict[str | None, str]:
          A dictionary mapping prefixes to URIs.
        """
        # Return container.
        all_namespaces = {}
        # Explicitly passing `None` to avoid warnings.
        for el in element.iter(None):
            # Merge any new namespaces found.
            all_namespaces.update(
                {
                    # Strip a defensive 'xmlns:' prefix if present;
                    # use None for default namespaces.
                    k.replace("xmlns:", "") if k else None: v
                    # lxml provides namespaces through the nsmap attr.
                    # Iterate over declared namespaces,
                    # falling back to an empty mapping.
                    for k, v in ( el.nsmap or {} ).items() # Ensure dict.
                }
            )
        return all_namespaces

    # Schema matching

    @staticmethod
    def schema_matches_xml_namespaces(
        xsd_schema: "XMLSchema",
        xml_namespaces: set[str],
        allow_declared_namespace_match: bool = False
    ) -> bool:
        """
        Matches an XSD schema to an XML document based on namespace
        rules.

        This method verifies whether a given XSD schema is applicable to
        an XML document by checking for namespace compatibility. The
        matching logic follows these rules:

        1. If the XSD schema defines a `target_namespace`, that
           namespace must be present in the XML document's declared
           namespaces.
        2. If no match is found via `target_namespace`, the method
           checks whether any explicitly imported schema namespace is
           present in the XML document's declared namespaces.
        3. If `allow_declared_namespace_match` is True, the method also
           checks whether any non-infrastructure namespace declared by
           the schema is present in the XML document's declared
           namespaces.
        4. If none of these checks pass, the schema is considered not
           to match.

        Args:

        - xsd_schema (XMLSchema):
          The compiled XSD schema object to test against.

        - xml_namespaces (set[str]):
          A set of namespace URIs declared in the XML document.

        - allow_declared_namespace_match (bool):
          If True, permits fallback matching against non-infrastructure
          namespaces declared by the schema. Defaults to False.

        Returns:

        - bool:
          `True` if the schema matches the XML document's namespaces;
          `False` otherwise.

        Raises:

        - Exception:
          Any unexpected error while reading schema namespace attributes
          is propagated unchanged to the caller.
        """
        # Collect and prepare schema namespaces for matching.
        (
            target_namespace,
            imported_namespaces,
            declared_match_namespaces
        ) = ValidatorUtils._prepare_schema_namespace_matches(
            xsd_schema,
            allow_declared_namespace_match
        )
        # Primary check: if target namespace is present in XML.
        if target_namespace and target_namespace in xml_namespaces:
            logger.info(
                f"Schema matched by target namespace: '{target_namespace}'.",
                also_console=True
            )
            return True
        # Secondary check: if any explicitly imported schema namespace matches.
        matching_imported_namespaces = imported_namespaces & xml_namespaces
        if matching_imported_namespaces:
            namespace = next(iter(matching_imported_namespaces))
            logger.info(
                f"Schema matched by imported namespace: '{namespace}'.",
                also_console=True
                )
            return True
        # Optional check: if any declared schema namespace matches.
        matching_declared_namespaces = declared_match_namespaces & xml_namespaces
        if matching_declared_namespaces:
            namespace = next(iter(matching_declared_namespaces))
            logger.info(
                f"Schema matched by declared namespace: '{namespace}'.",
                also_console=True
                )
            return True
        # No supported namespace match.
        return False

    @staticmethod
    def _prepare_schema_namespace_matches(
        xsd_schema: "XMLSchema",
        allow_declared_namespace_match: bool
    ) -> tuple[str | None, set[str], set[str]]:
        """
        Collects and filters schema namespaces used for XML matching.

        Args:

        - xsd_schema (XMLSchema):
          The compiled XSD schema object to inspect.

        - allow_declared_namespace_match (bool):
          If True, includes non-infrastructure declared schema
          namespaces as fallback matching candidates.

        Returns:

        - tuple[str | None, set[str], set[str]]:
          The target namespace, imported namespaces and optionally
          declared namespaces that may participate in XML/XSD matching.
        """
        # Collect target schema namespace.
        target_namespace = xsd_schema.target_namespace
        # Collect imported schema namespaces.
        imports = (
            getattr(
                xsd_schema,
                "imports",
                None
            ) or {}
        )
        imported_namespaces = set(imports.keys())
        # Collect declared schema namespaces.
        declared_namespaces = {
            ns
            for ns in getattr(xsd_schema, "namespaces", {}).values()
            if ns
        }
        declared_match_namespaces = (
            # Optionally elevate these namespaces to candidate status.
            declared_namespaces if allow_declared_namespace_match else set()
        )
        # Identify infrastructure schema namespaces.
        all_candidate_namespaces = (
            ({target_namespace} if target_namespace else set())
            | imported_namespaces
            | declared_match_namespaces
        )
        infrastructure_namespaces = (
            all_candidate_namespaces
            & ValidatorUtils.INFRASTRUCTURE_SCHEMA_NAMESPACES
        )
        # Remove infrastructure namespaces from the matching candidates.
        target_namespace = (
            target_namespace
            if target_namespace not in ValidatorUtils.INFRASTRUCTURE_SCHEMA_NAMESPACES
            else None
        )
        imported_namespaces -= ValidatorUtils.INFRASTRUCTURE_SCHEMA_NAMESPACES
        declared_match_namespaces -= ValidatorUtils.INFRASTRUCTURE_SCHEMA_NAMESPACES
        # Register ignored namespaces for logging/reporting purposes.
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

    # File path handling

    @staticmethod
    def get_file_paths(
        file_path: str | Path,
        file_extension: str
    ) -> tuple[list[Path], bool]:
        """
        Resolves files from the given path and filters them by
        the provided extension.

        If the path is a file, it returns a single-item-list and a
        True flag. If the path is a directory (and it contains at least
        one file), it returns all files with the matching extension and
        a boolean indicating whether exactly one file was found or not.

        Args:

        - file_path (str or Path):
            Path to a file or directory to validate and inspect.

        - file_extension (str):
            Expected file extension (e.g. "xml", ".xml", "xsd" or
            ".xsd"). Used when scanning a folder.

        Returns:

        - tuple[list[Path], bool]:
            - A list of resolved `Path` objects that match the file
              type.
            - A boolean indicating whether exactly one file was found.

        Raises:

        - ValueError:
            - If the path is neither a file nor a folder.
            - If no files with the expected extension are found in a
              folder.

        Notes:

        - Directory results are sorted to keep validation order
          deterministic.
        - The provided file extension is normalized, so callers may pass
          "xml", ".xml", "XML" or ".XML".
        """
        # Normalize the extension, accepting both "xml" and ".xml".
        file_extension = file_extension.lower().removeprefix(".")
        # Delegate path resolution.
        resolved_path = ValidatorUtils._resolve_path(file_path)
        # Path is to a single file.
        if resolved_path.is_file():
            # Then return the file.
            return [resolved_path], True
        # Path is to a folder, assumed to hold one or more files.
        if resolved_path.is_dir():
            # Get and resolve the path(s) to the file(s).
            resolved_paths = sorted(
                resolved_path.glob(f"*.{file_extension}")
            )
            # Fail if there are no files in the folder.
            if not resolved_paths:
                raise ValueError(
                    f"No .{file_extension} files found in folder: "
                    f"{resolved_path}."
                )
            # There are one or more files in the folder.
            return resolved_paths, len(resolved_paths) == 1
        # Fail if the path is neither a file nor a folder.
        raise ValueError(
            f'The provided path is neither a file nor a folder: {resolved_path}.'
        )

    @staticmethod
    def _resolve_path(path: str | Path) -> Path:
        """
        Accepts either a string or a `Path` instance and returns a
        resolved absolute path to a file or directory.

        Args:
            path (str or Path):
                A relative or absolute file or folder path.

        Returns:
            Path:
                The resolved absolute path.

        Notes:

        - This method does not check for file existence or permissions.
        - Used internally to normalize paths in validation workflows.
        """
        return Path(path).resolve() if isinstance(path, str) else path.resolve()

    # File sanity checks

    @staticmethod
    def sanity_check_files( # pylint: disable=R0914:too-many-locals
        file_paths: list[Path],
        base_url: str | None = None,
        error_facets: list[str] | None = None,
        parse_files: bool = False,
        skip_none_error_facets: bool = True
    ) -> ValidatorResult:
        """
        Performs sanity checks on XML or XSD files and returns a
        ValidatorResult instance.

        This method checks each file for basic validity, including:

        - File existence.
        - Non-empty content.
        - Correct file extension (".xml" or ".xsd").
        - Optional well-formedness and XSD parsing (`parse_files=True`).

        If any file fails a check, its error details are collected and
        returned as part of a `ValidatorResult` object. Otherwise, the
        validation is marked as successful.

        Args:

        - file_paths (list[Path]):
          A list of file paths (XML or XSD) to validate.

        - base_url (str | None):
          An optional base URL to resolve includes or imports during
          parsing (used when `parse_files=True`).

        - error_facets (list[str] | None):
          A list of exception attributes to extract and include in the
          error details (e.g., "msg", "position").

        - parse_files (bool, optional):
          If True, performs well-formedness checks and XSD schema
          validation. Defaults to False.

        - skip_none_error_facets (bool, optional):
          If True, omits requested error facets whose value is None.
          Defaults to True.

        Returns:

        - ValidatorResult:
          An object with `success: bool` and `error: list[dict[str, Any]]`.

        Notes:

        - This method catches `OSError`, `etree.XMLSyntaxError`,
          `etree.ParseError`, and related schema exceptions.
        - If no errors are found, `ValidatorResult.success` is True and
          the returned error collection is empty.
        - Used during initial file intake to catch structural issues before
          full validation begins.
        """
        # Explicitly type errors for clarity.
        errors: list[dict[str, str | None]] = []
        for file_path in file_paths:
            # Establish the file type/extension for the current file.
            file_type = file_path.suffix.lower()
            # General validations.
            file_error = ValidatorUtils._check_file_path(file_path, file_type)
            if file_error:
                errors.append(file_error)
                continue
            # XML/XSD specific validations.
            try:
                # Validate XML/XSD parsing when requested.
                ValidatorUtils._parse_file_for_sanity_check(
                    file_path,
                    file_type,
                    base_url,
                    parse_files
                )
            # Handle validation failures.
            except (
                OSError,
                etree.ParseError,
                etree.XMLSchemaParseError,
                etree.XMLSyntaxError
                ) as e:
                # Collect configured error details from the caught exception.
                error_details = ValidatorUtils._extract_error_details(
                    e,
                    error_facets,
                    ValidatorUtils.DEFAULT_ERROR_FACETS,
                    skip_none_error_facets
                )
                # Append the error to the return list.
                ValidatorUtils._append_file_error(
                    errors,
                    file_path,
                    "File parsing failed.",
                    error_details
                )
        # Determine success based on whether there are errors.
        success = len(errors) == 0
        return ValidatorResult(success=success, error=errors)

    @staticmethod
    def _check_file_path(
        file_path: Path,
        file_type: str
    ) -> dict[str, str | None] | None:
        """
        Checks whether a file path can be processed by sanity checks.

        Args:

        - file_path (Path):
          The file path to check.

        - file_type (str):
          The lowercase file extension, including the leading dot.

        Returns:

        - dict[str, str | None] | None:
          A structured error dictionary if the file path fails a basic
          check; otherwise, None.
        """
        # Check whether the file extension is supported.
        if file_type not in {".xml", ".xsd"}:
            return {
                "file": str(file_path),
                "reason": f"Unsupported file type: {file_type}.",
                "Error type": "ValueError"
            }
        # Check whether the file exists.
        if not file_path.exists():
            return {
                "file": str(file_path),
                "reason": (
                    f"The {file_type.removeprefix('.')} file does not exist."
                ),
                "Error type": "OSError"
            }
        # Check whether the file has content.
        if file_path.stat().st_size == 0:
            return {
                "file": str(file_path),
                "reason": "File is empty.",
                "Error type": "ValueError"
            }
        # The file path passed all basic checks.
        return None

    @staticmethod
    def _parse_file_for_sanity_check(
        file_path: Path,
        file_type: str,
        base_url: str | None,
        parse_files: bool
    ) -> None:
        """
        Parses a file when sanity checks include XML/XSD parsing.

        Args:

        - file_path (Path):
          The file path to parse.

        - file_type (str):
          The lowercase file extension, including the leading dot.

        - base_url (str | None):
          Optional base URL used by lxml to resolve includes or imports.

        - parse_files (bool):
          If True, parses XML/XSD files and compiles XSD schemas.

        Raises:

        - OSError:
          If the file cannot be opened.
        - etree.ParseError | etree.XMLSyntaxError:
          If XML/XSD parsing fails.
        - etree.XMLSchemaParseError:
          If XSD schema compilation fails.
        """
        # No parsing requested.
        if not parse_files:
            return
        # Read the file.
        with file_path.open("rb") as file:
            # Validate well-formedness (xml or xsd).
            tree = etree.parse(
                file,
                parser=etree.XMLParser(),
                base_url=base_url # type:ignore
                )
            # Validate the XSD schema as such.
            if file_type == ".xsd":
                _ = etree.XMLSchema(tree)

    @staticmethod
    def _extract_error_details(
        error: Exception,
        error_facets: list[str] | None,
        default_facets: dict[type, list[str]],
        skip_none_error_facets: bool = True
    ) -> dict[str, str | None]:
        """
        Extracts selected details from an exception into a dictionary.

        Args:

        - error (Exception):
          The caught exception to inspect.

        - error_facets (list[str] | None):
          Optional exception attribute names to include. If not
          provided, defaults are selected based on the exception type.

        - default_facets (dict[type, list[str]]):
          Default exception attribute names per exception type.

        - skip_none_error_facets (bool, optional):
          If True, omits requested error facets whose value is None.
          Defaults to True.

        Returns:

        - dict[str, str | None]:
          A dictionary containing selected exception details and the
          exception type name.
        """
        # Determine error facets based on provided facets or error type.
        facets_to_include = error_facets or default_facets.get(
            type(error),
            []
        )
        # Initialize the error details dict.
        error_details: dict[str, str | None] = {}
        # Add aspects/details of the caught error.
        for facet in facets_to_include:
            if hasattr(error, facet):
                value = getattr(error, facet, None)
                # Optionally skip empty exception details.
                if value is None and skip_none_error_facets:
                    continue
                # Handle tuple values like (line, column).
                if isinstance(value, tuple):
                    value = f"Line {value[0]}, Column {value[1]}."
                error_details[facet] = value
            # logger.warn(
            #     f"'{facet}' isn't an attr of error type'{type(error).__name__}'"
            #     )
        # Add the error type to the error details.
        error_details["Error type"] = type(error).__name__
        return error_details

    @staticmethod
    def _append_file_error(
        errors: list[dict[str, str | None]],
        file_path: Path,
        reason: str,
        additional_details: dict[str, str | None] | None = None
    ) -> None:
        """
        Appends a structured file validation error to the error list.

        Args:

        - errors (list[dict[str, str | None]]):
          The mutable list that collects validation errors.

        - file_path (Path):
          The file path associated with the error.

        - reason (str):
          A short, human-readable reason for the error.

        - additional_details (dict[str, str | None] | None):
          Optional additional error details.
        """
        # Always add the file path and the general reason.
        error: dict[str, str | None] = {
            "file": str(file_path),
            "reason": reason
        }
        # Optionally, add more error details (if provided).
        if additional_details:
            error.update(additional_details)
        # Add the error to the container list (of errors).
        errors.append(error)
