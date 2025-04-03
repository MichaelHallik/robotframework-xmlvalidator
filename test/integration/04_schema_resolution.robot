*** Settings ***
Documentation    Focusses on testing the functionality that matches XML 
...              files to their respective schema files.
...
...              Note that each test case uses it's own, unique library 
...              instance. Because of the scope of the XmlValidator 
...              library (GLOBAL), only one instance is created when 
...              running the test suite as a whole. That is, importing 
...              such a library in the Settings section will create one 
...              library instance which is shared by all test cases.
...              Given the nature of the test cases in this test suite, 
...              the latter may lead to false negatives.
Resource    ${EXECDIR}/test/integration/validation_keywords.resource
Variables    teardown_vars.py


*** Variables ***
# ${DELETE_CSV} determines deletion of the csv output files; values can be:
# - bool ${False}:    no delete at all
# - bool ${True}:     delete the one csv, as generated in current test case run
# - str 'All':        delete all csv files present in test case data folder
# ${DELETE_CSV}=    all


*** Test Cases ***
19_Validate_Using_Namespace_Matching_Different_folders
    [Documentation]    Validate XML files against XSD schemas, matching 
    ...                them dynamically by using namespace resolution.
    ...    
    ...                The XSD files reside in a folder different from 
    ...                the folder holding the XML files.
    # Set up test variables.
    ${xml_folder} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_19/
    ${xsd_folder} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_19/xsd/
    # Import the library.
    Import Library    xmlvalidator    AS    ${TEST_NAME}
    # Validate the XML files.
    ${errors}    ${csv_path}=    Run Keyword    ${TEST_NAME}.Validate Xml Files    ${xml_folder}    ${xsd_folder}
    # Define the expected results.
    ${expected_errors} =    Create Dictionary    
    ...                        file_name=19_invalid_test.xml
    ...                        reason=Unexpected child with tag '{http://example.com/ns1}wrongElement' at position 1. Tag '{http://example.com/ns1}child' expected.
    # Validate the validation results are as expected.
    Validate Xml Validation Result    ${errors}    ${expected_errors}
    # Validate the CSV output.
    Validate CSV    ${csv_path}    ${expected_errors}
    # Teardown.
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    [Teardown]    Default Test Case Teardown    ${csv_path}    ${DELETE_CSV}    ${xml_validator}    ${TEST NAME}

20_Validate_Using_Namespace_Matching_Same_folder
    [Documentation]    Validate XML files against XSD schemas, matching 
    ...                them dynamically by using namespace resolution.
    ...    
    ...                The XSD files reside in the same folder as the 
    ...                XML files. Therefore we do not have to specify a 
    ...                seperate path to the XSD files upon calling the 
    ...                keyword.
    # Set up test variables.
    ${xml_folder} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_20/
    # Import the library.
    Import Library    xmlvalidator    AS    ${TEST_NAME}
    # Validate the XML files, passing xsd_search_strategy, but passing NO xsd_path.
    ${errors}    ${csv_path}=    Run Keyword    ${TEST_NAME}.Validate Xml Files    ${xml_folder}    xsd_search_strategy=by_namespace
    # Define the expected results.
    ${expected_errors} =    Create Dictionary    
    ...                        file_name=20_invalid_test.xml
    ...                        reason=Unexpected child with tag '{http://example.com/ns1}wrongElement' at position 1. Tag '{http://example.com/ns1}child' expected.
    # Validate the validation results are as expected.
    Validate Xml Validation Result    ${errors}    ${expected_errors}
    # Validate the CSV output.
    Validate CSV    ${csv_path}    ${expected_errors}
    # Teardown.
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    [Teardown]    Default Test Case Teardown    ${csv_path}    ${DELETE_CSV}    ${xml_validator}    ${TEST NAME}

21_Validate_Using_Filename_Matching
    [Documentation]    Validate XML files against XSD schemas, matching 
    ...                them dynamically based on file name.
    # Set up test variables.
    ${xml_folder} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_21/
    # Import the library.
    Import Library    xmlvalidator    AS    ${TEST_NAME}
    # Validate the XML files.
    ${errors}    ${csv_path}=    Run Keyword    ${TEST_NAME}.Validate Xml Files    ${xml_folder}    xsd_search_strategy=by_file_name
    # Define the expected results.
    ${expected_errors} =    Create Dictionary    
    ...                        file_name=21_invalid_test.xml
    ...                        reason=invalid literal for int() with base 10: 'invalid_value'
    # Validate the validation results are as expected.
    Validate Xml Validation Result    ${errors}    ${expected_errors}
    # Validate the CSV output.
    Validate CSV    ${csv_path}    ${expected_errors}
    # Teardown.
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    [Teardown]    Default Test Case Teardown    ${csv_path}    ${DELETE_CSV}    ${xml_validator}    ${TEST NAME}

22_Validate_With_No_File_Match
    [Documentation]    Validate XML files against XSD schemas (using 
    ...                namespace matching), where one XML file does not 
    ...                have a matching XSD counterpart.
    # Set up test variables.
    ${xml_folder} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_22/
    # Import the library.
    Import Library    xmlvalidator    AS    ${TEST_NAME}
    # Validate the XML files.
    ${errors}    ${csv_path}=    Run Keyword    ${TEST_NAME}.Validate Xml Files    ${xml_folder}    xsd_search_strategy=by_namespace
    # Define the expected results.
    ${expected_errors} =    Create Dictionary    
    ...                        file_name=22_no_match.xml
    ...                        reason=No matching XSD found for: 22_no_match.
    # Validate the validation results are as expected.
    Validate Xml Validation Result    ${errors}    ${expected_errors}
    # Validate the CSV output.
    Validate CSV    ${csv_path}    ${expected_errors}
    # Teardown.
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    [Teardown]    Default Test Case Teardown    ${csv_path}    ${DELETE_CSV}    ${xml_validator}    ${TEST NAME}