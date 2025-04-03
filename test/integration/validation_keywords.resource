*** Settings ***
Documentation     Contains reusable test functions for XML validation, 
...               CSV validation, and test lifecycle management. It 
...               provides utilities for:
...    
...               - Validating XML and CSV output
...               - Managing test case teardowns
...               - Logging library instances and schema details
...               - Cleaning up CSV files after test execution
...               - And others
Library    Collections
Library    OperatingSystem
Library    ${EXECDIR}/test/integration/validation_keywords.py


*** Keywords ***
Default Test Case Teardown
    [Documentation]    Purpose:
    ...    
    ...                Handles cleanup operations after each test case. 
    ...                Deletes CSV files and logs the currently loaded 
    ...                schema.
    ...    
    ...                Arguments:
    ...    
    ...                - csv_path (str):
    ...                  Path to the CSV file generated during the test.
    ...                - delete_csv (bool or str):
    ...                  Determines whether to delete CSV files:
    ...                  - False (bool):
    ...                    No deletion.
    ...                  - True  (bool):
    ...                    Deletes the CSV file passed through csv_path.
    ...                  - "all" (str):
    ...                    Deletes all CSV files in the folder.
    ...                - lib_instance (XmlValidator object):
    ...                  The instance of the XmlValidator library used 
    ...                  in the test case.
    ...    
    ...                Steps:
    ...    
    ...                - Calls Delete CSV File to clean up CSV files.
    ...                - Calls Log Current Schema to record the current 
    ...                  state of the library instance's schema 
    ...                  attribute.
    [Arguments]    ${csv_path}    ${delete_csv}    ${lib_instance}    ${instance_name}    ${reset_schema}=${True}
    Log    ============== Running test teardown ... ==============    level=WARN
    # Delete the CSV file(s), if required.
    IF    $csv_path
        Delete CSV File    ${csv_path}    ${delete_csv}
    END
    # Log the schema attribute.
    Log Current Schema    ${lib_instance}
    # Set the schema attribute to Python None, if requested.
    IF    ${reset_schema}
        Log    Resetting schema ...    level=WARN
        Run keyword    ${instance_name}.Reset Schema
        Log Current Schema    ${lib_instance}
    END
    Log    =======================================================    level=WARN

Default Test Suite Teardown
    [Documentation]    Purpose:
    ...    
    ...                Executed after the entire test suite runs. Logs 
    ...                all currently loaded Robot Framework libraries 
    ...                and their instances.
    ...    
    ...                Steps:
    ...    
    ...                Calls Log Loaded Library Instances to capture all 
    ...                active library instances.
    Log    ============== Running suite teardown ... ==============    level=WARN
    Log Loaded Library Instances
    Log    ========================================================    level=WARN

Delete CSV File
    [Arguments]    ${csv_path}    ${delete_csv}
    [Documentation]    Purpose:
    ...    
    ...                Manages CSV file deletion after test execution.
    ...    
    ...                Arguments:
    ...    
    ...                - csv_path (str):
    ...                  Path to the CSV file generated during the test.
    ...                - False (bool):
    ...                  No deletion.
    ...                - True  (bool):
    ...                  Deletes the latest CSV file
    ...                - "all" (str):
    ...                  Deletes all CSV files in the folder
    # Only log if no file removal is to be performed.
    IF    $delete_csv == $False
        Log    CSV file NOT deleted: ${csv_path}    level=WARN
    # Delete a specific file or all CSV files (in the target folder).
    ELSE
        # Delete a specific file.
        IF    $delete_csv == $True
            Remove File    ${csv_path}
            Log    One CSV file deleted: ${csv_path}    level=WARN
        ELSE
            # Delete all files.
            IF    $delete_csv == all
                # Get the target folder.
                ${csv_folder}=    Evaluate    str(pathlib.Path(r"${csv_path}").parent)    modules=pathlib
                # And remove all CSV files found in that folder.
                Remove File    ${csv_folder}${/}*.csv
                Log    Removed all CSV files from folder.    level=WARN
            # Handle incorrect argument.
            ELSE
                Fail    Arg ``delete_csv`` must be: bool True, bool False or str 'all'.
            END
        END
    END

Log Current Schema
    [Arguments]    ${lib_instance}
    [Documentation]    Purpose:
    ...                Logs the currently loaded XML schema in the 
    ...                XmlValidator instance.
    ...    
    ...                Arguments:
    ...    
    ...                - lib_instance (XmlValidator object):
    ...                  The XmlValidator instance whose schema should 
    ...                  be logged.
    ...    
    ...                Steps:
    ...    
    ...                Logs the currently loaded schema by accessing 
    ...                lib_instance.schema.name.
    IF    $lib_instance.schema
        Log    Schema currently loaded: ${lib_instance.schema.name}    level=WARN
    ELSE
        Log    Schema currently loaded: None    level=WARN
    END

