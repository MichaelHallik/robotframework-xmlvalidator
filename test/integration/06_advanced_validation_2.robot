*** Settings ***
Documentation    Tests XML validation functionality by demonstrating and 
...              validating various approaches and use cases.
Library    Collections
Library    xmlvalidator    ${EXECDIR}/test/_data/integration/TC_26/schema.xsd    #    base_url    error_facets
Resource    ${EXECDIR}/test/integration/validation_keywords.resource
Suite Teardown    Default Test Suite Teardown
Variables    teardown_vars.py


*** Variables ***
# ${DELETE_CSV} determines deletion of the csv output files; values can be:
# - bool ${False}:    no delete at all
# - bool ${True}:     delete the one csv, as generated in current test case run
# - str 'All':        delete all csv files present in test case data folder
# ${DELETE_CSV}=    all
# ${RESET_SCHEMA}=    ${True}


*** Test Cases ***
26_Validation_With_Init_Schema
    [Documentation]    Validates that the schema as passed during 
    ...                library import is correctly loaded.
    ...    
    ...                Subsequently validates various XML files (located 
    ...                in a folder) against the loaded schema.
    ...    
    ...                Finally, validates that the keyword has correctly 
    ...                identified, collected and reported (returned) all 
    ...                errors that are to be expected and that, 
    ...                moreover, the errors have also been written to a 
    ...                CSV file.
    # Setup test variables.
    ${xml_folder} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_26
    # Validate the init schema is loaded.
    ${cur_schema}=    Get Schema
    Should be equal    ${cur_schema}    schema.xsd
    # Validate the XML files against the init XSD.
    ${errors}    ${csv_path} =    Validate Xml Files    ${xml_folder}
    # Define the expected results/errors.
    ${expected_errors_1} =    Create Dictionary    
    ...                        file_name=invalid_01.xml
    ...                        path=/Person/Age
    ...                        reason=invalid literal for int() with base 10: 'thirty'
    ${expected_errors_2} =    Create Dictionary    
    ...                        file_name=invalid_02.xml
    ...                        path=/Person
    ...                        reason=Unexpected child with tag 'Phone' at position 2. Tag 'Age' expected.
    ${expected_errors_3} =    Create Dictionary    
    ...                        file_name=invalid_02.xml
    ...                        path=/Person
    ...                        reason=Unexpected child with tag 'ExtraElement' at position 4.
    # Validate the validation results are as expected.
    Validate Xml Validation Results    ${errors}    ${expected_errors_1}    ${expected_errors_2}    ${expected_errors_3}
    # Validate the CSV output.
    Validate CSV    ${csv_path}    ${expected_errors_1}    ${expected_errors_2}    ${expected_errors_3}
    # Teardown.
    ${xml_validator} =    Get Library Instance    xmlvalidator
    [Teardown]    Default Test Case Teardown    ${csv_path}    ${DELETE_CSV}    ${xml_validator}    xmlvalidator    reset_schema=${RESET_SCHEMA}

