*** Settings ***
Documentation    Tests XML validation functionality by demonstrating and 
...              validating various approaches and use cases.
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
23_Validate_Batch_Single_XSD_Import
    [Documentation]    Validate multiple XML files against a single XSD 
    ...                file.
    ...
    ...                The XSD file is in a different folder from the XML 
    ...                files.
    ...    
    ...                The XSD path is passed during library 
    ...                instantiation.
    # Set up test variables.
    ${xml_folder} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_23/xml/
    ${xsd_path} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_23/xsd/23_schema.xsd
    # Import the library with the XSD path specified.
    Import Library    xmlvalidator    ${xsd_path}    AS    ${TEST_NAME}
    # Validate the XML files.
    ${errors}    ${csv_path}=    Run Keyword    ${TEST_NAME}.Validate Xml Files    ${xml_folder}
    # Define the expected results/errors.
    ${expected_error_1} =    Create Dictionary    
    ...                        file_name=23_invalid_1.xml
    ...                        path=/root/value
    ...                        reason=invalid literal for int() with base 10: 'NotANumber'
    ${expected_error_2} =    Create Dictionary    
    ...                        file_name=23_invalid_2.xml
    ...                        path=/root
    ...                        reason=Unexpected child with tag 'wrongChild' at position 2. Tag 'child' expected.
    ${expected_error_3} =    Create Dictionary    
    ...                        file_name=23_invalid_3.xml
    ...                        path=/root/data/item
    ...                        reason=value doesn't match any pattern of ['[\\\\i-[:]][\\\\c-[:]]*']
    # Validate the validation results are as expected.
    Validate Xml Validation Results    ${errors}    ${expected_error_1}    ${expected_error_2}    ${expected_error_3}
    # Validate the CSV output.
    Validate CSV    ${csv_path}    ${expected_error_1}    ${expected_error_2}    ${expected_error_3}
    # Teardown.
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    [Teardown]    Default Test Case Teardown    ${csv_path}    ${DELETE_CSV}    ${xml_validator}    ${TEST NAME}

24_Validate_Batch_Single_XSD_Keyword_Call
    [Documentation]    Validate multiple XML files against a single XSD 
    ...                file.
    ...
    ...                The XSD file is in a different folder from the XML 
    ...                files.
    ...
    ...                The XSD path is NOT passed during library 
    ...                instantiation, but with the keyword call.
    # Set up test variables.
    ${xml_folder} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_24/xml/
    ${xsd_path} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_24/xsd/24_schema.xsd
    # Import the library.
    Import Library    xmlvalidator    AS    ${TEST_NAME}
    # Validate the XML files.
    ${errors}    ${csv_path}=    Run Keyword    ${TEST_NAME}.Validate Xml Files    ${xml_folder}    ${xsd_path}
    # Define the expected results/errors.
    ${expected_error_1} =    Create Dictionary    
    ...                        file_name=24_invalid_1.xml
    ...                        path=/root/value
    ...                        reason=invalid literal for int() with base 10: 'NotANumber'
    ${expected_error_2} =    Create Dictionary    
    ...                        file_name=24_invalid_2.xml
    ...                        path=/root
    ...                        reason=Unexpected child with tag 'wrongChild' at position 2. Tag 'child' expected.
    ${expected_error_3} =    Create Dictionary    
    ...                        file_name=24_invalid_3.xml
    ...                        path=/root/data/item
    ...                        reason=value doesn't match any pattern of ['[\\\\i-[:]][\\\\c-[:]]*']
    # Validate the validation results are as expected.
    Validate Xml Validation Results    ${errors}    ${expected_error_1}    ${expected_error_2}    ${expected_error_3}
    # Validate the CSV output.
    Validate CSV    ${csv_path}    ${expected_error_1}    ${expected_error_2}    ${expected_error_3}
    # Teardown.
    ${xml_validator} =    Get Library Instance    ${TEST NAME}
    [Teardown]    Default Test Case Teardown    ${csv_path}    ${DELETE_CSV}    ${xml_validator}    ${TEST NAME}

25_Validate_Batch_Single_XSD_By_Filename
    [Documentation]    Validate multiple XML files against multiple XSD 
    ...                file, dynamically matching XML/XSD files, based 
    ...                on the filename matching strategy.
    ...                
    ...                The XSD file resides in the same folder as the XML 
    ...                files.
    ...    
    ...                No XSD path is provided, but the keyword is 
    ...                called with: xsd_search_strategy=by_file_name.
    # Set up test variables.
    ${xml_folder} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_25/
    # Import the library.
    Import Library    xmlvalidator    AS    ${TEST_NAME}
    # Validate the XML files, passing an xsd_search_strategy, but not passing an xsd_path.
    ${errors}    ${csv_path} =    Run Keyword    ${TEST_NAME}.Validate Xml Files    ${xml_folder}    xsd_search_strategy=by_file_name
    # Define the expected results/errors.
    ${expected_errors_1} =    Create Dictionary    
    ...                        file_name=25_invalid_1.xml
    ...                        path=/root/value
    ...                        reason=invalid literal for int() with base 10: 'NotANumber'
    ${expected_errors_2} =    Create Dictionary    
    ...                        file_name=25_invalid_2.xml
    ...                        path=/root
    ...                        reason=Unexpected child with tag 'wrongChild' at position 2. Tag 'child' expected.
    ${expected_errors_3} =    Create Dictionary    
    ...                        file_name=25_no_match_1.xml
    ...                        reason=No matching XSD found for: 25_no_match_1.
    ${expected_errors_4} =    Create Dictionary    
    ...                        file_name=25_no_match_2.xml
    ...                        reason=No matching XSD found for: 25_no_match_2.
    # Validate the validation results are as expected.
    Validate Xml Validation Results    ${errors}    ${expected_errors_1}    ${expected_errors_2}    ${expected_errors_3}    ${expected_errors_4}
    # Validate the CSV output.
    Validate CSV    ${csv_path}    ${expected_errors_1}    ${expected_errors_2}    ${expected_errors_3}    ${expected_errors_4}
    # Teardown.
    ${xml_validator} =    Get Library Instance    ${TEST_NAME}
    [Teardown]    Default Test Case Teardown    ${csv_path}    ${DELETE_CSV}    ${xml_validator}    ${TEST_NAME}