Log Loaded Library Instances
    [Documentation]    Purpose:
    ...    
    ...                Logs all currently loaded libraries in Robot 
    ...                Framework, specifically highlighting XmlValidator 
    ...                instances.
    ...    
    ...                Steps:
    ...    
    ...                Retrieves all library instances using Get Library 
    ...                Instance all=${True}.
    ...                Logs the dictionary of all loaded libraries.
    ...                Iterates over the libraries: if the library is an 
    ...                instance of XmlValidator, it logs the name of the 
    ...                instance with WARN level.
    # Get all library instances loaded.
    &{library_instances}=    Get Library Instance    all=${True}
    Log    XMLValidator instances loaded in this test suite:    level=WARN
    # Filter out instances that are not of XmlValidator.
    FOR    ${key}    ${value}    IN    &{library_instances}
        ${value_str}=    Convert To String    ${value}
        IF    "XmlValidator" in "${value_str}"
            Log    - ${key}    level=WARN
            Log    ${value.schema}    level=INFO
        END
    END

Validate CSV
    [Documentation]    Purpose:
    ...    
    ...                Validates the CSV output against expected error 
    ...                entries.
    ...    
    ...                Arguments:
    ...    
    ...                - csv_path (str):
    ...                  Path to the generated CSV file.
    ...                - expected_errors (list of dicts):
    ...                  List of expected error entries.
    ...    
    ...                Steps:
    ...    
    ...                Calls Validate Csv Output to compare the actual 
    ...                CSV content against expected errors. Fails the 
    ...                test if mismatches are found. Logs a success 
    ...                message if validation passes.
    [Arguments]    ${csv_path}    @{expected_errors}
    Log    =========== Validating the CSV output file. ===========    level=WARN
    ${status}    ${mismatches}=    Validate Csv Output    ${csv_path}    ${expected_errors}
    Should Be True    ${status}    msg=CSV validation failed: ${mismatches}.
    Log    CSV validation successful.    level=WARN

Validate Xml Validation Result
    [Documentation]    Purpose:

    ...                Validates the structure and content of an XML 
    ...                validation result.
    ...    
    ...                Arguments:
    ...    
    ...                - actual_errors (list of dicts):
    ...                  Errors returned by the XML validation process.
    ...                - expected_errors (dict):
    ...                  Dictionary containing expected error attributes.
    ...    
    ...                Steps:
    ...    
    ...                Ensures ${actual_errors} is a list.
    ...                Ensures the list is not empty.
    ...                Iterates through each actual error:
    ...                Checks that all expected keys are present.
    ...                Iterates through each expected key:
    ...                - Verifies at least one actual error contains the expected 
    ...                  value.
    ...                Logs success if all validations pass.
    [Arguments]    ${actual_errors}    ${expected_errors}
    # Validate that the actual_results list is, indeed, a list.
    ${data_type} =    Evaluate    type( ${actual_errors} ).__name__
    Should Be Equal As Strings    ${data_type}    list    msg=The actual_errors var should be of type list.
    # Validate that the actual_results list is not empty.
    Should Not Be Empty    ${actual_errors}    msg="Validation result should not be empty."
    # Validate the structure of each error.
    FOR    ${actual_error}    IN    @{actual_errors}
        Log    ${actual_error}    level=INFO
        FOR    ${key}    IN    @{expected_errors.keys()}
            Log    ${key}    level=INFO
            Dictionary Should Contain Key    ${actual_error}    ${key}
        END
    END
    # Validate expected values in at least one entry.
    FOR    ${key}    IN    @{expected_errors.keys()}
        ${values} =    Evaluate    [entry["${key}"] for entry in ${actual_errors}]
        List Should Contain Value    ${values}    ${expected_errors}[${key}]
    END
    Log    Errors returned by XmlValidator are as expected.

Validate Xml Validation Results
    [Documentation]    Purpose:

    ...                Validates the structure and content of an XML 
    ...                validation result.
    ...    
    ...                Arguments:
    ...    
    ...                - actual_errors (list of dicts):
    ...                  Errors returned by the XML validation process.
    ...                - expected_errors_list (list of dicts):
    ...                  List of dictionaries containing expected error attributes.
    ...    
    ...                Steps:
    ...    
    ...                Ensures ${actual_errors} is a list.
    ...                Ensures the list is not empty.
    ...                Iterates through each expected error:
    ...                - Checks that all expected keys are present in at least one actual error.
    ...                - Ensures at least one actual error contains the expected values.
    ...                Logs success if all validations pass.
    [Arguments]    ${actual_errors}    @{list_expected_errors}
    FOR    ${expected_errors}    IN    @{list_expected_errors}
        Validate Xml Validation Result    ${actual_errors}    ${expected_errors}
    END