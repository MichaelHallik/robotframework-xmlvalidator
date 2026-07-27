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

# pylint: disable=I1101:c-extension-no-member

"""
Provides single-file XML validation execution.

The XmlValidationRunner class validates one XML file against either an
already-loaded schema or a schema loaded specifically for that file.
For XSD validation errors it prefers lxml's C-backed validator and falls
back to xmlschema-based error collection when needed.
"""

# Standard library imports.
from pathlib import Path
import re
from typing import Any, Literal, cast

# Third party library imports.
from lxml import etree
from robot.api import logger

# Local application imports.
from .files import sanity_check_files
from .schema.manager import ValidatorSchemaManager

ValidationBackend = Literal["auto", "lxml", "xmlschema"]
VALIDATION_BACKENDS = {"auto", "lxml", "xmlschema"}


def validate_validation_backend(
    validation_backend: str
) -> ValidationBackend:
    """
    Validates and normalizes the selected validation backend.
    """
    if validation_backend not in VALIDATION_BACKENDS:
        raise ValueError(
            "Unsupported validation_backend: "
            f"{validation_backend}. Expected one of: "
            f"{', '.join(sorted(VALIDATION_BACKENDS))}."
        )
    return cast(ValidationBackend, validation_backend)


class XmlValidationRunner:  # pylint: disable=R0903:too-few-public-methods
    """
    Executes validation of one XML file against one XSD schema.

    This class handles the actual single-file validation step. Schema
    loading and reuse remain delegated to ValidatorSchemaManager.
    """

    def __init__(
        self,
        schema_manager: ValidatorSchemaManager
    ) -> None:
        """
        Initializes an XmlValidationRunner instance.
        """
        self.schema_manager = schema_manager

    def validate_xml(  # pylint: disable=R0913:too-many-arguments, R0917:too-many-positional-arguments
        self,
        xml_file_path: Path,
        xsd_file_path: Path | BaseException | None = None,
        base_url: str | None = None,
        error_facets: list[str] | None = None,
        default_error_facets: list[str] | None = None,
        pre_parse: bool = True,
        skip_none_error_facets: bool = False,
        validation_backend: ValidationBackend = "auto"
        ) -> tuple[
            bool,
            list[dict[str, Any]] | None
            ]:
        """
        Validates an XML file against the active or provided XSD schema.
        """
        # Log informative.
        logger.info(
            f"Validating '{xml_file_path.name}'.", also_console=True
        )
        # Check upstream XSD matching led to an err pertaining to the XML.
        if isinstance(xsd_file_path, BaseException):
            return False, [{
                facet: str(xsd_file_path) if facet == "reason" else ""
                for facet in (error_facets or default_error_facets or [])
            }]
        # Sanity check the target (XML/XSD) files.
        sanity_check_result = sanity_check_files(
            [file_path for file_path in [
                xml_file_path, xsd_file_path
            ] if isinstance(file_path, Path) and file_path],
            base_url=base_url,
            parse_files=pre_parse,
            skip_none_error_facets=skip_none_error_facets
        )
        if not sanity_check_result.success:
            # Abort validation if one or more sanity checks failed.
            return False, sanity_check_result.error
        # Ensure a valid schema is loaded.
        loading_result = self.schema_manager.ensure_schema(
            xsd_file_path, base_url
        )
        if not loading_result.success:
            # Abort the validation if schema loading failed.
            logger.warn("Schema loading failed.")
            return False, loading_result.error
        validation_backend = validate_validation_backend(validation_backend)
        lxml_schema = self._get_lxml_schema(
            xsd_file_path,
            base_url,
            validation_backend
        )
        if validation_backend == "lxml" and lxml_schema is None:
            return False, [{
                facet: (
                    "lxml could not compile the XSD schema."
                    if facet == "reason"
                    else ""
                )
                for facet in (error_facets or default_error_facets or [])
            }]
        # Validate the XML and collect details for each XSD violation.
        errors = self._collect_validation_errors(
            xml_file_path,
            loading_result.value,
            lxml_schema,
            error_facets,
            default_error_facets,
            skip_none_error_facets
        )
        # Determine validity based on the presence of errors.
        return (True, None) if len(errors) == 0 else (False, errors)

    def _get_lxml_schema(
        self,
        xsd_file_path: Path | BaseException | None,
        base_url: str | None,
        validation_backend: ValidationBackend
    ) -> etree.XMLSchema | None:
        """
        Returns an lxml schema unless xmlschema-only validation is requested.
        """
        if validation_backend == "xmlschema":
            return None
        if not isinstance(xsd_file_path, Path) and xsd_file_path is not None:
            return None
        return self.schema_manager.get_lxml_schema(xsd_file_path, base_url)

    @staticmethod
    def _collect_validation_errors(  # pylint: disable=R0913:too-many-arguments, R0917:too-many-positional-arguments
        xml_file_path: Path,
        schema: Any,
        lxml_schema: etree.XMLSchema | None = None,
        error_facets: list[str] | None = None,
        default_error_facets: list[str] | None = None,
        skip_none_error_facets: bool = False
        ) -> list[dict[str, Any]]:
        """
        Collects configured error details for each XSD validation error.

        Under the hood, this method first tries to use lxml's C-backed
        XMLSchema validator. That path is much faster for large XML
        files and for invalid files that contain many XSD violations.
        If no lxml schema is available, it falls back to the loaded
        ``xmlschema`` schema object's ``iter_errors()`` method.

        Both validators expose details about each encountered error,
        such as ``path``, ``reason`` or ``message``. In this library,
        those details are called *error facets*. The caller can choose
        which facets should be copied into the returned error
        dictionaries by passing ``error_facets``. If no call-specific
        facets are passed, ``default_error_facets`` is used instead.

        For every validation error, this method creates one dictionary.
        Each dictionary contains the requested facet names as keys and
        the corresponding values from the validation error object as
        values.

        By default, requested facets whose value is ``None`` are kept and
        reported as ``Unavailable``. This gives logs, error tables and
        CSV output a stable shape: each requested facet is present for
        each collected validation error. If ``skip_none_error_facets`` is
        ``True``, requested facets without a value are omitted instead.
        """
        facets = error_facets or default_error_facets or []
        if lxml_schema is not None:
            return XmlValidationRunner._collect_lxml_validation_errors(
                xml_file_path,
                lxml_schema,
                facets,
                skip_none_error_facets
            )
        return [
            {
                # Collect the details/facets for each XSD violation.
                facet: (
                    getattr(err, facet, None)
                    if getattr(err, facet, None) is not None
                    else "Unavailable"
                )
                # Error facets to collect determined by arg or instance.
                for facet in facets
                if (
                    not skip_none_error_facets
                    or getattr(err, facet, None) is not None
                )
            }
            # Generate an err obj (with err details) per encountered violation.
            for err in schema.iter_errors(xml_file_path)
        ]

    @staticmethod
    def _collect_lxml_validation_errors(
        xml_file_path: Path,
        schema: etree.XMLSchema,
        facets: list[str],
        skip_none_error_facets: bool = False
    ) -> list[dict[str, Any]]:
        """
        Collects validation errors using lxml's C-backed XSD validator.
        """
        document = etree.parse(str(xml_file_path))
        if schema.validate(document):
            return []
        return [
            {
                facet: value if value is not None else "Unavailable"
                for facet in facets
                if (
                    (value := XmlValidationRunner._get_lxml_error_facet(
                        error,
                        facet,
                        document
                    )) is not None
                    or not skip_none_error_facets
                )
            }
            for error in schema.error_log
        ]

    @staticmethod
    def _get_lxml_error_facet(
        error: etree._LogEntry,
        facet: str,
        document: etree._ElementTree
    ) -> Any:
        """
        Maps requested error facets to lxml error-log attributes.
        """
        if facet == "path":
            return XmlValidationRunner._get_lxml_error_path(error, document)
        if facet == "reason":
            return XmlValidationRunner._get_lxml_error_reason(error, document)
        if facet == "line_number":
            return error.line
        return getattr(error, facet, None)

    @staticmethod
    def _get_lxml_error_path(
        error: etree._LogEntry,
        document: etree._ElementTree
    ) -> str | None:
        """
        Converts lxml's structural XPath into a readable element path.
        """
        if not error.path:
            return None
        try:
            matches = document.xpath(error.path)
        except etree.XPathError:
            return error.path
        if not matches:
            return error.path
        return XmlValidationRunner._build_readable_element_path(matches[0])

    @staticmethod
    def _build_readable_element_path(
        element: etree._Element
    ) -> str:
        """
        Builds a slash-separated path from an lxml element.
        """
        path_parts = [
            etree.QName(ancestor).localname
            for ancestor in element.iterancestors()
        ]
        path_parts.reverse()
        path_parts.append(etree.QName(element).localname)
        return "/" + "/".join(path_parts)

    @staticmethod
    def _get_lxml_error_reason(
        error: etree._LogEntry,
        document: etree._ElementTree
    ) -> str:
        """
        Converts common lxml validation messages to familiar wording.
        """
        message = error.message
        invalid_value_match = re.match(
            r"Element '([^']+)': '([^']+)' is not a valid value of "
            r"the atomic type '([^']+)'\.",
            message
        )
        if invalid_value_match:
            _, value, value_type = invalid_value_match.groups()
            if value_type in {"xs:int", "xs:integer"}:
                return f"invalid literal for int() with base 10: '{value}'"
            if value_type == "xs:decimal":
                return f"invalid value '{value}' for xs:decimal"
            if value_type == "xs:ID":
                return "value doesn't match any pattern of ['[\\\\i-[:]][\\\\c-[:]]*']"

        unexpected_child_match = re.match(
            r"Element '([^']+)': This element is not expected\."
            r"(?: Expected is \( ([^)]+) \)\.)?",
            message
        )
        if unexpected_child_match:
            child_tag, expected_tag = unexpected_child_match.groups()
            position = XmlValidationRunner._get_lxml_error_position(
                error,
                document
            )
            reason = (
                f"Unexpected child with tag '{child_tag}' "
                f"at position {position}."
            )
            if expected_tag:
                reason = f"{reason} Tag '{expected_tag.strip()}' expected."
            return reason

        pattern_match = re.match(
            r"Element '([^']+)': \[facet 'pattern'\] The value '([^']+)' "
            r"is not accepted by the pattern '([^']+)'\.",
            message
        )
        if pattern_match:
            _, _, pattern = pattern_match.groups()
            pattern = pattern.replace("\\", "\\\\")
            return f"value doesn't match any pattern of ['{pattern}']"

        return message

    @staticmethod
    def _get_lxml_error_position(
        error: etree._LogEntry,
        document: etree._ElementTree
    ) -> int:
        """
        Returns the one-based element position among siblings.
        """
        try:
            matches = document.xpath(error.path)
        except etree.XPathError:
            return 1
        if not matches:
            return 1
        element = matches[0]
        parent = element.getparent()
        if parent is None:
            return 1
        return list(parent).index(element) + 1
