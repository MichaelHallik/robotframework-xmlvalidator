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
Provides file-level sanity checks for XML and XSD validation workflows.
"""

# pylint: disable=I1101:c-extension-no-member

# Standard library imports.
from pathlib import Path

# Third party library imports.
from lxml import etree

# Local application imports.
from .results import ValidatorResult

DEFAULT_ERROR_FACETS: dict[type, list[str]] = {
    OSError: ["strerror"],
    etree.ParseError: ["msg", "position"],
    etree.XMLSchemaParseError: ["msg", "position"],
    etree.XMLSyntaxError: ["msg", "position"]
}


def sanity_check_files( # pylint: disable=R0914:too-many-locals
    file_paths: list[Path],
    base_url: str | None = None,
    error_facets: list[str] | None = None,
    parse_files: bool = False,
    skip_none_error_facets: bool = False
) -> ValidatorResult:
    """
    Performs file-level sanity checks on XML or XSD files.

    The function verifies that each path points to a supported,
    existing, non-empty XML or XSD file. If ``parse_files`` is True, it
    also parses XML files and parses/compiles XSD files before the main
    validation step starts.

    Parsing errors are converted into structured error dictionaries.
    By default, requested error facets whose value is ``None`` are kept
    and reported as ``Unavailable``. If ``skip_none_error_facets`` is
    True, such facets are omitted instead.
    """
    errors: list[dict[str, str | None]] = []
    for file_path in file_paths:
        file_type = file_path.suffix.lower()
        file_error = _check_file_path(file_path, file_type)
        if file_error:
            errors.append(file_error)
            continue
        try:
            _parse_file_for_sanity_check(
                file_path,
                file_type,
                base_url,
                parse_files
            )
        except (
            OSError,
            etree.ParseError,
            etree.XMLSchemaParseError,
            etree.XMLSyntaxError
        ) as e:
            error_details = _extract_error_details(
                e,
                error_facets,
                DEFAULT_ERROR_FACETS,
                skip_none_error_facets
            )
            _append_file_error(
                errors,
                file_path,
                "File parsing failed.",
                error_details
            )
    success = len(errors) == 0
    return ValidatorResult(success=success, error=errors)


def _check_file_path(
    file_path: Path,
    file_type: str
) -> dict[str, str | None] | None:
    """
    Checks whether a file path can be processed by sanity checks.
    """
    if file_type not in {".xml", ".xsd"}:
        return {
            "file": str(file_path),
            "reason": f"Unsupported file type: {file_type}.",
            "Error type": "ValueError"
        }
    if not file_path.exists():
        return {
            "file": str(file_path),
            "reason": (
                f"The {file_type.removeprefix('.')} file does not exist."
            ),
            "Error type": "OSError"
        }
    if file_path.stat().st_size == 0:
        return {
            "file": str(file_path),
            "reason": "File is empty.",
            "Error type": "ValueError"
        }
    return None


def _parse_file_for_sanity_check(
    file_path: Path,
    file_type: str,
    base_url: str | None,
    parse_files: bool
) -> None:
    """
    Parses a file when sanity checks include XML/XSD parsing.
    """
    if not parse_files:
        return
    with file_path.open("rb") as file:
        tree = etree.parse(
            file,
            parser=etree.XMLParser(),
            base_url=base_url # type:ignore
        )
        if file_type == ".xsd":
            _ = etree.XMLSchema(tree)


def _extract_error_details(
    error: Exception,
    error_facets: list[str] | None,
    default_facets: dict[type, list[str]],
    skip_none_error_facets: bool = False
) -> dict[str, str | None]:
    """
    Extracts selected details from an exception into a dictionary.

    ``error_facets`` controls which exception attributes are copied. If
    no explicit facets are passed, the function falls back to the
    default facets configured for the exception type.

    If a requested facet exists but has value ``None``, the default
    behavior is to record the value as ``Unavailable``. This keeps error
    dictionaries, logs and CSV output predictable. Passing
    ``skip_none_error_facets=True`` omits such unavailable facets.
    """
    facets_to_include = error_facets or default_facets.get(
        type(error),
        []
    )
    error_details: dict[str, str | None] = {}
    for facet in facets_to_include:
        if hasattr(error, facet):
            value = getattr(error, facet, None)
            if value is None and skip_none_error_facets:
                continue
            if value is None:
                value = "Unavailable"
            if isinstance(value, tuple):
                value = f"Line {value[0]}, Column {value[1]}."
            error_details[facet] = value
    error_details["Error type"] = type(error).__name__
    return error_details


def _append_file_error(
    errors: list[dict[str, str | None]],
    file_path: Path,
    reason: str,
    additional_details: dict[str, str | None] | None = None
) -> None:
    """
    Appends a structured file validation error to the error list.
    """
    error: dict[str, str | None] = {
        "file": str(file_path),
        "reason": reason
    }
    if additional_details:
        error.update(additional_details)
    errors.append(error)
