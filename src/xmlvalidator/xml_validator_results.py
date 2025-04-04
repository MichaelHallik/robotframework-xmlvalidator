# Copyright 2024-2025 Michael Hallik
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
  Encapsulates validation results, including valid/invalid files and 
  associated error details. Supports logging and also exporting to CSV.
- ValidatorResult:
  A lightweight result wrapper for encapsulating success/failure states 
  and their corresponding values or errors.

These classes are used internally by the XmlValidator library and 
associated utilities to manage and report outcomes of validation 
tasks.
"""


# Standard library imports.
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
# Third party library imports.
import pandas as pd
from robot.api import logger


# This class is structured as a dataclass for default field setup, but
# (also) provides utility methods for result recording and reporting.
@dataclass
class ValidatorResultRecorder:
    """
    Collects and manages results from XML validation runs.

    This class serves as an internal aggregator for storing validation 
    outcomes, including:

    - A summary of valid and invalid XML files.
    - Detailed validation errors grouped by file.

    It supports logging of individual errors and summary statistics to 
    the Robot Framework log, as well as exporting all errors to a 
    CSV file.

    Attributes:

    - errors_by_file (List[Dict[str, Any]]):
      A list of validation error dictionaries, each tagged with its 
      corresponding file name.

    - validation_summary (Dict[str, List[str]]):
      A dictionary with two keys: 'valid' and 'invalid'. Each key maps 
      to a list of file names.

    This class is used internally by XmlValidator to record, summarize, 
    and export validation results.
    """

    __version__ = '1.0.0'

    errors_by_file: List[Dict[str, Any]] = field(default_factory=list)
    validation_summary: Dict[str, List[str]] = field(
        default_factory=lambda: {"valid": [], "invalid": []}
        )

    def _get_summary(self) -> Dict[str, int]:
        """
        Constructs a summary of validation outcomes.

        This internal method returns a dictionary containing the count 
        of validated, valid, and invalid files. It safely handles cases 
        where either category is missing from the summary.

        Returns:

        - Dict[str, int]:
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

    def add_file_errors(
        self,
        file_path: Path,
        error_details: List[Dict[str, Any]] | Dict[str, Any] | None
        ) -> None:
        """
        Adds validation error(s) for a given XML file.

        Accepts either a single error dictionary or a list of error 
        dictionaries and appends them to the `errors_by_file` attribute. 
        Each error entry is tagged with the file name.

        Args:

        - file_path (Path):
          The path of the XML file that caused the error(s).

        - error_details (Dict or List[Dict] or None):
          The validation error(s) to record. If a single dictionary is 
          provided, it is internally converted to a list.

        Returns:

        None
        """
        if error_details:
            # Normalize error_details to always be a list.
            if isinstance(error_details, dict):
                error_details = [error_details]
            # Append each error to the errors_by_file list.
            for error in error_details:
                error_entry = {"file_name": file_path.name, **error}
                self.errors_by_file.append(error_entry)

    def add_invalid_file(
            self,
            file_path: Path
            ) -> None:
        """
        Records a file as invalid and logs the result.

        Adds the file name to the `invalid` list within the 
        `validation_summary` attribute and emits a warning log 
        to Robot Framework output.

        Args:

        - file_path (Path):
          The path to the XML file that failed validation.

        Returns:

        None
        """
        logger.warn("\tXML is invalid:")
        self.validation_summary["invalid"].append(file_path.name)

    def add_valid_file(
            self,
            file_path: Path
            ) -> None:
        """
        Records a file as valid and logs the result.

        Adds the file name to the `valid` list within the 
        `validation_summary` attribute and emits a confirmation 
        log to the Robot Framework output.

        Args:

        - file_path (Path):
          The path to the XML file that passed validation.

        Returns:
        
        None
        """
        logger.info("\tXML is valid!", also_console=True)
        self.validation_summary["valid"].append(file_path.name)

    def log_file_errors(
            self,
            errors: List[Dict[str, Any]]
            ) -> None:
        """
        Logs a list of validation errors to the Robot Framework log.

        Each error dictionary is logged under a numbered header 
        (e.g., "Error #1") followed by its individual key-value 
        pairs.

        Args:

        - errors (List[Dict[str, Any]]):
          A list of dictionaries containing validation error details for 
          one or more XML files.

        Returns:
        
        None
        """
        for idx, error in enumerate(errors):
            logger.warn(f'\t\tError #{idx}:')
            for key, value in error.items():
                logger.warn(f"\t\t\t{key}: {value}")

    def log_summary(self) -> None:
        """
        Logs a summary of validation results to the Robot Framework log.

        This method retrieves the number of valid, invalid, and total 
        files from `_get_summary()` and prints them in a structured 
        format.

        Returns:

        None
        """
        for category, value in self._get_summary().items():
            logger.info(f"{category}: {value}.", also_console=True)

    def reset(self) -> None:
        """
        Clears all stored validation results.

        This method resets the internal state of the result recorder, 
        including:

        - `errors_by_file`:
           cleared
        - `validation_summary`:
           reset to default structure with empty 'valid' and 'invalid' 
           lists

        Call this method before starting a new validation run if you 
        want to discard previous results.

        Returns:

        None
        """
        self.errors_by_file.clear()
        self.validation_summary = {"valid": [], "invalid": []}

    def write_errors_to_csv(self,
                            errors: List[ Dict[str, Any] ],
                            output_path: Path,
                            include_timestamp: Optional[bool] = False,
                            file_name_column: Optional[str] = None
                            ) -> str:
        """
        Writes a list of validation errors to a CSV file.

        This method takes a list of error dictionaries and writes them 
        to a CSV file at the specified output path. Optionally, it 
        appends a timestamp to the file name and reorders columns to 
        place a specific column (e.g., "file_name") first.

        Args:

        - errors (List[Dict[str, Any]]):
          A list of dictionaries, where each dictionary contains details 
          of a validation error. Each key in the dictionaries 
          corresponds to a column in the output CSV.

        - output_path (Path):
          The base path for the output CSV file. A timestamp will be 
          appended to the filename if `include_timestamp` is True.

        - include_timestamp (bool, optional):
          If True, appends a timestamp (in the format 
          `YYYY-MM-DD_HH-MM-SS`) to the output file name. Defaults to 
          False.

        - file_name_column (str, optional):
          The name of the column to be placed first in the CSV. If the 
          specified column is not present, the original column order is 
          preserved.

        Raises:

        - ValueError:
          Raised if the `errors` list is empty or improperly formatted.

        - IOError:
          Raised if writing the CSV fails due to file system issues.

        Returns:

        - str:
          The resolved path of the created CSV file.

        Notes:

        - If `errors` is an empty list, the method exits early and logs 
          an informational message without creating a file.
        - Column reordering occurs only if `file_name_column` exists in 
          the error dictionaries.
        - The method uses `pandas` for CSV generation.
        """
        # Return if no errors were passed.
        if not errors:
            logger.info("No errors to write to CSV.")
            return ''
        # Generate a timestamp to be added to the filename.
        timestamp = f'_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")}' \
            if include_timestamp else None
        # Construct the output path.
        output_csv_path = (
            output_path.parent / f"errors{timestamp if timestamp else ''}.csv"
            )
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
                f"Validation errors exported to '{output_csv_path}'.",
                also_console=True
                )
        except IOError as e:
            raise IOError(
                f"Failed to write CSV file: {output_csv_path}."
                ) from e
        return str( output_csv_path.resolve() )

class ValidatorResult: # pylint: disable=R0903:too-few-public-methods
    """
    Encapsulates the result of an operation in a success-or-failure format.

    `ValidatorResult` provides a structured way to handle the outcome of 
    operations throughout the XML validation library. It captures whether 
    an operation succeeded and includes either the result (`value`) or 
    the error (`error`) — but not both.

    This pattern allows methods to return a single object regardless of 
    success or failure, simplifying error handling.

    Attributes:

    - success (bool):
        True if the operation was successful; False otherwise.

    - value (Any, optional):
        The returned data from a successful operation.

    - error (Any, optional):
        Error information if the operation failed.
    """

    __version__ = '0.0.1'

    def __init__(
            self,
            success: bool,
            value: Optional[Any] = None,
            error: Optional[Any] = None
            ) -> None:
        """
        Initializes a ValidatorResult instance.

        Used to encapsulate the outcome of an operation, including 
        success state, result value, or error information.

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
        if self.success: # pylint: disable=R1705:no-else-return
            return f"Result(success=True, value={self.value})"
        else:
            return f"Result(success=False, error={self.error})"