27_Various_Ways_To_Load_Schemas_01
    [Documentation]    Optionally validates that the schema (as active 
    ...                at the end of the previous test case) is (still) 
    ...                correctly loaded.
    ...    
    ...                Subsequently validates various XML files (located 
    ...                in a folder), passing a new schema file (located 
    ...                in a seperate/different folder) directly to the 
    ...                keyword (replacing the previously active schema).
    ...                Since all XML files are actually valid, the only 
    ...                validation applied to the result of the action 
    ...                is to ensure that the new schema has, indeed, 
    ...                replaced the previously active schema.
    ...    
    ...                Finally, a second set of XML files (located in 
    ...                yet another folder) is being validated, by 
    ...                passing the XML folder path as xsd_path to the 
    ...                keyword. This will load a schema file that is 
    ...                located in that folder, provided there is only 
    ...                one such schema file present.
    ...                Since all XML files are valid, it is then only 
    ...                validated that the new schema has successfully 
    ...                replaced the previous schema.
    # Validate the init schema is (still) loaded.
    IF    not ${RESET_SCHEMA}
        ${cur_schema}=    Get Schema
        Should be equal    ${cur_schema}    schema.xsd
    END
    # Pass an XSD file (path) to the keyword and validate XMLs in a seperate folder.
    ${errors}    ${csv_path} =    Validate Xml Files    
    ...                           ${EXECDIR}/test/_data/integration/TC_27
    ...                           xsd_path=${EXECDIR}/test/_data/integration/TC_27/xsd/schema_01.xsd
    # Validate the new schema is loaded.
    ${cur_schema}=    Get Schema
    Should be equal    ${cur_schema}    schema_01.xsd
    # Pass the XML folder path also as XSD path.
    ${xml_folder}=    Set Variable    ${EXECDIR}/test/_data/integration/TC_27/xml_folder
    ${errors}    ${csv_path} =    Validate Xml Files    
    ...                           ${xml_folder}   
    ...                           xsd_path=${xml_folder}
    # Validate the correct schema is loaded.
    ${cur_schema}=    Get Schema
    Should be equal    ${cur_schema}    schema_02.xsd
     # Teardown.
    ${xml_validator} =    Get Library Instance    xmlvalidator
    [Teardown]    Default Test Case Teardown    ${csv_path}    ${DELETE_CSV}    ${xml_validator}    xmlvalidator    reset_schema=${RESET_SCHEMA}

28_Various_Ways_To_Load_Schemas_02 
    [Documentation]    Optionally validates that the schema (as active 
    ...                at the end of the previous test case) is (still) 
    ...                correctly loaded.
    ...    
    ...                Subsequently validates various XML files (located 
    ...                in a folder), without expicitly passing an 
    ...                xsd_path. Rather, the XML files are 
    ...                mapped to their respective XSD files (located in 
    ...                the same folder) dynamically, by file name 
    ...                matching. The latter is triggered by passing the 
    ...                ``xsd_search_strategy`` argument as 
    ...                'by_filename' to the keyword, next to the XML 
    ...                folder path.
    ...                The results of the validation are subsequently 
    ...                thoroughly validated in terms of completeness and 
    ...                correctness.
    ...    
    ...                Subsequently a second batch of XML files is 
    ...                validated in the same fashion. However, this time 
    ...                the XSD files reside in their own folder, 
    ...                different from the folder where the XML files are 
    ...                located.
    ...                Since all XML files are valid, only the correct 
    ...                setting schemas is validated.
    [Tags]    git-exclude
    # Validate the schema from the previous test case is (still) loaded.
    IF    not ${RESET_SCHEMA}
        ${cur_schema}=    Get Schema
        Should be equal    ${cur_schema}    schema_02.xsd
    END
    # Pass no XSD file path, but provide a matching strategy (XSDs assumed to be in XML folder).
    ${errors}    ${csv_path} =    Validate Xml Files    
    ...                           ${EXECDIR}/test/_data/integration/TC_28
    ...                           xsd_search_strategy=by_filename
    # Validate the new schema is loaded.
    ${cur_schema}=    Get Schema
    Should be equal    ${cur_schema}    file_4.xsd
    # Define the errors that the library should identify, collect and report/return.
    ${expected_errors_1} =    Create Dictionary    
    ...                        file_name=file_1.xml
    ...                        path=/Person/Age
    ...                        reason=invalid literal for int() with base 10: 'ABC'
    ${expected_errors_2} =    Create Dictionary    
    ...                        file_name=file_5.xml
    ...                        reason=No matching XSD found for: file_5.
    ${expected_errors_3} =    Create Dictionary    
    ...                        file_name=file_6.xml
    ...                        reason=No matching XSD found for: file_6.
    # Validate the validation results are as expected.
    Validate Xml Validation Results    ${errors}    ${expected_errors_1}    ${expected_errors_2}    ${expected_errors_3}
    # Validate the CSV output.
    Validate CSV    ${csv_path}    ${expected_errors_1}    ${expected_errors_2}    ${expected_errors_3}
    # Pass a seperate XSD folder path, but also a search strategy.
    ${errors}    ${csv_path} =    Validate Xml Files    
    ...                           ${EXECDIR}/test/_data/integration/TC_28/xml
    ...                           xsd_path=${EXECDIR}/test/_data/integration/TC_28/xsd
    ...                           xsd_search_strategy=by_filename
    # Validate the new schema is loaded.
    ${cur_schema}=    Get Schema
    Should be equal    ${cur_schema}    file_9.xsd
     # Teardown.
    ${xml_validator} =    Get Library Instance    xmlvalidator
    [Teardown]    Default Test Case Teardown    ${csv_path}    ${DELETE_CSV}    ${xml_validator}    xmlvalidator    reset_schema=${RESET_SCHEMA}

