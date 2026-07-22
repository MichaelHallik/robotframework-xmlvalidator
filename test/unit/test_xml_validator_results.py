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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Contains the unit tests for the ValidatorResultRecorder and
ValidatorResult classes in the
src/xmlvalidator/xml_validator_results.py module.

See for an overview of all tests the file test/overview_of_tests.html.
"""

# Standard library imports.
import csv
from pathlib import Path

# Local application imports.
from xmlvalidator import xml_validator_results as results_module
from xmlvalidator.xml_validator_results import (
    ValidatorResult,
    ValidatorResultRecorder
)


# ValidatorResultRecorder.__init__()

def test_validator_result_recorder_initializes_empty_state():
    """
    Test that ValidatorResultRecorder starts with empty result state.

    Priority: H
    """
    # Create a fresh result recorder.
    recorder = ValidatorResultRecorder()
    # Expected outcome: all mutable recorder state starts empty/reset.
    assert recorder.errors_by_file == []
    assert recorder.validation_summary == {"valid": [], "invalid": []}
    assert recorder.error_table_id == 0


# add_valid_file()

def test_add_valid_file_records_file_and_logs(monkeypatch):
    """
    Test that add_valid_file() records the file as valid and logs it.

    Priority: H
    """
    # Collect log messages produced by the method under test.
    log_messages = []
    monkeypatch.setattr(
        results_module.logger,
        "info",
        lambda message, **_: log_messages.append(message)
    )
    recorder = ValidatorResultRecorder()
    # Call the method under test.
    recorder.add_valid_file(Path("valid.xml"))
    # Expected outcome: the file is stored under the valid category.
    assert recorder.validation_summary["valid"] == ["valid.xml"]
    assert recorder.validation_summary["invalid"] == []
    assert log_messages == ["\tXML is valid!"]


# add_invalid_file()

def test_add_invalid_file_records_file_and_logs(monkeypatch):
    """
    Test that add_invalid_file() records the file as invalid and logs it.

    Priority: H
    """
    # Collect warning messages produced by the method under test.
    warning_messages = []
    monkeypatch.setattr(
        results_module.logger,
        "warn",
        lambda message, **_: warning_messages.append(message)
    )
    recorder = ValidatorResultRecorder()
    # Call the method under test.
    recorder.add_invalid_file(Path("invalid.xml"))
    # Expected outcome: the file is stored under the invalid category.
    assert recorder.validation_summary["valid"] == []
    assert recorder.validation_summary["invalid"] == ["invalid.xml"]
    assert warning_messages == ["\tXML is invalid:"]


# add_file_errors()

def test_add_file_errors_ignores_none_and_empty_collections():
    """
    Test that add_file_errors() records nothing for empty inputs.

    Priority: H
    """
    recorder = ValidatorResultRecorder()
    # Call the method under test with values that should not be recorded.
    recorder.add_file_errors(Path("invalid.xml"), None)
    recorder.add_file_errors(Path("invalid.xml"), [])
    recorder.add_file_errors(Path("invalid.xml"), {})
    # Expected outcome: no error entries are created.
    assert recorder.errors_by_file == []


def test_add_file_errors_records_single_error_dictionary():
    """
    Test that add_file_errors() records a single error dictionary.

    Priority: H
    """
    recorder = ValidatorResultRecorder()
    error_details = {"reason": "Element is missing."}
    # Call the method under test.
    recorder.add_file_errors(Path("invalid.xml"), error_details)
    # Expected outcome: the error is tagged with the source file name.
    assert recorder.errors_by_file == [
        {
            "file_name": "invalid.xml",
            "reason": "Element is missing."
        }
    ]


def test_add_file_errors_records_list_of_error_dictionaries():
    """
    Test that add_file_errors() records multiple error dictionaries.

    Priority: H
    """
    recorder = ValidatorResultRecorder()
    error_details = [
        {"reason": "Element is missing."},
        {"path": "/root/child"}
    ]
    # Call the method under test.
    recorder.add_file_errors(Path("invalid.xml"), error_details)
    # Expected outcome: each error is tagged with the source file name.
    assert recorder.errors_by_file == [
        {
            "file_name": "invalid.xml",
            "reason": "Element is missing."
        },
        {
            "file_name": "invalid.xml",
            "path": "/root/child"
        }
    ]


# log_file_errors()

def test_log_file_errors_logs_all_error_fields(monkeypatch):
    """
    Test that log_file_errors() logs each error and its fields.

    Priority: M
    """
    # Collect warning messages produced by the method under test.
    warning_messages = []
    monkeypatch.setattr(
        results_module.logger,
        "warn",
        lambda message, **_: warning_messages.append(message)
    )
    recorder = ValidatorResultRecorder()
    errors = [
        {"reason": "Missing element.", "path": "/root"},
        {"reason": "Wrong type."}
    ]
    # Call the method under test.
    recorder.log_file_errors(errors)
    # Expected outcome: each error is logged with a numbered header.
    assert warning_messages == [
        "\t\tError #0:",
        "\t\t\treason: Missing element.",
        "\t\t\tpath: /root",
        "\t\tError #1:",
        "\t\t\treason: Wrong type."
    ]


# log_summary()

def test_log_summary_logs_summary_counts(monkeypatch):
    """
    Test that log_summary() logs validation summary counts.

    Priority: M
    """
    # Collect log messages produced by the method under test.
    log_messages = []
    monkeypatch.setattr(
        results_module.logger,
        "info",
        lambda message, **_: log_messages.append(message)
    )
    recorder = ValidatorResultRecorder()
    recorder.validation_summary = {
        "valid": ["valid_1.xml", "valid_2.xml"],
        "invalid": ["invalid.xml"]
    }
    # Call the method under test.
    recorder.log_summary()
    # Expected outcome: the computed summary is logged in order.
    assert log_messages == [
        "Total_files validated: 3.",
        "Valid files: 2.",
        "Invalid files: 1."
    ]


# _get_summary()

def test_get_summary_returns_validation_counts():
    """
    Test that _get_summary() returns total, valid and invalid counts.

    Priority: H
    """
    recorder = ValidatorResultRecorder()
    recorder.validation_summary = {
        "valid": ["valid_1.xml", "valid_2.xml"],
        "invalid": ["invalid.xml"]
    }
    # Call the method under test.
    summary = recorder._get_summary()
    # Expected outcome: the summary contains all relevant counts.
    assert summary == {
        "Total_files validated": 3,
        "Valid files": 2,
        "Invalid files": 1
    }


def test_get_summary_handles_missing_categories():
    """
    Test that _get_summary() safely handles missing summary categories.

    Priority: M
    """
    recorder = ValidatorResultRecorder()
    recorder.validation_summary = {"valid": ["valid.xml"]}
    # Call the method under test.
    summary = recorder._get_summary()
    # Expected outcome: missing categories are counted as zero.
    assert summary == {
        "Total_files validated": 1,
        "Valid files": 1,
        "Invalid files": 0
    }


# write_error_table_to_log()

def test_write_error_table_to_log_ignores_empty_errors(monkeypatch):
    """
    Test that write_error_table_to_log() does not write a table for no errors.

    Priority: M
    """
    # Collect log messages produced by the method under test.
    log_messages = []
    monkeypatch.setattr(
        results_module.logger,
        "info",
        lambda message, **_: log_messages.append(message)
    )
    recorder = ValidatorResultRecorder()
    # Call the method under test with no errors.
    recorder.write_error_table_to_log([])
    # Expected outcome: no table is written and the id counter is unchanged.
    assert recorder.error_table_id == 0
    assert log_messages == ["No errors to write to log file."]


def test_write_error_table_to_log_writes_filterable_html_table(monkeypatch):
    """
    Test that write_error_table_to_log() logs a filterable HTML table.

    Priority: H
    """
    # Collect log messages produced by the method under test.
    log_entries = []
    monkeypatch.setattr(
        results_module.logger,
        "info",
        lambda message, **kwargs: log_entries.append((message, kwargs))
    )
    recorder = ValidatorResultRecorder()
    errors = [{"file_name": "invalid.xml", "reason": "Missing element."}]
    # Call the method under test.
    recorder.write_error_table_to_log(errors)
    # Expected outcome: a filterable HTML table is logged.
    html_message, log_options = log_entries[0]
    assert recorder.error_table_id == 1
    assert log_options == {"html": True}
    assert 'id="table_block_0"' in html_message
    assert "filterTable('0')" in html_message
    assert "Missing element." in html_message
    assert recorder.STYLE_AND_FILTER_SCRIPT in html_message


def test_write_error_table_to_log_adds_style_only_for_first_table(monkeypatch):
    """
    Test that write_error_table_to_log() adds CSS/JS only to the first table.

    Priority: M
    """
    # Collect HTML messages produced by the method under test.
    html_messages = []
    monkeypatch.setattr(
        results_module.logger,
        "info",
        lambda message, **_: html_messages.append(message)
    )
    recorder = ValidatorResultRecorder()
    errors = [{"file_name": "invalid.xml", "reason": "Missing element."}]
    # Call the method under test twice.
    recorder.write_error_table_to_log(errors)
    recorder.write_error_table_to_log(errors)
    # Expected outcome: the style/script block is only logged once.
    assert recorder.error_table_id == 2
    assert recorder.STYLE_AND_FILTER_SCRIPT in html_messages[0]
    assert recorder.STYLE_AND_FILTER_SCRIPT not in html_messages[1]


# write_errors_to_csv()

def test_write_errors_to_csv_ignores_empty_errors(monkeypatch):
    """
    Test that write_errors_to_csv() creates no file for empty errors.

    Priority: M
    """
    # Collect log messages produced by the method under test.
    log_messages = []
    monkeypatch.setattr(
        results_module.logger,
        "info",
        lambda message, **_: log_messages.append(message)
    )
    recorder = ValidatorResultRecorder()
    output_dir = Path("results/unit-test-output")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv_path = output_dir / "errors.csv"
    output_csv_path.unlink(missing_ok=True)
    # Call the method under test with no errors.
    result = recorder.write_errors_to_csv([], output_dir / "input.xml")
    # Expected outcome: no CSV file is created.
    assert result == ''
    assert not output_csv_path.exists()
    assert log_messages == ["No errors to write to CSV."]


def test_write_errors_to_csv_writes_file_and_moves_file_name_first(
        monkeypatch
        ):
    """
    Test that write_errors_to_csv() writes CSV data and reorders columns.

    Priority: H
    """
    # Suppress logger output during the unit test.
    monkeypatch.setattr(results_module.logger, "info", lambda *_, **__: None)
    recorder = ValidatorResultRecorder()
    output_dir = Path("results/unit-test-output")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv_path = output_dir / "errors.csv"
    output_csv_path.unlink(missing_ok=True)
    errors = [
        {
            "reason": "Missing element.",
            "file_name": "invalid.xml",
            "path": "/root"
        }
    ]
    # Call the method under test.
    csv_path = recorder.write_errors_to_csv(
        errors,
        output_dir / "input.xml",
        file_name_column="file_name"
    )
    # Read the generated CSV file for verification.
    with Path(csv_path).open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))
        fieldnames = rows[0].keys()
    # Expected outcome: the CSV exists and file_name is the first column.
    assert Path(csv_path).resolve() == output_csv_path.resolve()
    assert list(fieldnames) == ["file_name", "reason", "path"]
    assert rows == [
        {
            "file_name": "invalid.xml",
            "reason": "Missing element.",
            "path": "/root"
        }
    ]


# reset()

def test_reset_clears_all_recorder_state():
    """
    Test that reset() clears all stored recorder state.

    Priority: H
    """
    recorder = ValidatorResultRecorder()
    recorder.errors_by_file = [{"file_name": "invalid.xml"}]
    recorder.validation_summary = {
        "valid": ["valid.xml"],
        "invalid": ["invalid.xml"]
    }
    recorder.error_table_id = 3
    # Call the method under test.
    recorder.reset()
    # Expected outcome: all recorder state is restored to defaults.
    assert recorder.errors_by_file == []
    assert recorder.validation_summary == {"valid": [], "invalid": []}
    assert recorder.error_table_id == 0


# ValidatorResult.__init__()

def test_validator_result_stores_success_value():
    """
    Test that ValidatorResult stores a successful operation result.

    Priority: M
    """
    # Call the method under test.
    result = ValidatorResult(success=True, value="payload")
    # Expected outcome: success and value are stored unchanged.
    assert result.success is True
    assert result.value == "payload"
    assert result.error is None


def test_validator_result_stores_failure_error():
    """
    Test that ValidatorResult stores a failed operation result.

    Priority: M
    """
    # Call the method under test.
    result = ValidatorResult(success=False, error="failure")
    # Expected outcome: failure state and error are stored unchanged.
    assert result.success is False
    assert result.value is None
    assert result.error == "failure"


# ValidatorResult.__repr__()

def test_validator_result_repr_returns_success_representation():
    """
    Test that ValidatorResult.__repr__() describes successful results.

    Priority: L
    """
    result = ValidatorResult(success=True, value="payload")
    # Expected outcome: the representation contains the success value.
    assert repr(result) == "Result(success=True, value=payload)"


def test_validator_result_repr_returns_failure_representation():
    """
    Test that ValidatorResult.__repr__() describes failed results.

    Priority: L
    """
    result = ValidatorResult(success=False, error="failure")
    # Expected outcome: the representation contains the error value.
    assert repr(result) == "Result(success=False, error=failure)"
