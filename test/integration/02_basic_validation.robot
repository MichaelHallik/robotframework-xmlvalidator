*** Settings ***
Documentation    Tests basic XML validation functionality using 
...              XmlValidator.
...
...              Note that each test case uses it's own, unique library 
...              instance. Because of the scope of the XmlValidator 
...              library (GLOBAL), only one instance is created when 
...              running the test suite as a whole. That is, importing 
...              such a library in the Settings section will create one 
...              library instance which is shared by all test cases.
...              Given the nature of the test cases in this test suite, 
...              the latter may lead to false negatives.
Library    Collections
Resource    ${EXECDIR}/test/integration/validation_keywords.resource
Suite Teardown    Default Test Suite Teardown
Variables    teardown_vars.py


*** Variables ***
# ${DELETE_CSV} determines deletion of the csv output files; values can be:
# - bool ${False}:    no delete at all
# - bool ${True}:     delete the one csv, as generated in current test case run
# - str 'All':        delete all csv files present in test case data folder
# ${DELETE_CSV}=    all


*** Test Cases ***
07_Validate_Single_Valid_XML
    [Documentation]    Validate a single, valid XML file against a valid 
    ...                XSD schema.
    ...    
    ...                Should return no error(s) and hence shouldn't 
    ...                write a CSV file.
    # Set up test variables.
    ${xsd_path} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_07/07_test_schema.xsd
    ${xml_path} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_07/07_valid_test.xml
    # Import the library and call the keyword.
    Import Library    xmlvalidator    ${xsd_path}    AS    ${TEST_NAME}
    ${errors}    ${csv_path}=    Run Keyword    ${TEST_NAME}.Validate Xml Files    ${xml_path}
    # Validate the keyword returns (no errors and no CSV file path).
    @{expected_errors}=    Create List
    Lists Should Be Equal    ${expected_errors}    ${errors}
    Should Be Equal    ${csv_path}    ${None}
    # Teardown.
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    [Teardown]    Default Test Case Teardown    ${csv_path}    ${DELETE_CSV}    ${xml_validator}    ${TEST NAME}

08_Validate_Single_Invalid_XML
    [Documentation]    Validate a single, invalid XML file against a 
    ...                valid XSD schema and verify the correctness of 
    ...                the error reporting of the keyword.
    ...    
    ...                The latter means we validate the list of errors 
    ...                the keyword returns and the corresponding CSV 
    ...                file it should have created (containing the 
    ...                collected errors in CSV format).
    # Set up test variables.
    ${xsd_path} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_08/08_test_schema.xsd
    ${xml_path} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_08/08_invalid_test.xml
    # Import the library and call the keyword.
    Import Library    xmlvalidator    ${xsd_path}    fail_on_errors=${False}    AS    ${TEST_NAME}
    ${errors}    ${csv_path}=    Run Keyword    ${TEST_NAME}.Validate Xml Files    ${xml_path}
    # Define the expected results.
    ${expected_errors} =    Create Dictionary    
    ...                        file_name=08_invalid_test.xml
    ...                        path=/root
    ...                        reason=Unexpected child with tag 'wrongChild' at position 1. Tag 'child' expected. 
    # Validate the returned errors list.
    Validate Xml Validation Result    ${errors}    ${expected_errors}
    # Validate the created CSV file.
    Validate CSV    ${csv_path}    ${expected_errors}
    # Teardown.
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    [Teardown]    Default Test Case Teardown    ${csv_path}    ${DELETE_CSV}    ${xml_validator}    ${TEST NAME}

09_Validate_Multiple_Valid_XMLs
    [Documentation]    Validate multiple valid XML files against a 
    ...                single, valid XSD schema.
    ...    
    ...                Should return no error(s) and hence shouldn't 
    ...                write a CSV file.
    # Set up test variables.
    ${xsd_path} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_09/09_test_schema.xsd
    ${xml_path} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_09
    # Import the library and call the keyword.
    Import Library    xmlvalidator    ${xsd_path}    AS    ${TEST_NAME}
    ${errors}    ${csv_path}=    Run Keyword    ${TEST_NAME}.Validate Xml Files    ${xml_path}
    # Validate the keyword returns (no errors and no CSV file path).
    @{expected_errors}=    Create List
    Lists Should Be Equal    ${expected_errors}    ${errors}
    Should Be Equal    ${csv_path}    ${None}
    # Teardown.
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    [Teardown]    Default Test Case Teardown    ${csv_path}    ${DELETE_CSV}    ${xml_validator}    ${TEST NAME}