29_Various_Ways_To_Load_Schemas_03
    [Documentation]    Optionally validates that the schema (as active 
    ...                at the end of the previous test case) is (still) 
    ...                correctly loaded.
    ...    
    ...                Subsequently validates various XML files (located 
    ...                in a folder), without expicitly passing an 
    ...                xsd_path. Rather, the XML files are 
    ...                mapped to their respective XSD files (located in 
    ...                the same folder) dynamically, by namespace 
    ...                matching. The latter is triggered by passing the 
    ...                ``xsd_search_strategy`` argument as 
    ...                'by_name_space' to the keyword, next to the XML 
    ...                folder path.
    ...    
    ...                In total, 21 invalid files will be reported as 
    ...                invalid, either because of (1) XSD violation, 
    ...                (2) malformedness or (3) because of not matching 
    ...                any XSD.
    ...    
    ...                Of the 21 errors that the library will identify, 
    ...                collect and report, only three will be validated 
    ...                for correctness. since there have been plenty 
    ...                validations throughout the various integration 
    ...                test suites already. You can inspect the log to 
    ...                see the various XSD violations and other types of 
    ...                errors that the library reports.
    ...    
    ...                Bascially, there are three XSD files and for each 
    ...                XSD file there are three XML files that violate 
    ...                the XSD and three XML files that do not violate 
    ...                the schema, but are malformed. The latter will be 
    ...                catched and reported by the library as well!
    ...                Finally, there are three XML files that do not 
    ...                match with any of the three schema files and will 
    ...                therefore be reported as such, by the library.
    # Validate the schema from the previous test case is (still) loaded.
    IF    not ${RESET_SCHEMA}
        ${cur_schema}=    Get Schema
        Should be equal    ${cur_schema}    schema_02.xsd
    END
    # Pass no XSD file path, but provide a matching strategy: XSDs assumed to be in XML folder.
    ${errors}    ${csv_path} =    Validate Xml Files    
    ...                           ${EXECDIR}/test/_data/integration/TC_29
    ...                           xsd_search_strategy=by_name_space
    # Validate the expected schema is loaded.
    ${cur_schema}=    Get Schema
    Should Be Equal    ${cur_schema}    schema3.xsd
    # Define the expected validation results.
    ${expected_errors_1} =    Create Dictionary    
    ...                        file_name=schema1_invalid_1.xml
    ...                        path=/Employee/ID
    ...                        reason=invalid literal for int() with base 10: 'ABC'
    ${expected_errors_2} =    Create Dictionary    
    ...                        file_name=schema1_malformed_1.xml
    ...                        path=
    ...                        reason=Premature end of data in tag Employee line 1, line 1, column 11
    ${expected_errors_3} =    Create Dictionary    
    ...                        reason=No matching XSD found for: unmatched_1.
    # Validate the validation results are as expected.
    Validate Xml Validation Results    ${errors}    ${expected_errors_1}    ${expected_errors_2}    ${expected_errors_3}
    # Teardown.
    ${xml_validator} =    Get Library Instance    xmlvalidator
    [Teardown]    Default Test Case Teardown    ${csv_path}    ${DELETE_CSV}    ${xml_validator}    xmlvalidator    reset_schema=${RESET_SCHEMA}

