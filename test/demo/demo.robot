*** Settings ***
Library    xmlvalidator    ${EXECDIR}/test/_data/demo/TC_01/schema.xsd    # base_url    error_facets


*** Test Cases ***
TC_01
    # Validate XML files using the init schema - assign return tuple.
    ${errors}    ${csv_path} =    Validate Xml Files    ${EXECDIR}/test/_data/demo/TC_01
    # Do something with the return if ever needed.

TC_02
    # Load a new schema - XSD file resides in XML folder (auto-detect).
    ${target_folder}=    Set Variable    ${EXECDIR}/test/_data/demo/TC_02
    Validate Xml Files    ${target_folder}    xsd_path=${target_folder}

TC_03
    # Load a new schema - XSD file resides in separate folder (file name optional).
    Validate Xml Files    ${EXECDIR}/test/_data/demo/TC_03/xml_folder
    ...                   xsd_path=${EXECDIR}/test/_data/demo/TC_03/xsd

TC_04
    # Dynamic XML/XSD mapping - by filename - one folder.
    Validate Xml Files    ${EXECDIR}/test/_data/demo/TC_04
    ...                   xsd_search_strategy=by_filename
    
TC_05
    # Dynamic XML/XSD mapping - by filename - separate folders.
    Validate Xml Files    ${EXECDIR}/test/_data/demo/TC_05/xml
    ...                   xsd_path=${EXECDIR}/test/_data/demo/TC_05/xsd
    ...                   xsd_search_strategy=by_filename

TC_06
    # Dynamic XML/XSD mapping - by namespace.
    Validate Xml Files    ${EXECDIR}/test/_data/demo/TC_06
    ...                   xsd_search_strategy=by_name_space

TC_07
    # Custom error facets.
    @{new_error_facets}=    Create List    message    elem    namespaces    validator
    Validate Xml Files    ${EXECDIR}/test/_data/demo/TC_07
    ...                   xsd_search_strategy=by_name_space
    ...                   error_facets=${new_error_facets}

TC_08
    # Passing a base_url to be used for includes when constructing the schema object.
    Validate Xml Files    ${EXECDIR}/test/_data/demo/TC_08/xml    
    ...                   xsd_path=${EXECDIR}/test/_data/demo/TC_08/main_schema.xsd
    ...                   base_url=${EXECDIR}/test/_data/demo/TC_08