10_Validate_Multiple_XMLs_With_Multiple_XSDs
    [Documentation]    Validate multiple valid XML files against 
    ...                multiple XSD schemas.
    ...    
    ...                Should return no error(s) and hence shouldn't 
    ...                write a CSV file.
    ...    
    ...                By passing 'by_file_name' as 
    ...                ``xsd_search_strategy``, each XML files are is 
    ...                matched to its corresponding XSD file (namely 
    ...                the XSD file that has the same file name as its 
    ...                XML counterpart).
    # Set up test variables.
    ${xsd_path} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_10
    ${xml_path} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_10
    # Import the library and call the keyword.
    Import Library    xmlvalidator    AS    ${TEST_NAME}
    ${errors}    ${csv_path}=    Run Keyword    ${TEST_NAME}.Validate Xml Files    ${xml_path}    ${xsd_path}    xsd_search_strategy=by_file_name
    # Validate the keyword returns (no errors and no CSV file path).
    @{expected_errors}=    Create List
    Lists Should Be Equal    ${expected_errors}    ${errors}
    Should Be Equal    ${csv_path}    ${None}
    # Teardown.
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    [Teardown]    Default Test Case Teardown    ${csv_path}    ${DELETE_CSV}    ${xml_validator}    ${TEST NAME}

11_Validate_Mixed_Results_With_Single_XSD
    [Documentation]    Validate multiple XML files against a single XSD 
    ...                schema where some files pass validation and 
    ...                others fail.
    ...    
    ...                The test case subsequently validates the 
    ...                expected validation results that the keyword 
    ...                should return/report.
    # Set up test variables.
    ${xsd_path} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_11
    ${xml_valid} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_11
    # Import the library and call the keyword.
    Import Library    xmlvalidator    ${xsd_path}    fail_on_errors=${False}    AS    ${TEST_NAME}
    ${errors}    ${csv_path}=    Run Keyword    ${TEST_NAME}.Validate Xml Files    ${xml_valid}
    # Define the expected results.
    ${expected_errors_1} =    Create Dictionary
    ...                        file_name=11_invalid_test_1.xml
    ...                        path=/root
    ...                        reason=Unexpected child with tag 'wrongChild' at position 1. Tag 'child' expected.
    ${expected_errors_2} =    Create Dictionary    
    ...                        file_name=11_invalid_test_2.xml
    ...                        path=/root/value
    ...                        reason=invalid literal for int() with base 10: 'hello'
    # Validate the returned errors list.
    Validate Xml Validation Results    ${errors}    ${expected_errors_1}    ${expected_errors_2}
    # Validate the CSV output.
    Validate CSV    ${csv_path}    ${expected_errors_1}    ${expected_errors_2}
    # Teardown.
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    [Teardown]    Default Test Case Teardown    ${csv_path}    ${DELETE_CSV}    ${xml_validator}    ${TEST NAME}