30_Error_Facets
    [Documentation]    This test case passes custom (non-default) error 
    ...                facets to the Validate Xml Files keywords.
    ...    
    ...                Error facets determine which attributes of a 
    ...                parse error or an XmlSchema (validation) error 
    ...                are collected and reported by the keyword.
    ...    
    ...                Error facets can also be passed during library 
    ...                import. Passing error facets to the keyword 
    ...                overrules these default facets. However, the next 
    ...                time the keyword ios called without passing 
    ...                error_facets, the default facets apply again. 
    ...    
    ...                The validations errors that are reported/returned 
    ...                in this test case will not be validated. Instead, 
    ...                each error is logged, including the data type of 
    ...                the error facet (e.g. string or 
    ...                xml.etree.ElementTree.Element).
    # Specify error facets.
    @{new_error_facets}=    Create List    message    elem    namespaces
    # Pass non-default error facets; pass no XSD file path, but provide a matching strategy (XSDs are assumed to reside in the XML folder).
    ${errors}    ${csv_path} =    Validate Xml Files    
    ...                           ${EXECDIR}/test/_data/integration/TC_30
    ...                           xsd_search_strategy=by_name_space
    ...                           error_facets=${new_error_facets}
    # Let's see what's inside the collected errors/violations.
    FOR    ${idx}    ${error}    IN ENUMERATE    @{errors}
        Log    ==================================== Inspecting error #${idx}    level=WARN
        FOR    ${key}    ${value}    IN    &{error}
            Log    Error facet '${key}': ${value} (${{ type( $value ) }})    level=WARN
        END
        IF    ${idx} == 5
            BREAK
        END
    END
    # Validate the new schema is loaded.
    ${cur_schema}=    Get Schema
    Should Be Equal    ${cur_schema}    schema3.xsd
    # Teardown.
    ${xml_validator} =    Get Library Instance    xmlvalidator
    [Teardown]    Default Test Case Teardown    ${csv_path}    ${DELETE_CSV}    ${xml_validator}    xmlvalidator    reset_schema=${RESET_SCHEMA}

31_Validation_Passing_XSD_Path_With_Include
    [Documentation]    Validate multiple XML files against an XSD with 
    ...                an included XSD.
    ...    
    ...                This ensures that XSD imports/includes are 
    ...                correctly handled.
    ...    
    ...                The Validate Xml Keyword will validate three XML 
    ...                files against the loaded schema:
    ...    
    ...                - one file will be deemed valid
    ...                - one file will be deemed invalid on account of 
    ...                  violating the main XSD schema
    ...                - one file will be deemed invalid on account of 
    ...                  violating the included XSD schema
    # Set up test variables.
    ${xml_folder} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_31/xml
    ${xsd_path} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_31/main_schema.xsd
    ${base_url} =    Set Variable    ${EXECDIR}/test/_data/integration/TC_31
    # Validate XML files, passing also a base_url to be used when constructing the schema object.
    ${result}    ${csv_path} =    Validate Xml Files    ${xml_folder}    xsd_path=${xsd_path}    base_url=${base_url}
    # Validate the schema has been loaded without problems.
    ${cur_schema}=    Get Schema
    Should be equal    ${cur_schema}    main_schema.xsd
    # Expected validation results
    ${expected_result_1} =    Create Dictionary    
    ...                        file_name=invalid_by_include.xml
    ...                        path=/Person/PhoneNumber
    ...                        reason=value doesn't match any pattern of ['\\\\d{3}-\\\\d{3}-\\\\d{4}']
    ${expected_result_2} =    Create Dictionary    
    ...                        file_name=invalid_by_main.xml
    ...                        path=/Person
    ...                        reason=Unexpected child with tag '{http://example.com/my_namespace}PhoneNumber' at position 1. Tag '{http://example.com/my_namespace}Name' expected.
    # Validate structured results
    Validate Xml Validation Results    ${result}    ${expected_result_1}    ${expected_result_2}
    # Validate CSV output
    Validate CSV    ${csv_path}    ${expected_result_1}    ${expected_result_2}
    # Teardown.
    ${xml_validator} =    Get Library Instance    xmlvalidator
    [Teardown]    Default Test Case Teardown    ${csv_path}    ${DELETE_CSV}    ${xml_validator}    xmlvalidator    reset_schema=${RESET_SCHEMA}