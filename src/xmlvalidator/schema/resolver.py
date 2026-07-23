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
Provides XML-to-XSD schema resolution for XmlValidator.

The ValidatorSchemaResolver class determines which schema should be used
for each XML file before validation starts.
"""

# Standard library imports.
from pathlib import Path
from typing import Literal

# Third party library imports.
from lxml import etree
from robot.api import logger

# Local application imports.
from ..namespaces import extract_namespaces, schema_matches_xml_namespaces
from ..paths import get_file_paths
from .manager import ValidatorSchemaManager

ValidationPlan = dict[Path, Path | BaseException | None]


class ValidatorSchemaResolver:
    """
    Resolves XML files to the XSD schemas that should validate them.

    This class handles validation planning only. It does not validate
    XML files itself; it returns a mapping that the main XmlValidator
    workflow can execute later.

    The resolver receives a ValidatorSchemaManager instance through
    constructor-based dependency injection. This is intentional because:

    - ValidatorSchemaResolver does not own schema state itself.
    - XmlValidator and ValidatorSchemaResolver can share the same schema
      manager.
    - Tests can provide a mocked or prepared schema manager.
    - Responsibilities remain separated:
      - ValidatorSchemaManager: load/reuse schemas.
      - ValidatorSchemaResolver: decide which XML maps to which schema.
    """

    def __init__(
        self,
        schema_manager: ValidatorSchemaManager
    ) -> None:
        """
        Initializes a ValidatorSchemaResolver instance.

        Args:

        - schema_manager (ValidatorSchemaManager):
          Schema manager used to load or reuse XSD schemas.
        """
        self.schema_manager = schema_manager

    def build_validation_plan(  # pylint: disable=R0913,R0917
        self,
        xml_paths: list[Path],
        xsd_path: str | Path | None = None,
        xsd_search_strategy: Literal["by_namespace", "by_file_name"] | None = None,
        base_url: str | None = None,
        allow_declared_namespace_match: bool = False
    ) -> ValidationPlan:
        """
        Constructs a mapping between XML files and XSD schemas.

        A mapped value of None means the currently loaded schema should
        be used. A FileNotFoundError value means no matching schema
        could be found for that XML file.

        The validation plan is built according to this decision table:

        +-------------------+-------------------+-----------------------------+
        |     xsd_path      |xsd_search_strategy|           Impact            |
        +===================+===================+=============================+
        | Single XSD file   | None              | Load and reuse that schema. |
        +-------------------+-------------------+-----------------------------+
        | Single XSD file   | by_namespace or   | Strategy ignored: single    |
        |                   | by_file_name      | schema is loaded/reused.    |
        +-------------------+-------------------+-----------------------------+
        | XSD folder        | None              | Match by XML/XSD namespace. |
        +-------------------+-------------------+-----------------------------+
        | XSD folder        | by_namespace      | Match by XML/XSD namespace. |
        +-------------------+-------------------+-----------------------------+
        | XSD folder        | by_file_name      | Match by filename stem.     |
        +-------------------+-------------------+-----------------------------+
        | None              | by_namespace      | Infer XSD folder from XML   |
        |                   |                   | folder; match by namespace. |
        +-------------------+-------------------+-----------------------------+
        | None              | by_file_name      | Infer XSD folder from XML   |
        |                   |                   | folder; match by filename.  |
        +-------------------+-------------------+-----------------------------+
        | None              | None              | Use already-loaded schema;  |
        |                   |                   | fail if none is loaded.     |
        +-------------------+-------------------+-----------------------------+

        All decisions are covered by this method.

        This method expects `xml_paths` to contain at least one XML path.
        """
        # No XSD path: dynamic matching assumes XSD/XML file(s) live in one dir.
        if not xsd_path and xsd_search_strategy:
            xsd_path = xml_paths[0].parent
        # Resolve an explicitly provided or inferred XSD path.
        if xsd_path:
            return self._build_xsd_path_plan(
                xml_paths,
                xsd_path,
                xsd_search_strategy,
                base_url,
                allow_declared_namespace_match
            )
        # No XSD path and no dynamic strategy: use the existing schema.
        self.schema_manager.ensure_schema(None, None)
        return self._build_loaded_schema_plan(xml_paths)

    def _build_xsd_path_plan(  # pylint: disable=R0913,R0917
        self,
        xml_paths: list[Path],
        xsd_path: str | Path,
        xsd_search_strategy: Literal["by_namespace", "by_file_name"] | None,
        base_url: str | None,
        allow_declared_namespace_match: bool
    ) -> ValidationPlan:
        """
        Builds a validation plan from an explicit or inferred XSD path.
        """
        # Resolve the XSD path to one or more concrete schema files.
        xsd_paths, is_single_xsd_file = (
            get_file_paths(xsd_path, "xsd")
        )
        # Single schema: is loaded once and reused for all XMLs.
        if is_single_xsd_file:
            result = self.schema_manager.ensure_schema(
                xsd_paths[0],
                base_url
            )
            # Raise if unable to load schema.
            if not result.success:
                raise SystemError(
                    f"Loading of schema failed: {result.error}."
                )
            # Use the loaded schema for each of the XMLs.
            return self._build_loaded_schema_plan(xml_paths)
        # Multiple schemas: must be matched to XMLs before validation.
        return self.match_xml_files_to_schemas(
            xml_paths,
            xsd_paths,
            xsd_search_strategy if xsd_search_strategy else "by_namespace",
            base_url,
            allow_declared_namespace_match
        )

    @staticmethod
    def _build_loaded_schema_plan(
        xml_paths: list[Path]
    ) -> ValidationPlan:
        """
        Builds a validation plan that reuses the currently loaded schema.
        """
        # None tells the validation step to use the loaded schema for each XML.
        xsd_file_paths: list[Path | None] = [None] * len(xml_paths)
        return dict(
            # Each XML mapped to None: validation step will reuse loaded schema.
            zip(xml_paths, xsd_file_paths, strict=True)
        )

    def match_xml_files_to_schemas(  # pylint: disable=R0913,R0917
        self,
        xml_file_paths: list[Path],
        xsd_file_paths: list[Path],
        search_by: Literal["by_namespace", "by_file_name"] = "by_namespace",
        base_url: str | None = None,
        allow_declared_namespace_match: bool = False
    ) -> ValidationPlan:
        """
        Finds matching XSD schemas for XML files.

        Supported strategies are namespace-based matching and file-name
        based matching.
        """
        logger.info(
            f"Mapping XML files to schemas {search_by.replace('_', ' ')}.",
            also_console=True
        )
        # Build one XML-to-XSD mapping entry per XML file.
        validations = {}
        for xml_file_path in xml_file_paths:
            # Prepare the mapping entry.
            logger.info(f"\tSearching schema for: {xml_file_path.stem}.")
            validations[xml_file_path] = None
            # Delegate to the selected matching strategy.
            if search_by == "by_namespace":
                validations[xml_file_path] = (
                    self._match_xml_file_to_schema_by_namespace(
                        xml_file_path,
                        xsd_file_paths,
                        base_url,
                        allow_declared_namespace_match
                    )
                )
            elif search_by == "by_file_name":
                validations[xml_file_path] = (
                    self._match_xml_file_to_schema_by_file_name(
                        xml_file_path,
                        xsd_file_paths
                    )
                )
            else:
                # Defensive runtime check.
                raise ValueError(f"Unsupported search strategy: {search_by}.")
            # Convert an unsuccessful lookup into an explicit error marker.
            if not validations[xml_file_path]:
                logger.info(f"\t\tNo valid XSD found for {xml_file_path}.")
                validations[xml_file_path] = FileNotFoundError(
                    f"No matching XSD found for: {xml_file_path.stem}."
                )
        return validations

    def _match_xml_file_to_schema_by_namespace(
        self,
        xml_file_path: Path,
        xsd_file_paths: list[Path],
        base_url: str | None,
        allow_declared_namespace_match: bool
    ) -> Path | BaseException | None:
        """
        Matches a single XML file to an XSD file by namespace.
        """
        # Parse the XML and collect the namespaces declared on its root.
        try:
            xml_root = etree.parse( # pylint: disable=I1101:c-extension-no-member
                str(xml_file_path),
                parser=etree.XMLParser() # pylint: disable=I1101:c-extension-no-member
            ).getroot()
            xml_namespaces = extract_namespaces(
                xml_root,
                include_nested=False
            )
        # Return parse/access errors, so downstream reporting can log them.
        except Exception as err: # pylint: disable=W0718:broad-exception-caught
            logger.info("\t\tProcessing XML file failed.")
            return err
        # Test each candidate schema until one matches the XML namespace(s).
        for xsd_file_path in xsd_file_paths:
            logger.info(f"\t\tTesting schema: {xsd_file_path}.")
            # Load the schema.
            result = self.schema_manager.load_schema(
                xsd_file_path,
                base_url=base_url
            )
            if not result.success:
                logger.warn(
                    f"Matching attempt failed due to exception: {result.error}."
                )
                continue
            # Compare XML namespaces with the loaded schema's namespaces.
            match = schema_matches_xml_namespaces(
                result.value, # type: ignore
                xml_namespaces, # type: ignore
                allow_declared_namespace_match
            )
            # Return a matching XSD's file path.
            if match:
                logger.info(f"\t\t\tMatch found with: {xsd_file_path}.")
                return xsd_file_path
        # No match found.
        return None

    @staticmethod
    def _match_xml_file_to_schema_by_file_name(
        xml_file_path: Path,
        xsd_file_paths: list[Path]
    ) -> Path | None:
        """
        Matches a single XML file to an XSD file by filename stem.
        """
        # Test each candidate schema until its stem matches the XML stem.
        for xsd_file_path in xsd_file_paths:
            logger.info(f"\t\t\tTesting file name: {xsd_file_path}.")
            if xsd_file_path.stem == xml_file_path.stem:
                logger.info("\t\tFound match.")
                return xsd_file_path
            logger.info("\t\t\tNo match: trying next schema file.")
            continue
        return None
