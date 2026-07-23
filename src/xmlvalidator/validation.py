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
Provides single-file XML validation execution.

The XmlValidationRunner class validates one XML file against either an
already-loaded schema or a schema loaded specifically for that file.
"""

# Standard library imports.
from pathlib import Path
from typing import Any

# Third party library imports.
from robot.api import logger

# Local application imports.
from .files import sanity_check_files
from .schema.manager import ValidatorSchemaManager


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
        skip_none_error_facets: bool = False
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
        # Validate the XML and collect details for each XSD violation.
        errors = self._collect_validation_errors(
            xml_file_path,
            loading_result.value,
            error_facets,
            default_error_facets,
            skip_none_error_facets
        )
        # Determine validity based on the presence of errors.
        return (True, None) if len(errors) == 0 else (False, errors)

    @staticmethod
    def _collect_validation_errors(
        xml_file_path: Path,
        schema: Any,
        error_facets: list[str] | None = None,
        default_error_facets: list[str] | None = None,
        skip_none_error_facets: bool = False
        ) -> list[dict[str, Any]]:
        """
        Collects configured error details for each XSD validation error.

        Under the hood, the loaded ``xmlschema`` schema object validates
        the XML file through its ``iter_errors()`` method. That method
        does not immediately raise on the first XSD violation. Instead,
        it walks through the XML document and yields one validation
        error object for each encountered violation.

        Each yielded error object contains several attributes, such as
        ``path``, ``reason``, ``message`` or ``validator``. In this
        library, those attributes are called *error facets*. The caller
        can choose which facets should be copied into the returned error
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
        return [
            {
                # Collect the details/facets for each XSD violation.
                facet: (
                    getattr(err, facet, None)
                    if getattr(err, facet, None) is not None
                    else "Unavailable"
                )
                # Error facets to collect determined by arg or instance.
                for facet in (error_facets or default_error_facets or [])
                if (
                    not skip_none_error_facets
                    or getattr(err, facet, None) is not None
                )
            }
            # Generate an err obj (with err details) per encountered violation.
            for err in schema.iter_errors(xml_file_path)
        ]
