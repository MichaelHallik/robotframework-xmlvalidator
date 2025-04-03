*** Settings ***
Documentation    This suite tests the importing of the XmlValidator 
...              library in different ways.
...
...              Note that each test case uses it's own, unique library 
...              instance. Because of the scope of the XmlValidator 
...              library (GLOBAL), only one instance is created when 
...              running the test suite as a whole. That is, importing 
...              such a library in the Settings section will create one 
...              library instance which is shared by all test cases.
...              Given the nature of the test cases in this test suite, 
...              a suite-level import is impossible.
Resource    ${EXECDIR}/test/integration/validation_keywords.resource
Suite Teardown    Default Test Suite Teardown
Variables    teardown_vars.py


*** Variables ***
# ${DELETE_CSV} determines deletion of the csv output files; values can be:
# - bool ${False}:    no delete at all
# - bool ${True}:     delete one csv, as generated in current test case run
# - str 'All':        delete all csv files present in test case data folder
# ${DELETE_CSV}=    all


*** Test Cases ***
01_ImportLibrary_Default
    [Documentation]    Import the XmlValidator library without 
    ...                arguments and verify the correct initialization 
    ...                of the schema and error_facets _attribute.
    # Import the library.
    Import Library    xmlvalidator    AS    ${TEST NAME}
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    # Validate the schema and error facets attributes.
    Should Be Equal    ${xml_validator.schema}    ${None}
    ${passed_error_facets} =    Create List    path    reason
    Lists Should Be Equal    ${passed_error_facets}    ${xml_validator.error_facets}

02_ImportLibrary_With_XSD
    [Documentation]    Import the XmlValidator library, passing an XSD 
    ...                schema file and verify correct initialization of 
    ...                the schema attribute.
    # Set up test variables.
    ${xsd_path} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_02/02_test_schema.xsd
    # Import the library.
    Import Library    xmlvalidator    ${xsd_path}    AS    ${TEST NAME}
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    # Validate only the schema.
    Should Be Equal    ${xml_validator.schema.name}    02_test_schema.xsd
    Dictionary Should Contain Key    ${xml_validator.schema.elements}    root
    # Teardown.
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    [Teardown]    Default Test Case Teardown    ${None}    ${DELETE_CSV}    ${xml_validator}    ${TEST NAME}

03_ImportLibrary_With_Base_URL
    [Documentation]    Import the XmlValidator library with a an XSD 
    ...                schema file *and* a base URL (referencing an XSD 
    ...                include file) and verify the correct 
    ...                initialization of the schema attribute.
    # Set up test variables.
    ${xsd_path} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_03/03_test_schema_with_include.xsd
    ${base_url} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_03/
    # Import the library.
    Import Library    xmlvalidator    ${xsd_path}    base_url=${base_url}    AS    ${TEST NAME}
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    # Validate the schema.
    Should Be Equal    ${xml_validator.schema.name}    03_test_schema_with_include.xsd
    Dictionary Should Contain Key    ${xml_validator.schema.elements}    root
    # Teardown.
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    [Teardown]    Default Test Case Teardown    ${None}    ${DELETE_CSV}    ${xml_validator}    ${TEST NAME}

04_ImportLibrary_With_Error_Facets
    [Documentation]    Import the XmlValidator library with custom error 
    ...                facets and verify the correct initialization of 
    ...                the error_facets attribute.
    # Set up test variables.
    ${xsd_path} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_04/04_test_schema.xsd
    ${passed_error_facets} =    Create List    path    reason    line_number
    # Import the library.
    Import Library    xmlvalidator    ${xsd_path}    error_facets=${passed_error_facets}    AS    ${TEST NAME}
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    # Validate the schema and error_facets attributes.
    Should Be Equal    ${xml_validator.schema.name}    04_test_schema.xsd
    Dictionary Should Contain Key    ${xml_validator.schema.elements}    root
    Lists Should Be Equal    ${passed_error_facets}    ${xml_validator.error_facets}
    [Teardown]    Default Test Case Teardown    ${None}    ${DELETE_CSV}    ${xml_validator}    ${TEST NAME}

05_ImportLibrary_Invalid_XSD
    [Documentation]    Attempt to import the XmlValidator library with 
    ...                an invalid XSD file and verify the informative 
    ...                and structured error message that the library 
    ...                constructs and returns.
    [Tags]    TODO    Not yet implemented    NYI
    ${invalid_xsd_path} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_05/05_invalid_schema.xsd
    ${status}    ${error}=    Run Keyword And Ignore Error    Import Library    xmlvalidator    ${invalid_xsd_path}    AS    ${TEST NAME}
    Should Be Equal    ${status}    FAIL
    Should Contain    ${error}    Initializing library 'xmlvalidator' with arguments [ ${EXECDIR}/test/_data/integration/TC_05/05_invalid_schema.xsd ] failed: SystemError: Loading of schema failed: {'XMLSchemaValidationError': ParseError('mismatched tag: line 8, column 2')}

06_ImportLibrary_Multiple_XSDs
    [Documentation]    Attempt to import the XmlValidator library with 
    ...                multiple XSD files and verify the informative 
    ...                and structured error message that the library 
    ...                constructs and returns.
    ${xsd_folder} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_06/
    Run Keyword And Expect Error    * ValueError: Got multiple xsd files: *    Import Library    xmlvalidator    ${xsd_folder}    AS    ${TEST NAME}