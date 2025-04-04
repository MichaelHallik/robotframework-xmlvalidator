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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.


"""
Provides utility functions to support XML and XSD validation tasks.

This module is used internally by the XmlValidator library to assist 
with file resolution, namespace extraction, validation sanity checks, 
and schema matching.

It does not interact with Robot Framework directly, but supports the 
functionality exposed by the main library class.

Features:

- Extraction of XML namespaces from parsed documents.
- Resolution and validation of file and directory paths.
- Well-formedness checks for XML and XSD files.
- Mapping of XML namespaces to matching XSD schemas.
"""


# pylint: disable=I1101:c-extension-no-member


from __future__ import annotations
# Standard library imports.
from pathlib import Path
from typing import List, Optional, Tuple, Union, TYPE_CHECKING
# Third party library imports.
from lxml import etree
from robot.api import logger
# Local application imports.
from .xml_validator_results import ValidatorResult
if TYPE_CHECKING:
    from xmlschema import XMLSchema


class ValidatorUtils:
    """
    A stateless utility class for common XML and XSD validation 
    support operations.

    `ValidatorUtils` provides reusable static methods used internally by 
    the `XmlValidator` class and its supporting modules. It handles 
    tasks such as:

    - Extracting namespaces from XML documents.
    - Resolving and validating file and directory paths.
    - Performing well-formedness and sanity checks on files.
    - Matching XML namespaces to candidate XSD schemas.

    All methods are static and the class maintains no internal state.
    """

    __version__ = '1.0.0'

    @staticmethod
    def _resolve_path(path: str | Path) -> Path:
        """
        Resolves a file or directory path to an absolute `Path` object.

        This internal helper method accepts either a string or a `Path` 
        instance and returns a resolved absolute path.

        Args:

        - path (str or Path):
            A relative or absolute file or folder path.

        Returns:
            Path:
                The resolved absolute path.

        Notes:

        - This method does not check for file existence or permissions.
        - Used internally to normalize paths in validation workflows.
        """
        resolved_path = Path(path).resolve() if isinstance(path, str) else path.resolve()
        return resolved_path

    @staticmethod
    def extract_xml_namespaces(
            xml_root: etree.ElementBase,
            return_dict: Optional[bool] = False,
            include_nested: Optional[bool] = False
            ) -> Union[
                set[str],
                dict[str | None, str]
                ]:
        """
        Extracts XML namespaces from an XML root element.

        This method retrieves namespaces declared in the `xmlns` 
        attributes of the XML document.
        
        Namespaces can be returned as:

        - A *set* of namespace URIs (default).
        - A *dictionary* mapping prefixes to URIs (`return_dict=True`).

        The method can optionally search nested elements for additional 
        namespace declarations (`include_nested=True`).

        Args:

        - xml_root (etree.ElementBase):
          The root element of the parsed XML document.
        - return_dict (bool, optional):
          If True, returns a dict mapping namespace prefixes to URIs. 
          If False, returns a set of URIs. Defaults to False.
        - include_nested (bool, optional):
          If True, also includes namespaces declared in nested elements. 
          Defaults to False.

        Returns:

        - set[str] | dict[Optional[str], str]:
          A set of namespace URIs or a dict mapping prefixes to URIs. 
          The default namespace (no prefix) is represented as `None`.

        Raises:

        - Exception:
          Any parsing or extraction error is propagated upstream for 
          centralized error handling.

        Notes:

        - If no namespaces are found, an empty set or dict is returned.
        - The internal helper `_extract_nested_namespaces` performs a 
          recursive search of the XML tree when `include_nested` is 
          enabled.
        - This method does not catch or handle errors — they are 
          reported as part of the validation error pipeline.

        Example Usage:

        >>> xml_root = etree.fromstring('<root xmlns:ns1=\"http://example.com/ns1\"/>')
        >>> extract_xml_namespaces(xml_root)
        {'http://example.com/ns1'}

        >>> extract_xml_namespaces(xml_root, return_dict=True)
        {'ns1': 'http://example.com/ns1'}
        """
        def _extract_nested_namespaces(element: etree.ElementBase) -> dict[str | None, str]:
            """
            Recursively extracts namespaces from all elements in the XML 
            tree.

            Args:
            - element (etree.ElementBase):
              The starting element for extraction.

            Returns:
            - dict[str | None, str]:
              A dictionary mapping prefixes to URIs.
            """
            all_namespaces = {}
            for el in element.iter(None): # Explicitly passing `None` to avoid warnings.
                # Merge any new namespaces found.
                all_namespaces.update(
                    {
                        k.replace("xmlns:", "") if k else None: v
                        for k, v in ( el.nsmap or {} ).items()
                    }
                )
            return all_namespaces

        try:
            # Collect all namespaces, including root.
            if include_nested:
                namespaces = _extract_nested_namespaces(xml_root)
            # Extract namespaces explicitly from the root element.
            else:
                namespaces = {
                    k.replace("xmlns:", "") if k else None: v
                    # lxml provides namespaces through the nsmap attribute.
                    for k, v in ( xml_root.nsmap or {} ).items() # Ensure nsmap is a dictionary.
                    }
            # Determine the return type based on `return_dict`.
            return namespaces if return_dict else set(namespaces.values())
        # Catch any exception, propagating it upstream for further handling.
        except Exception: # pylint: disable=W0706:try-except-raise
            # Keep the original error intact.
            raise

    @staticmethod
    def get_file_paths(
        file_path: str | Path,
        file_type: str
        ) -> Tuple[List[Path], bool]:
        """
        Resolves files from a given path and filters them by type.

        If the path is a file, it returns a single-item list and a 
        True flag. If the path is a directory, it returns all files 
        with the matching extension and a boolean indicating whether 
        exactly one file was found.

        Args:

        - file_path (str or Path):
            Path to a file or directory to validate and inspect.

        - file_type (str):
            Expected file extension (e.g., "xml" or "xsd"). Used when 
            scanning a folder.

        Returns:

        - Tuple[List[Path], bool]:
            - A list of resolved `Path` objects that match the file type.
            - A boolean indicating whether exactly one file was found.

        Raises:

        - ValueError:
            - If the path is neither a file nor a folder.
            - If no files with the expected extension are found in a folder.

        Notes:

        - The method uses `.glob(f"*.{file_type}")` when inspecting folders.
        - Paths are normalized using `_resolve_path()`.
        """
        # Delegate resolving the provided path.
        resolved_path = ValidatorUtils._resolve_path(file_path)
        # Path is to a single file.
        if resolved_path.is_file():
            # Then return the file.
            return [resolved_path], True
        # Path is to a folder, assumed to hold one or more xsd files.
        if resolved_path.is_dir():
            # Get and resolve the path(s) to the file(s).
            resolved_paths = list(
                resolved_path.glob(f"*.{file_type}")
                )
            # Fail if there are no files in the folder.
            if not resolved_paths:
                raise ValueError(
                    f"No files reside in the folder: {resolved_paths}."
                    )
            # There are one or more files in the folder.
            return resolved_paths, len(resolved_paths) == 1
        # Fail if the path is neither a file nor a folder.
        raise ValueError(
            f'The provided path is neither a file nor a folder: {resolved_path}'
            )

    @staticmethod
    def match_namespace_to_schema(
        xsd_schema: XMLSchema,
        xml_namespaces: set[str]
        ) -> bool:
        """
        Matches an XSD schema to an XML document based on namespace 
        rules.

        This method verifies whether a given XSD schema is applicable to 
        an XML document by checking for namespace compatibility. The 
        matching logic follows these rules:

        1. If the XSD schema defines a `target_namespace`, it must be 
           present in the XML document's declared namespaces.
        2. If no match is found via `target_namespace`, the method 
           checks whether any of the schema's declared namespaces 
           (`xsd_schema.namespaces.values()`) are present in the XML.
        3. If neither check passes, the schema is considered not to 
           match.

        Args:

        - xsd_schema (XMLSchema):
          The compiled XSD schema object to test against.

        - xml_namespaces (set[str]):
          A set of namespace URIs declared in the XML document.

        Returns:

        - bool:
          `True` if the schema matches the XML document's namespaces; 
          `False` otherwise.

        Raises:

        - Exception:
          Propagates any unexpected errors encountered during namespace 
          access or comparison.

        Notes:

        - This function does not validate the XML against the schema — it only 
          performs a namespace-level compatibility check.
        - Used internally to assist with schema selection during multi-schema 
          validation.
        """
        try:
            # Primary check: if target namespace is explicitly present in XML.
            if xsd_schema.target_namespace is not None:
                if xsd_schema.target_namespace in xml_namespaces:
                    return True
            # Check if any other defined namespaces match.
            if any(
                ns in xml_namespaces for ns in xsd_schema.namespaces.values()
                ):
                return True
            # No matching namespace found.
            return False
        except Exception: # pylint: disable=W0706:try-except-raise
            raise

    @staticmethod
    def sanity_check_files( # pylint: disable=R0914:too-many-locals
        file_paths: List[Path],
        base_url: Optional[str] = None,
        error_facets: Optional[List[str]] = None,
        parse_files: Optional[bool] = False
        ) -> ValidatorResult:
        """
        Performs sanity checks on XML or XSD files and returns a 
        ValidatorResult instance.

        This method checks each file for basic validity, including:

        - Existence
        - Non-empty content
        - Correct file extension (".xml" or ".xsd")
        - Optional well-formedness and XSD parsing (`parse_files=True`)

        If any file fails a check, its error details are collected and 
        returned as part of a `ValidatorResult` object. Otherwise, the 
        validation is marked as successful.

        Args:

        - file_paths (List[Path]):
          A list of file paths (XML or XSD) to validate.

        - base_url (Optional[str]):
          An optional base URL to resolve includes or imports during 
          parsing (used when `parse_files=True`).

        - error_facets (Optional[List[str]]):
          A list of exception attributes to extract and include in the 
          error details (e.g., "msg", "position").

        - parse_files (bool, optional):
          If True, performs well-formedness checks and XSD schema 
          validation. Defaults to False.

        Returns:

        - ValidatorResult:
          An object with `success: bool` and `error: List[Dict[str, Any]]`.

        Notes:

        - This method catches `OSError`, `etree.XMLSyntaxError`, 
          `etree.ParseError`, and related schema exceptions.
        - If no errors are found, `ValidatorResult.success` is True and 
          `error` is None.
        - Used during initial file intake to catch structural issues before 
          full validation begins.
        """
        # Explicitly type errors and default_facets for clarity.
        errors: List[ dict[str, Optional[str]] ] = []
        default_facets: dict[ type, list[str] ] = {
            OSError: ["strerror"],
            etree.ParseError: ["msg", "position"],
            etree.XMLSchemaParseError: ["msg", "position"],
            etree.XMLSyntaxError: ["msg", "position"]
            }

        # Helper function to process errors into a data structure.
        def append_error(
                file_path: Path,
                reason: str,
                additional_details: Optional[dict] = None
                ) -> None:
            """
            Helper function to append an error dictionary to the errors 
            list.
            """
            # Always add the file path and the general reason.
            error: dict[ str, Optional[str] ] = {
                "file": str(file_path),
                "reason": reason
                }
            # Optionally, add more error details (if provided).
            if additional_details:
                error.update(additional_details)
            # Add the error to the container list (of errors).
            errors.append(error)

        for file_path in file_paths:
            # Establish the file type/extension for the current file.
            file_type = file_path.suffix.lower()
            # General validations.
            if file_type not in {".xml", ".xsd"}:
                # Incorrect file exstension.
                append_error(
                    file_path,
                    f"Unsupported file type: {file_type}.",
                    {"Error type": "ValueError"}
                )
                continue
            if not file_path.exists():
                # File does not exist.
                append_error(
                    file_path,
                    f"The {file_type.removeprefix('.')} file does not exist.",
                    {"Error type": "OSError"}
                )
                continue
            if file_path.stat().st_size == 0:
                # File is empty.
                append_error(
                    file_path,
                    "File is empty.",
                    {"Error type": "ValueError"}
                )
                continue
            # XML/XSD specific validations.
            try:
                # Read the file.
                with file_path.open("rb") as file:
                    # Validate well-formedness (xml or xsd).
                    if parse_files:
                        tree = etree.parse(
                            file,
                            parser=etree.XMLParser(),
                            base_url=base_url # type:ignore
                            )
                        # Validate the XSD schema as such.
                        if file_type == '.xsd':
                            _ = etree.XMLSchema(tree)
            # Handle validation failures.
            except (
                OSError,
                etree.ParseError,
                etree.XMLSchemaParseError,
                etree.XMLSyntaxError
                ) as e:
                # Determine error facets based on error type or provided facets.
                facets_to_include = error_facets or default_facets.get(
                    type(e), []
                    )
                # Initialize the error details dict.
                error_details: dict[str, Optional[str]] = {}
                # Add aspects/details of the caught error.
                for facet in facets_to_include:
                    if hasattr(e, facet):
                        value = getattr(e, facet, None)
                        # Handle tuple values like (line, column).
                        if isinstance(value, tuple):
                            value = f"Line {value[0]}, Column {value[1]}."
                        error_details[facet] = value
                    logger.warn(
                        f"Facet '{facet}' is not an attribute of error type'{type(e).__name__}'."
                        )
                # Add the error type to the error details
                error_details['Error type'] = type(e).__name__
                # Append the error to the return list.
                append_error(file_path, "File parsing failed.", error_details)
        # Determine success based on whether there are errors.
        success = len(errors) == 0
        return ValidatorResult(success=success, error=errors)
