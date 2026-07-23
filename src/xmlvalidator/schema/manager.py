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
Provides schema-loading and schema-state management for XmlValidator.

The ValidatorSchemaManager class owns the currently loaded XMLSchema
object and centralizes the logic for loading, replacing and reusing XSD
schemas.
"""

# Standard library imports.
from pathlib import Path

# Third party library imports.
from robot.api import logger
from xmlschema import XMLSchema

# Local application imports.
from ..paths import get_file_paths
from ..results import ValidatorResult


class ValidatorSchemaManager:
    """
    Loads and stores the XSD schema used by validation workflows.

    This class separates schema-state management from the Robot
    Framework keyword facade. It is responsible for resolving initial
    schema paths, loading XMLSchema objects and deciding whether an
    existing schema can be reused.
    """

    def __init__(self) -> None:
        """
        Initializes a ValidatorSchemaManager instance.
        """
        self.schema: XMLSchema | None = None

    def ensure_schema(
        self,
        xsd_path: Path | None = None,
        base_url: str | None = None
    ) -> ValidatorResult:
        """
        Ensures that a schema is available for validation.

        If no `xsd_path` is given but a schema is already loaded, the
        existing schema is reused. If a new path is passed, that schema
        is loaded and replaces the current one.
        """
        if not (self.schema or xsd_path):
            raise ValueError(
                "No schema: provide an XSD path during keyword call(s)."
            )
        if self.schema and not xsd_path:
            return ValidatorResult(success=True, value=self.schema)
        if not self.schema and xsd_path:
            logger.info(f"Setting schema file: {xsd_path}.", also_console=True)
        if self.schema and xsd_path:
            logger.info(
                f"\tUsing schema: {xsd_path}.",
                also_console=True
            )
        if xsd_path is None:
            raise ValueError(
                "No schema: provide an XSD path during keyword call(s)."
            )
        return self.load_schema(xsd_path, base_url)

    def load_schema(
        self,
        xsd_path: Path,
        base_url: str | None = None
    ) -> ValidatorResult:
        """
        Loads an XSD schema from disk and stores it as the active
        schema.

        Schema loading errors are captured and returned in a
        ValidatorResult instead of being raised directly.
        """
        try:
            self.schema = XMLSchema(xsd_path, base_url=base_url)
            return ValidatorResult(success=True, value=self.schema)
        except Exception as e: # pylint: disable=W0718:broad-exception-caught
            return ValidatorResult(
                success=False,
                error={type(e).__name__: e}
            )

    def try_load_initial_schema(
        self,
        xsd_path: str | Path | None = None,
        base_url: str | None = None
    ) -> XMLSchema | None:
        """
        Attempts to load a single initial schema during library import.

        If `xsd_path` is not provided, no schema is loaded and None is
        returned. If a path is provided, it must resolve to exactly one
        XSD file.
        """
        if xsd_path:
            xsd_file_path, is_single_xsd_file = (
                get_file_paths(xsd_path, "xsd")
            )
            if not is_single_xsd_file:
                raise ValueError(
                    f"Got multiple xsd files: {xsd_file_path}."
                )
            if xsd_file_path[0].suffix != ".xsd":
                raise SystemError(
                    f"ValueError: {xsd_file_path[0]} is not an XSD file."
                )
            result = self.load_schema(xsd_file_path[0], base_url)
            if result.success:
                logger.info(
                    f"Schema '{self.schema.name}' set.", # type: ignore
                    also_console=True
                )
                return result.value
            raise SystemError(
                f"Loading of schema failed: {result.error}"
            )
        logger.info(
            "No XSD schema set: provide schema(s) during keyword calls.",
            also_console=True
        )
        return None