12_Validate_Mixed_Results_With_Multiple_XSDs
    [Documentation]    Validate multiple XML files against multiple XSD 
    ...                schemas where some files pass validation and 
    ...                others fail.
    ...    
    ...                The test case subsequently validates the 
    ...                expected validation results that the keyword 
    ...                should return/report.
    ...    
    ...                Note from the log that the XML and XSD files will 
    ...                be matched dynamically, using their namespaces as 
    ...                matching strategy.
    # Set up test variables.
    ${xml_path} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_12
    ${xsd_path} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_12
    # Import the library and call the keyword.
    Import Library    xmlvalidator    fail_on_errors=${False}    AS    ${TEST_NAME}
    ${errors}    ${csv_path}=    Run Keyword    ${TEST_NAME}.Validate Xml Files    ${xml_path}    ${xsd_path}
    # Define the expected results.
    ${expected_errors_1} =    Create Dictionary    
    ...                        file_name=12_invalid_test_1.xml
    ...                        path=/root
    ...                        reason=Unexpected child with tag '{http://example.com/ns1}wrongElement' at position 1. Tag '{http://example.com/ns1}child' expected.
    ${expected_errors_2} =    Create Dictionary    
    ...                        file_name=12_invalid_test_2.xml
    ...                        path=/data/value
    ...                        reason=invalid literal for int() with base 10: 'NaN'
    ${expected_errors_3} =    Create Dictionary    
    ...                        file_name=12_no_match.xml
    ...                        reason=No matching XSD found for: 12_no_match.
    # Validate the returned errors list.
    Validate Xml Validation Results    ${errors}    ${expected_errors_1}    ${expected_errors_2}    ${expected_errors_3}
    # Validate the CSV output.
    Validate CSV    ${csv_path}    ${expected_errors_1}    ${expected_errors_2}    ${expected_errors_3}
    # Teardown.
    # Run keyword    ${TEST_NAME}.Reset Schema
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    [Teardown]    Default Test Case Teardown    ${csv_path}    ${DELETE_CSV}    ${xml_validator}    ${TEST NAME}

13_ImportLibrary_Change_Schema_On_Validation
    [Documentation]    Import the XmlValidator library with an XSD file, 
    ...                validate that the schema attribute is correctly 
    ...                set, then call the Validate XML Files keyword 
    ...                with a valid XML file and a *new* XSD file, 
    ...                verifying that the new schema is correctly set 
    ...                and used for validation.
    ...    
    ...                Note:
    ...    
    ...                This test case should probably be moved to 
    ...                another test suite file.
    # Set up test variables.
    ${xsd_path_1} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_13/13_test_schema_1.xsd
    ${xsd_path_2} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_13/13_test_schema_2.xsd
    ${xml_path} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_13/13_valid_test.xml
    # Import the library with the first schema and validate correct setting of the schema attribute.
    Import Library    xmlvalidator    ${xsd_path_1}    AS    ${TEST NAME}
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    Should Be Equal    ${xml_validator.schema.name}    13_test_schema_1.xsd
    # Validate XML, passing a different/second schema to the keyword.
    ${errors}    ${csv_path}=    Run Keyword    ${TEST_NAME}.Validate Xml Files    ${xml_path}    ${xsd_path_2}
    # Validate the results.
    Should Be Equal    ${xml_validator.schema.name}    13_test_schema_2.xsd
    @{expected_errors}=    Create List
    Lists Should Be Equal    ${expected_errors}    ${errors}    Validation should pass only if second schema is used.
    # Teardown.
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    [Teardown]    Default Test Case Teardown    ${csv_path}    ${DELETE_CSV}    ${xml_validator}    ${TEST NAME}

14_Validate_Malformed_XML
    [Documentation]    Attempt to validate a malformed XML file and 
    ...                verify that a parse/syntax error is collected and 
    ...                reported.
    # Set up test variables.
    ${xsd_path} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_14/14_test_schema.xsd
    ${xml_malformed} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_14/14_malformed.xml
    # Import the library and call the keyword.
    Import Library    xmlvalidator    ${xsd_path}    fail_on_errors=${False}    AS    ${TEST_NAME}
    ${errors}    ${csv_path}=    Run Keyword    ${TEST_NAME}.Validate Xml Files    ${xml_malformed}
    # Define the expected results.
    ${expected_errors} =    Create Dictionary    
    ...                        file_name=14_malformed.xml
    ...                        reason=File parsing failed.
    ...                        msg=Opening and ending tag mismatch: child line 3 and root, line 4, column 8
    ...                        position=Line 4, Column 8.
    ...                        Error type=XMLSyntaxError
    # Validate the errors lists.
    Validate Xml Validation Result    ${errors}    ${expected_errors}
    # Validate the CSV output.
    Validate CSV    ${csv_path}    ${expected_errors}
    # Teardown.
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    [Teardown]    Default Test Case Teardown    ${csv_path}    ${DELETE_CSV}    ${xml_validator}    ${TEST NAME}