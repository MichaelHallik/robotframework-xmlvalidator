*** Settings ***
Documentation    Tests various sorts of error handling.
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
Suite Teardown    Default Test Suite Teardown
Variables    teardown_vars.py


*** Variables ***
# ${DELETE_CSV} determines deletion of the csv output files; values can be:
# - bool ${False}:    no delete at all
# - bool ${True}:     delete the one csv, as generated in current test case run
# - str 'All':        delete all csv files present in test case data folder
# ${DELETE_CSV}=    all


*** Test Cases ***
15_Import_With_Non_Existing_XSD
    [Documentation]    Attempt import:
    ...                - once with a path to a non-existent XSD file
    ...                - once with a path to an an empty folder
    ...                - once with a path to a non-xsd file
    ...    
    ...                Verify that the library catches the errors and 
    ...                constructs and reports an informative error 
    ...                message.
    [Tags]    git-exclude
    # Set up test variables.
    ${xsd_path_1} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_15/15_non_existing.xsd
    ${xsd_path_2} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_15/empty_folder
    ${xsd_path_3} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_15/non_xsd_extension/15_test_schema.txt
    # Import with the three invalid XSD paths and validate each error is catched and reported.
    ## Path to non-existing file.
    Run Keyword And Expect Error    * ValueError: The provided path is neither a file nor a folder: *    Import Library    xmlvalidator    ${xsd_path_1}    AS    ${TEST_NAME}
    ## Path to an empty folder (could also contain one or more non-xsd files).
    ${status}    ${error}=    Run Keyword And Ignore Error    Import Library    xmlvalidator    ${xsd_path_2}    AS    ${TEST_NAME}
    Should Contain    ${error}    Initializing library 'xmlvalidator' with arguments [ ${EXECDIR}/test/_data/integration/TC_15/empty_folder ] failed: ValueError: No files reside in the folder: [].
    ## Path to a non-xsd file.
    ${status}    ${error}=    Run Keyword And Ignore Error    Import Library    xmlvalidator    ${xsd_path_3}    AS    ${TEST_NAME}
    Should Contain    ${error}    ValueError: ${EXECDIR}\\test\\_data\\integration\\TC_15\\non_xsd_extension\\15_test_schema.txt is not an XSD file.

16_Validate_Non_Existing_XML
    [Documentation]    Attempt to validate a non-existent XML file and 
    ...                verify that the library catches the error and 
    ...                constructs and reports an informative error 
    ...                message.
    # Set up test variables.
    ${xsd_path} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_16/16_test_schema.xsd
    ${xml_missing} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_16/16_non_existing.xml
    # Call the keyword and validate the error is catched and reported.
    Import Library    xmlvalidator    ${xsd_path}    AS    ${TEST_NAME}
    Run Keyword And Expect Error    ValueError: The provided path is neither a file nor a folder: *    ${TEST_NAME}.Validate Xml Files    ${xml_missing}
    # Teardown (and validate schema attribute is None).
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    Should Be Equal    ${xml_validator.schema.name}    16_test_schema.xsd
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    [Teardown]    Default Test Case Teardown    ${None}    ${DELETE_CSV}    ${xml_validator}    ${TEST NAME}

17_Validate_Against_Malformed_XSD
    [Documentation]    Attempt to validate an XML against malformed XSD 
    ...                files and verify that the library catches the 
    ...                errors and constructs and reports an informative 
    ...                error message.
    # Set up test variables.
    ${xsd_malformed_1}=    Set Variable    ${EXECDIR}/test/_data/integration/TC_17/17_malformed_1.xsd
    ${xsd_malformed_2}=    Set Variable    ${EXECDIR}/test/_data/integration/TC_17/17_malformed_2.xsd
    ${xml_path}=    Set Variable    ${EXECDIR}/test/_data/integration/TC_17/17_valid_xml.xml
    # Call the keyword and validate errors are catched and reported.
    Import Library    xmlvalidator    AS    ${TEST_NAME}
    ${result}=    Run Keyword And Expect Error    SystemError: Loading of schema failed: {'XMLSchemaValidationError': ParseError('no element found: line 11, column 0')}.    ${TEST_NAME}.Validate Xml Files    ${xml_path}    ${xsd_malformed_1}
    ${result}=    Run Keyword And Expect Error    SystemError: Loading of schema failed: {'XMLSchemaValidationError': XMLSchemaParseError(XMLSchema10(name='17_malformed_2.xsd', namespace=''), "Unexpected child with tag 'xs:invalidTag' at position 2.", <Element '{http://www.w3.org/2001/XMLSchema}schema' at *   ${TEST_NAME}.Validate Xml Files    ${xml_path}    ${xsd_malformed_2}
    # Teardown (and validate schema attribute is None).
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    Should Be Equal    ${xml_validator.schema}    ${None}
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    [Teardown]    Default Test Case Teardown    ${None}    ${DELETE_CSV}    ${xml_validator}    ${TEST NAME}

18_Validate_Non_Existing_XSD
    [Documentation]    Attempt validation of an XML file:
    ...                - once with a path to a non-existent XSD file
    ...                - once with a path to an an empty folder
    ...                - once with a path to a non-xsd file
    ...    
    ...                Verify that the library catches the errors and 
    ...                constructs and reports an informative error 
    ...                message.
    [Tags]    git-exclude
    # Set up test variables.
    ${xsd_path_1} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_18/18_non_existing.xsd
    ${xsd_path_2} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_18/empty_folder
    ${xsd_path_3} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_18/non_xsd_extension/18_test_schema.txt
    ${xml_path} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_18/18_valid_test.xml
    # Call the keyword and validate errors are catched and reported.
    Import Library    xmlvalidator    AS    ${TEST_NAME}
    ## Path to non-existing file.
    ${result}=    Run Keyword And Expect Error    ValueError: The provided path is neither a file nor a folder: *    ${TEST_NAME}.Validate Xml Files    ${xml_path}    ${xsd_path_1}
    ## Path to an empty folder (could also contain one or more non-xsd files).
    ${status}    ${error}=    Run Keyword And Ignore Error    Import Library    xmlvalidator    ${xsd_path_2}    AS    ${TEST_NAME}
    Should Contain    ${error}    Initializing library 'xmlvalidator' with arguments [ ${EXECDIR}/test/_data/integration/TC_18/empty_folder ] failed: ValueError: No files reside in the folder: [].
    ## Path to a non-xsd file.
    ${status}    ${error}=    Run Keyword And Ignore Error    Import Library    xmlvalidator    ${xsd_path_3}    AS    ${TEST_NAME}
    Should Contain    ${error}    ValueError: ${EXECDIR}\\test\\_data\\integration\\TC_18\\non_xsd_extension\\18_test_schema.txt is not an XSD file.
    # Teardown (and validate schema attribute is None).
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    Should Be Equal    ${xml_validator.schema}    ${None}
    [Teardown]    Default Test Case Teardown    ${None}    ${DELETE_CSV}    ${xml_validator}    ${TEST NAME}