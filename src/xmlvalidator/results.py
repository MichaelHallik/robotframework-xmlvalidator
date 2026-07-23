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
Provides result-handling components for XML validation operations.

This module defines:

- ValidatorResultRecorder:
  Collects validation results, including valid/invalid files and
  associated error details. Supports logging, CSV export and filterable
  HTML error tables in the Robot Framework log.
- ValidatorResult:
  A lightweight result wrapper for encapsulating success/failure states
  and their corresponding values or errors.

These classes are used internally by the XmlValidator library and
associated utilities to manage and report validation outcomes.
"""

# Standard library imports.
from datetime import datetime
from pathlib import Path
from typing import Any

# Third party library imports.
import pandas as pd
from robot.api import logger


class ValidatorResultRecorder:
    """
    Collects and manages all results from XML validation runs.

    This class serves as an aggregator for storing validation outcomes,
    including:

    - A summary of valid and invalid XML files.
    - Detailed validation errors per invalid file.

    It supports writing individual errors and summary statistics to the
    Robot Framework log, rendering filterable HTML error tables and
    exporting all errors to a CSV file.

    Attributes:

    - errors_by_file (list[dict[str, Any]]):
      A list of validation error dictionaries, each tagged with its
      corresponding file name.

    - validation_summary (dict[str, list[str]]):
      A dictionary with two keys: 'valid' and 'invalid'. Each key maps
      to a list of file names.

    Notes:

    - This class is used internally by XmlValidator to record,
      summarize and export validation results.
    - This class keeps validation state per library instance and
      provides utility methods for result recording and reporting.
    """

    # Styling plus filtering script for embedding error tables in the log.
    STYLE_AND_FILTER_SCRIPT = """
        <style>
            #table_block_0 {
              margin-bottom: -5em;
            }
            .dataframe th {
                background-color: var(--primary-color);
                padding: 0.2em 0.3em;
            }
            .dataframe th, .dataframe td {
                border-width: 1px;
                border-style: solid;
                border-color: var(--secondary-color);
                padding: 0.1em 0.3em;
                font-family: Helvetica, sans-serif;
            }
            input.filter {
                width: 25em;
                background-color: var(--background-color);
                border-color: var(--secondary-color);
                border-width: 2px;
                border-style: solid;
                border-radius: 2px;
                color: var(--text-color);
                margin-left: 0;
                font-family: Helvetica, sans-serif;
              }
        </style>
        <script>
            function filterTable(blockId) {
                const container = document.getElementById("table_block_" + blockId);
                const input = container.querySelector("input");
                const table = container.querySelector("table");
                const filter = input.value.toLowerCase();
                const trs = table.getElementsByTagName("tr");

                for (let i = 1; i < trs.length; i++) {
                    const tds = trs[i].getElementsByTagName("td");
                    let rowVisible = false;
                    for (let j = 0; j < tds.length; j++) {
                        const td = tds[j];
                        if (td && td.textContent.toLowerCase().indexOf(filter) > -1) {
                            rowVisible = true;
                            break;
                        }
                    }
                    trs[i].style.display = rowVisible ? "" : "none";
                }
            }
        </script>
      """

    def __init__(self) -> None:
        """
        Initializes a ValidatorResultRecorder instance.

        The recorder starts with:

        - an empty error collection
        - empty validation summaries
        - error-table-id counter set to zero
        """
        # Stores all collected errors, grouped by source file.
        self.errors_by_file: list[dict[str, Any]] = []
        # Tracks validated file names by outcome category.
        self.validation_summary: dict[str, list[str]] = {
            "valid": [],
            "invalid": []
        }
        # Tracks error tables so each table receives a unique HTML id.
        self.error_table_id: int = 0

    # Collect validation results.

    def add_valid_file(self, file_path: Path) -> None:
        """
        Records a file as valid and logs the result.

        Adds the file name to the `valid` list within the
        `validation_summary` attribute and emits a confirmation
        to the console and log file.

        Args:

        - file_path (Path):
          The path to the XML file that passed validation.

        Returns:

        None
        """
        self.validation_summary["valid"].append(file_path.name)
        logger.info("\tXML is valid!", also_console=True)

    def add_invalid_file(self, file_path: Path) -> None:
        """
        Records a file as invalid and logs the result.

        Adds the file name to the `invalid` list within the
        `validation_summary` attribute and emits a warning
        to the console and the log file.

        Args:

        - file_path (Path):
          The path to the XML file that failed validation.

        Returns:

        None
        """
        self.validation_summary["invalid"].append(file_path.name)
        logger.warn("\tXML is invalid:")

    def add_file_errors(
        self,
        file_path: Path,
        error_details: list[dict[str, Any]] | dict[str, Any] | None
    ) -> None:
        """
        Adds validation error(s) for a given XML file.

        Accepts either a single error dictionary or a list of error
        dictionaries and appends them to the `errors_by_file` attribute.
        Each error entry is tagged with the file name.

        Args:

        - file_path (Path):
          The path of the XML file that caused the error(s).

        - error_details (dict[str, Any] | list[dict[str, Any]] | None):
          The validation error(s) to record.
          If a single dictionary is provided, it is internally converted
          to a list.
          If None or an empty collection is provided, nothing is added.

        Returns:

        None
        """
        if not error_details:
            # Nothing to record for this file.
            return
        # Normalize error_details to always be a list.
        if isinstance(error_details, dict):
            error_details = [error_details]
        # Append each error to the errors_by_file list.
        for error in error_details:
            error_entry = {"file_name": file_path.name, **error}
            self.errors_by_file.append(error_entry)

    # Write errors to the console and log file.

    def log_file_errors(self, errors: list[dict[str, Any]]) -> None:
        """
        Logs a list of validation errors to the console as well as to
        the log file.

        Each error dictionary is logged under a numbered header (e.g.
        "Error #0") followed by its individual key-value pairs.

        Args:

        - errors (list[dict[str, Any]]):
          A list of dictionaries containing validation error details for
          one or more XML files.

        Returns:

        None
        """
        for idx, error in enumerate(errors):
            logger.warn(f"\t\tError #{idx}:")
            for key, value in error.items():
                logger.warn(f"\t\t\t{key}: {value}")

    def log_summary(self) -> None:
        """
        Logs a summary of validation results to the console as well as
        to the log file.

        This method retrieves the number of valid, invalid and total
        files from `_get_summary()` and logs them in a structured
        format.

        Returns:

        None
        """
        for category, value in self._get_summary().items():
            logger.info(f"{category}: {value}.", also_console=True)

    def _get_summary(self) -> dict[str, int]:
        """
        Constructs a summary of validation outcomes.

        This internal method returns a dictionary containing the count
        of validated, valid and invalid files. It safely handles cases
        where either category is missing from the summary.

        Returns:

        - dict[str, int]:
          {
              "Total_files validated": int,
              "Valid files": int,
              "Invalid files": int
          }
        """
        valid_files = len(self.validation_summary.get("valid", []))
        invalid_files = len(self.validation_summary.get("invalid", []))
        return {
            "Total_files validated": valid_files + invalid_files,
            "Valid files": valid_files,
            "Invalid files": invalid_files,
        }

    # Write extended reports.

    def write_error_table_to_log(self, errors: list[dict[str, Any]]) -> None:
        """
        Writes a table of validation errors to the log file.

        This method takes a list of error dictionaries and renders them
        as a filterable HTML table in the Robot Framework log.

        Args:

        - errors (list[dict[str, Any]]):
          A list of dictionaries, where each dictionary contains details
          of a validation error. Each key in the dictionaries
          corresponds to a column in the generated HTML table.

        Notes:

        - If `errors` is an empty list, the method exits early and logs
          an informational message without writing a table to the log.
        - The method uses `pandas` for HTML table generation.
        """
        # Return if no errors were passed.
        if not errors:
            logger.info("No errors to write to log file.")
            return
        # Convert the errors list to a DataFrame.
        df = pd.DataFrame(errors)
        # Convert the DataFrame to HTML.
        html_table = df.to_html(index=False, border=0)
        # Get the table id and increment for the next one.
        error_table_id = self.error_table_id
        self.error_table_id += 1
        # Add filter input to the HTML table (includes the function call).
        full_html = f"""<div id="table_block_{error_table_id}">
            <input class="filter" type="text"
                   onkeyup="filterTable('{error_table_id}')"
                   placeholder="Search validation errors...">
            {html_table}
        </div>"""
        # Add the style and filter script if it is the first table.
        if error_table_id == 0:
            full_html = f"{full_html}{self.STYLE_AND_FILTER_SCRIPT}"
        # Write the filterable table to the log file.
        logger.info(full_html, html=True)

    def write_errors_to_csv(self,
        errors: list[dict[str, Any]],
        output_path: Path,
        include_timestamp: bool | None = False,
        file_name_column: str | None = None
    ) -> str:
        """
        Writes a list of validation errors to a CSV file.

        This method takes a list of error dictionaries and writes them
        to a CSV file at the specified output path. Optionally, it
        appends a timestamp to the file name and reorders columns to
        place a specific column (e.g., "file_name") first.

        Args:

        - errors (list[dict[str, Any]]):
          A list of dictionaries, where each dictionary contains details
          of a validation error. Each key in the dictionaries
          corresponds to a column in the output CSV.

        - output_path (Path):
          The base path for the output CSV file. A timestamp will be
          appended to the filename if `include_timestamp` is True.

        - include_timestamp (bool, optional):
          If True, appends a timestamp (in the format
          `YYYY-MM-DD_HH-MM-SS-ffffff`) to the output file name.
          Defaults to False.

        - file_name_column (str, optional):
          The name of the column to be placed first in the CSV. If the
          specified column is not present, the original column order is
          preserved.

        Raises:

        - OSError:
          Raised if writing the CSV fails due to file system issues.

        Returns:

        - str:
          The resolved path of the created CSV file.

        Notes:

        - If `errors` is an empty list, the method exits early and logs
          an informational message without creating a file.
        - Column reordering occurs only if `file_name_column` exists in
          the error dictionaries.
        - If different error dictionaries contain different keys,
          pandas creates columns for the union of those keys. Missing
          values are written as empty CSV cells. Explicit values such as
          "Unavailable" are preserved.
        - The method uses `pandas` for CSV generation.
        """
        # Nothing to export.
        if not errors:
            logger.info("No errors to write to CSV.")
            return ''
        # Generate a timestamp to be added to the filename.
        timestamp = (
            f'_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")}'
            if include_timestamp
            else ""
        )
        # Construct the output path.
        output_csv_path = output_path.parent / f"errors{timestamp}.csv"
        # Convert the errors list to a DataFrame.
        df = pd.DataFrame(errors)
        # Ensure the specified column is first, if provided.
        if file_name_column and file_name_column in df.columns:
            columns_order = [file_name_column] + [
                col for col in df.columns if col != file_name_column
                ]
            df = df[columns_order]
        # Write the DataFrame to a CSV file.
        try:
            df.to_csv(output_csv_path, index=False)
            logger.info(
                f"Validation errors exported to: \n\t'{output_csv_path}'.",
                also_console=True
                )
        except OSError as e:
            raise OSError(
                f"Failed to write CSV file: {output_csv_path}."
                ) from e
        return str(output_csv_path.resolve())

    # Clear all results.

    def reset(self) -> None:
        """
        Clears all stored validation results.

        This method resets the internal state of the result recorder,
        including:

        - `errors_by_file`: list emptied.
        - `validation_summary`: dict reset to default structure with
          empty 'valid' and 'invalid' lists
        - `error_table_id`: counter reset to zero.
        """
        self.errors_by_file.clear()
        self.validation_summary = {"valid": [], "invalid": []}
        self.error_table_id = 0


class ValidatorResult: # pylint: disable=R0903:too-few-public-methods
    """
    Encapsulates the result of an operation in a success-or-failure
    format.

    `ValidatorResult` provides a structured way to handle the outcome of
    operations throughout the XML validation library. It captures
    whether an operation succeeded and typically includes either the
    result (`value`) or the error (`error`).

    This pattern allows methods to return a single object regardless of
    success or failure, simplifying error handling.

    `ValidatorResult` is intentionally different from
    `ValidatorResultRecorder`: one class records/reports validation
    outcomes, the other represents an individual operation result.

    `ValidatorResult` represents the result of one operation: for
    example, whether a file lookup, schema match or validation
    preparation step succeeded and what value or error was produced. It
    is therefore useful for passing a local result from one method to
    another without immediately logging or storing it.

    `ValidatorResultRecorder`, by contrast, stores and reports the
    *accumulated* outcome of a validation run. It keeps track of valid
    and invalid files, collects validation errors, writes summaries and
    can export those errors to the Robot Framework log or to CSV.

    In a typical workflow, `ValidatorResult` can be used for individual
    decisions or helper-method results, while `ValidatorResultRecorder`
    collects the final validation evidence that should be shown to the
    user. Together, they separate short-lived operation results from the
    longer-lived reporting state of the library.

    Attributes:

    - success (bool):
        True if the operation was successful; False otherwise.

    - value (Any, optional):
        The returned data from a successful operation.

    - error (Any, optional):
        Error information if the operation failed.
    """

    def __init__(
        self,
        success: bool,
        value: Any | None = None,
        error: Any | None = None
    ):
        """
        Initializes a ValidatorResult instance.

        Used to encapsulate the outcome of an operation, including
        success state, result value or error information.

        Args:

        - success (bool):
          Whether the operation was successful.
        - value (Any, optional):
          The result of the operation, if successful. Defaults to None.
        - error (Any, optional):
          Error details if the operation failed. Defaults to None.

        Returns:

        None
        """
        self.success = success
        self.value = value
        self.error = error

    def __repr__(self) -> str:
        """
        Returns a string representation of the ValidatorResult instance.

        If the result is successful, includes the value.

        Otherwise, includes the error details.

        Returns:

        str
        """
        if self.success:
            return f"Result(success=True, value={self.value})"
        return f"Result(success=False, error={self.error})"
