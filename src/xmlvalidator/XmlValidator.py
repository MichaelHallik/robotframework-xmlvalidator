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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.


"""
This module defines the `XmlValidator` class — a Robot Framework test 
library for validating XML files against XSD schemas using the 
`xmlschema` library.

The validator supports both individual and batch validation workflows, 
with comprehensive error reporting and optional export to structured 
CSV files.

Key Features:

- Validation of a single XML file against a specified schema.
- Batch validation of multiple XML files in a folder, using:
  - A single shared schema.
  - Dynamic schema matching by namespace or file name.
- Detailed error reporting for validation failures.
- Namespace-aware validation for strict conformance.
- Graceful handling of malformed XML or XSD files.
- Optional export of all collected errors to a CSV file.

This module is intended to be imported by Robot Framework test suites 
or executed as a Python module via a direct call.
"""


# pylint: disable=C0103:invalid-name      # On account of the module name, that is not snake-cased (required by Robot Framework).
# pylint: disable=C0302:too-many-lines    # On account of the extensive docstrings and annotations.
# pylint: disable=C0301:line-too-long     # On account of tables in docstrings.


# Standard library imports.
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple
# Third party library imports.
from lxml import etree
from robot.api import Failure, logger
from robot.api.deco import keyword, library
from xmlschema import XMLSchema
# Local application imports.
from .xml_validator_results import ValidatorResultRecorder, ValidatorResult
from .xml_validator_utils import ValidatorUtils


@library(scope='GLOBAL')
class XmlValidator:
    """
    XmlValidator is a `Robot Framework <https://robotframework.org/>`_ 
    test library for validating XML files against XSD schemas.

    The library leverages the power of the 
    `xmlschema library <https://pypi.org/project/xmlschema/>`_ and is 
    designed for both single-file and batch XML validation workflows.

    It provides structured and detailed reporting of XML parse errors 
    (malformed XML content) and XSD violations, schema auto-detection 
    and CSV exports of collected errors.

    Features are described in detail on the `project repo's landing page. 
    <https://github.com/MichaelHallik/robotframework-xmlvalidator>`_.

    **Overview**
    
    The main keyword is ``Validate Xml Files``.
    
    The other keywords are convenience/helper functions, e.g. ``Reset 
    Error Facets``.

    The ``Validate Xml Files`` validates one or more XML files against one 
    or more XSD schema files and collects and reports all encountered 
    errors.

    The type of error that the keyword can detect is not limited to XSD 
    violations, but may also pertain to malformed XML files (e.g. parse 
    errors), empty files, unmatched XML files (no XSD match found) and 
    others.

    Errors that result from malformed XML files or from XSD violations 
    support detailed error reporting. Using the ``error_facets`` argument 
    you may specify the details the keyword should collect and report 
    about captured errors.

    When operating in batch mode, the ``Validate Xml Files`` keyword 
    always validates the entire set of passed XML files. That is, when 
    it encounters an error in a file, it does not simply fail. Rather, 
    it collects the error details (as determined by the error_facets 
    arg) and then continues validating the current file as well as any 
    subsequent file(s).

    In that fashion the keyword works through the entire set of files.

    When having finished checking the last file, it will log a summary 
    of the test run and then proceed to report all collected errors in 
    the console, in the RF log and, optionally, in the form of a CSV 
    file.

    **Batch mode & dynamic XSD matching**

    The ``Validate Xml Files`` keyword supports validating a single, 
    individual XML file against an XSD schema. It also supports batch 
    flows, by being able to validate multiple XML files in a specified 
    folder against one or more XSD schema files. These XSD files may 
    either reside in the same folder (as the XML files) or in a 
    different folder.
    
    In the latter case (i.e. when multiple schema files are 
    involved) XML files are matched dynamically to XSD files, supporting 
    either a 'by filename' strategy or a 'by namespace strategy'.

    That means you can simply pass the paths to a folder containing 
    XML files and to a folder containing XSD files and the library 
    will determine which XSD schema file to use for each XML file. 

    If the XML and XSD files reside in the same folder, you only 
    have to pass one folder path and the library will dynamically pair 
    each XML file with the relevant XSD schema file. 
    
    When no matching XSD schema could be identified for an XML file, 
    this will be integrated into the error reporting (the keyword will 
    not fail).

    As mentioned earlier, you may also refer to specific XML/XSD files 
    (instead of to folders). In that case, no matching will be 
    attempted, but the library will simply try to validate the specified 
    XML file against the specified XSD file.

    **Schema pre-loading**

    The library supports loading a schema by specifying an ``xsd_path`` 
    when importing the library in a Robot Framework test suite. The 
    preloaded schema is then reused for all validations until 
    overridden at the test case level. 

    **Comprehensive, robust and flexible error reporting**

    - Captures XSD schema violations.

     - Missing required elements.
     - Cardinality constraints.
     - Datatype mismatches (e.g., invalid `xs:dateTime`).
     - Pattern and enumeration violations.
     - Namespace errors.
     - Etc.

    - Captures malformed XML.
    - Handles edge cases like empty files or XML files that could not be 
      matched to an XSD schema file.
    - Does not fail on errors, but collects encountered errors in all 
      files and reports them in a structured format in the console and 
      RF log.
    - Supports specifying the details that should be collected for 
      encountered errors.
    - Optionally exports the error report to a CSV file, providing the 
      file name next to all error details for traceability.
    
    **Customizing error collection**

    Use the ``error_facets`` argument to control which attributes of 
    detected errors will be collected and reported. E.g. the element 
    locator (XPath), error message, involved namespace and/or the XSD 
    validator that failed.

    Error facets can be set by passing a list of one or more error 
    facets, either with the library import and/or on the test case 
    level (i.e. when calling the ``Validate XML Files`` keyword).

    These are the facets (or attributes) that can be collected and 
    reported for each encountered error:

    +---------------+----------------------------------------------------------------------------+
    | Facet         | Description                                                                |
    +===============+============================================================================+
    | ``message``   | A human-readable message describing the validation error.                  |
    +---------------+----------------------------------------------------------------------------+
    | ``path``      | The XPath location of the error in the XML document.                       |
    +---------------+----------------------------------------------------------------------------+
    | ``domain``    | The domain of the error (e.g., "validation").                              |
    +---------------+----------------------------------------------------------------------------+
    | ``reason``    | The reason for the error, often linked to XSD constraint violations.       |
    +---------------+----------------------------------------------------------------------------+
    | ``validator`` | The XSD component (e.g., element, attribute, type) that failed validation. |
    +---------------+----------------------------------------------------------------------------+
    | ``schema_path`` | The XPath location of the error in the XSD schema.                       |
    +---------------+----------------------------------------------------------------------------+
    | ``namespaces`` | The namespaces involved in the error (if applicable).                     |
    +---------------+----------------------------------------------------------------------------+
    | ``elem``      | The XML element that caused the error (``ElementTree.Element``).           |
    +---------------+----------------------------------------------------------------------------+
    | ``value``     | The invalid value that triggered the error.                                |
    +---------------+----------------------------------------------------------------------------+
    | ``severity``  | The severity level of the error (not always present).                      |
    +---------------+----------------------------------------------------------------------------+
    | ``args``      | The arguments passed to the error message formatting.                      |
    +---------------+----------------------------------------------------------------------------+

    For each error that is encountered, the selected error facet(s) will 
    be collected and reported.

    Error facets passed during library initialization will be overruled 
    by error facets that are passed at the test case level, when calling 
    the ``Validate Xml Files`` keyword.

    The values you can pass through the `error_facets` argument are 
    based on the attributes of the error objects as returned by the 
    XMLSchema.iter_errors() method, that is provided by the xmlschema 
    library and the the xmlvalidator library leverages. Said method 
    yields instances of 
    xmlschema.validators.exceptions.XMLSchemaValidationError (or its 
    subclasses), each representing a specific validation issue 
    encountered in an XML file. These error objects expose various 
    attributes that describe the nature, location, and cause of the 
    problem.

    The table lists the most commonly available attributes, though 
    additional fields may be available depending on the type of 
    validation error.

    **Support for XSD includes/imports**

    Enables resolution of schema imports/includes via a custom base URL, 
    via the ``base_url`` arg.

    Use ``base_url`` when your XSD uses <xs:include> or <xs:import> with 
    relative paths.

    You can pass ``base_url`` with the library import (together with 
    passing ``xsd_path``) and/or when calling ``Validate Xml Files`` 
    with ``xsd_path``.

    ** Optional test case fail **

    The ``Validate Xml Files`` keyword collects one or more errors for 
    one or more XML files. As mentioned earlier, the keyword is designed 
    so as to not fail upon encountering errors.

    However, in case you want your test case to fail when one or more 
    errors have been detected, you can use the ``fail_on_errors`` (bool)
    argument to make it so. It defaults to ${False}.

    **Basic usage examples**

    For a comprehensive set of example test cases, please see the 
    `Robot Framework integration tests <https://github.com/MichaelHallik/robotframework-xmlvalidator/tree/main/test/integration/>`_ 
    in the projects GitHub repository.

    The repo contains a 
    `structured overview of all implemented tests <https://github.com/MichaelHallik/robotframework-xmlvalidator/blob/main/test/_doc/integration/overview.html>`_
    per topic (e.g. library import, schema matching strategies, etc.).

    It further contains a detailed instruction on 
    `how to run Robot Framework tests <https://github.com/MichaelHallik/robotframework-xmlvalidator/blob/main/test/_doc/integration/README.md>`_.

	.. code:: robotframework

		*** Settings ***
		Library    XmlValidator    xsd_path=path/to/default/schema.xsd

		*** Variables ***
		${SINGLE_XML_FILE}                path/to/file1.xml
		${FOLDER_MULTIPLE_XML}            path/to/xml_folder_1
		${FOLDER_MULTIPLE_XML_ALT}        path/to/xml_folder_2
		${FOLDER_MULTIPLE_XML_NS}         path/to/xml_folder_3
		${FOLDER_MULTIPLE_XML_FN}         path/to/xml_folder_4

		${SINGLE_XSD_FILE}                path/to/alt_schema.xsd
		${FOLDER_MULTIPLE_XSD}            path/to/xsd_schemas/

		*** Test Cases ***

		Validate Single XML File With Default Schema
			[Documentation]    Validates a single XML file using the default schema
			Validate Xml Files    ${SINGLE_XML_FILE}

		Validate Folder Of XML Files With Default Schema
			[Documentation]    Validates all XML files in a folder using the default schema
			Validate Xml Files    ${FOLDER_MULTIPLE_XML}

		Validate Folder With Explicit Schema Override
			[Documentation]    Validates XML files using a different, explicitly provided schema
			Validate Xml Files    ${FOLDER_MULTIPLE_XML_ALT}    ${SINGLE_XSD_FILE}

		Validate Folder With Multiple Schemas By Namespace
			[Documentation]    Resolves matching schema for each XML file based on namespace
			Validate Xml Files    ${FOLDER_MULTIPLE_XML_NS}    ${FOLDER_MULTIPLE_XSD}    xsd_search_strategy=by_namespace

		Validate Folder With Multiple Schemas By File Name
			[Documentation]    Resolves schema based on matching file name patterns (no schema path passed)
			Validate Xml Files    ${FOLDER_MULTIPLE_XML_FN}    xsd_search_strategy=by_file_name
    
    Example of the console output where some files passed validation and 
    multiple errors have been found for multiple other files:

    .. code:: console

        Schema 'schema.xsd' set.
        Collecting error facets: ['path', 'reason'].
        XML Validator ready for use!
        ==============================================================================
        01 Advanced Validation:: Demo XML validation
        Mapping XML files to schemata by namespace.
        Validating 'valid_1.xml'.
            XML is valid!
        Validating 'valid_2.xml'.
            XML is valid!
        Validating 'valid_3.xml'.
            XML is valid!
        Validating 'xsd_violations_1.xml'.
        Setting new schema file: C:\\Projects\\robotframework-xmlvalidator\\test\\_data\\integration\\TC_01\\schema1.xsd. 
        [ WARN ]    XML is invalid:
        [ WARN ]        Error #0:
        [ WARN ]            path: /Employee
        [ WARN ]            reason: Unexpected child with tag '{http://example.com/schema1}FullName' at position 2. Tag '{http://example.com/schema1}Name' expected.
        [ WARN ]        Error #1:
        [ WARN ]            path: /Employee/Age
        [ WARN ]            reason: invalid literal for int() with base 10: 'Twenty Five'
        [ WARN ]        Error #2:
        [ WARN ]            path: /Employee/ID
        [ WARN ]            reason: invalid literal for int() with base 10: 'ABC'
        Validating 'valid_.xml_4'.
            XML is valid!
        Validating 'valid_.xml_5'.
            XML is valid!
        Validating 'malformed_xml_1.xml'.
        [ WARN ]    XML is invalid:
        [ WARN ]        Error #0:
        [ WARN ]            reason: Premature end of data in tag Name line 1, line 1, column 37 (file:/C:/Projects/robotframework-xmlvalidator/test/_data/integration/TC_01/malformed_xml_1.xml, line 1)
        [ WARN ]        Error #1:
        [ WARN ]            reason: Opening and ending tag mismatch: ProductID line 1 and Product, line 1, column 31 (file:/C:/Projects/robotframework-xmlvalidator/test/_data/integration/TC_01/malformed_xml_1.xml, line 1)
        Validating 'xsd_violations_2.xml'.
        Setting new schema file: C:\\Projects\\robotframework-xmlvalidator\\test\\_data\\integration\\TC_01\\schema2.xsd.
        [ WARN ]    XML is invalid:
        [ WARN ]        Error #0:
        [ WARN ]            path: /Product/Price
        [ WARN ]            reason: invalid value '99.99USD' for xs:decimal
        [ WARN ]        Error #1:
        [ WARN ]            path: /Product
        [ WARN ]            reason: The content of element '{http://example.com/schema2}Product' is not complete. Tag '{http://example.com/schema2}Price' expected.
        Validating 'valid_.xml_6'.
            XML is valid!
        Validating 'no_xsd_match_1.xml'.
        [ WARN ]    XML is invalid:
        [ WARN ]        Error #0:
        [ WARN ]            reason: No matching XSD found for: no_xsd_match_1.xml.
        Validating 'no_xsd_match_2.xml'.
        [ WARN ]    XML is invalid:
        [ WARN ]        Error #0:
        [ WARN ]            reason: No matching XSD found for: no_xsd_match_2.xml.
        Validation errors exported to 'C:\\test\\01_Advanced_Validation\\errors_2025-03-29_13-54-46-552150.csv'.
        Total_files validated: 11.
        Valid files: 6.
        Invalid files: 5
        01 Advanced Validation:: Demo XML validation | PASS |
        21 errors have been detected.
        ========================================================
        01 Advanced Validation:: Demo XML validation | PASS |
        1 test, 1 passed, 0 failed

    In case ``fail_on_errors`` is True, the console output will look like this:

    .. code:: console

        Validation errors exported to 'C:\\test\\01_Advanced_Validation\\errors_2025-03-29_13-54-46-552150.csv'.
        Total_files validated: 11.
        Valid files: 6.
        Invalid files: 5.
        01 Advanced Validation:: Demo XML validation | FAIL |
        21 errors have been detected.
        ========================================================
        01 Advanced Validation:: Demo XML validation | FAIL |
        1 test, 0 passed, 1 failed
        
    The corresponding CSV output would in both cases look like:

    .. code:: text

        file_name,path,reason
        xsd_violations_1.xml,/Employee/ID,invalid literal for int() with base 10: 'ABC'
        xsd_violations_1.xml,/Employee/Age,invalid literal for int() with base 10: 'Twenty Five'
        xsd_violations_1.xml,/Employee,Unexpected child with tag '{http://example.com/schema1}FullName' at position 2. Tag '{http://example.com/schema1}Name' expected.
        malformed_xml_1.xml,,"Premature end of data in tag Name line 1, line 1, column 37 (file:/C:/Projects/robotframework-xmlvalidator/test/_data/integration/TC_01/schema1_malformed_2.xml, line 1)"
        malformed_xml_1.xml,,"Opening and ending tag mismatch: ProductID line 1 and Product, line 1, column 31 (file:/C:/Projects/robotframework-xmlvalidator/test/_data/integration/TC_01/schema2_malformed_3.xml, line 1)"
        schema2_invalid_1.xml,/Product/Price,invalid value '99.99USD' for xs:decimal
        schema2_invalid_2.xml,/Product,The content of element '{http://example.com/schema2}Product' is not complete. Tag '{http://example.com/schema2}Price' expected.
        no_xsd_match_1.xml,,No matching XSD found for: no_xsd_match_1.xml.
        no_xsd_match_2.xml,,No matching XSD found for: no_xsd_match_2.xml.

    """

    __version__ = '1.0.0'
    ROBOT_LIBRARY_DOC_FORMAT = 'reST'
    nr_instances = 0

    def __init__(
            self,
            xsd_path: Optional[str | Path] = None,
            base_url: Optional[str] = None,
            error_facets: Optional[ List[str] ] = None
            ) -> None:
        """
        **Library Scope**

        The XmlValidator library has a ``GLOBAL`` 
        `library scope <https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#library-scope>`_


        **Library Arguments**

        +--------------+--------------+-----------+---------------------------------------------------------------------------------------------+
        | Argument     | Type         | Required  | Description                                                                                 |
        +==============+==============+===========+=============================================================================================+
        | xsd_path     | str          | No        | Path to an XSD file or folder to preload during initialization.                             |
        |              |              |           | In case of a folder, the folder must hold one file only.                                    |
        +--------------+--------------+-----------+---------------------------------------------------------------------------------------------+
        | base_url     | str          | No        | Base path used to resolve includes/imports within the provided XSD schema.                  |
        +--------------+--------------+-----------+---------------------------------------------------------------------------------------------+
        | error_facets | list of str  | No        | The attributes of validation errors to collect and report. E.g. ``path``, ``reason``.       |
        +--------------+--------------+-----------+---------------------------------------------------------------------------------------------+

        All arguments are optional.

        ``xsd_path``

        Must be a (valid) path to a single XSD file. If the path 
        points to a directory, to a file without '.xsd' extension or 
        to an invalid or corrupt XSD file, an appropriate exception 
        will be raised.

        The optional ``xsd_path`` parameter allows pre-loading a 
        specific XSD schema file during initialization. This schema 
        will then be used as the schema for all subsequent calls to 
        ``Validate Xml Files`` that do not themselves pass a path to 
        an XSD schema file or to a folder containing one or more XSD 
        files.
        
        As soon as an ``xsd_path`` (to a schema file or a folder 
        holding one or more schema files) is passed to 
        ``Validate Xml Files``, at the test case level, a schema 
        file that was loaded during library initialization will be 
        overriden.
        
        If no schema has been set during initialization, then a path 
        to an XSD schema file (or a folder holding one or more 
        schema files) must be supplied in the very first call to 
        ``Validate Xml Files`` to prevent the call from failing.

        If no schema has been set during library import or by a 
        precending call to ``Validate Xml Files``, then any call to 
        the keyword that does not provide a schema, will fail.

        Each time a schema file is passed and set, all subsequent calls 
        to ``Validate Xml Files`` will use that schema, unless it is 
        replaced by passing a new ``xsd_path`` with a call.

        ``base_url``

        The `base_url` parameter is used to resolve relative imports 
        and includes within the XSD schema. It should point to the 
        base directory or URL for resolving relative paths in the 
        XSD schema, such as imports and includes.

        ``error_facets``

        This parameter accepts a list of error attributes to collect 
        during validation failures. If not provided, it will be set to 
        the default: ['path', 'reason']. 
        
        Using ``error_facets`` you can control which attributes of 
        validation errors are to be collected and, ultimately, reported.
        
        See the introduction for more details on the purpose and usage 
        of error facets.
        
        **Examples**

        Using a preloaded schema:

        .. code:: robotframework

            ************* Settings ***
                      Library    xmlvalidator    xsd_path=path/to/schema.xsd

        Defer schema loading to the test case(s):

        .. code:: robotframework

            **********Library    xmlvalidator

        Importing with preloaded XSD that requires a base_url:

        .. code:: robotframework

            **********Library    xmlvalidator    xsd_path=path/to/schema_with_include.xsd
            **********...                        base_url=path/to/include_schemas

        Use ``base_url`` when your XSD uses ``<xs:include>`` or ``<xs:import>`` with relative paths.

        Use the ``error_facets`` argument to control which attributes of detected errors will be collected and reported.

        E.g. the element locator (XPath), error message, involved namespace and/or the XSD validator that failed.

        Example:

        .. code:: robotframework

            **********Library    xmlvalidator    error_facets=path, message, validator

        You can also combine this with a preloaded schema and/or a base_url:

        .. code:: robotframework

            **********Library    xmlvalidator    xsd_path=schemas/schema.xsd
            **********...                        error_facets=value, namespaces

        For more examples see the project's 
        `Robot Framework integration test suite <https://github.com/MichaelHallik/robotframework-xmlvalidator/blob/main/test/integration/01_library_initialization.robot>`_.

        **Raises**

        +---------------+--------------------------------------------------------------+
        | Exception     | Description                                                  |
        +===============+==============================================================+
        | ValueError    | Raised if ``xsd_path`` is provided, but resolves to multiple |
        |               | XSD files instead of a single one.                           |
        +---------------+--------------------------------------------------------------+
        | SystemError   | Raised if loading the specified XSD schema fails due to an   |
        |               | invalid or unreadable file.                                  |
        +---------------+--------------------------------------------------------------+
        | IOError       | Raised if the XSD file cannot be accessed due to file        |
        |               | system restrictions.                                         |
        +---------------+--------------------------------------------------------------+
        """
        # Use composition for flexibility, as helper classes may grow.
        self.validator_utils = ValidatorUtils()
        self.validator_results = ValidatorResultRecorder()
        # Initialize the xsd schema from the xsd_path, if provided.
        if xsd_path:
            # Try to get a single xsd file from the provided xsd_path.
            xsd_file_path, is_single_xsd_file = (
                self.validator_utils.get_file_paths(
                    xsd_path, 'xsd'
                    )
                )
            # We need (a path to) a single xsd file.
            if not is_single_xsd_file:
                raise ValueError(f"Got multiple xsd files: {xsd_file_path}.")
            # Handle incorrect file extension.
            if xsd_file_path[0].suffix != '.xsd':
                # Raise a load error.
                raise SystemError(
                    f"ValueError: {xsd_file_path[0]} is not an XSD file."
                    )
            # Try to load the provided XSD file.
            result = self._load_schema(xsd_file_path[0], base_url )
            if result.success:
                # Set the loaded XSD file as default schema.
                self.schema = result.value
                logger.info(
                    f"Schema '{self.schema.name}' set.", # type: ignore
                    also_console=True)
            else:
                # Or report the load error.
                raise SystemError(f"Loading of schema failed: {result.error}")
        # Or inform the user on what to do.
        else:
            logger.info(
                "No XSD schema set: provide schema(s) during keyword calls.",
                also_console=True
                )
            # And flag the schema attr as None.
            self.schema = None
        # Set the error facets to collect for failed XML validations.
        self.error_facets = error_facets if error_facets else [
            'path', 'reason'
            ]
        logger.info(
            f"Collecting error facets: {self.error_facets}.",
            also_console=True
            )
        logger.info("XML Validator ready for use!", also_console=True)
        self.nr_instances += 1
        logger.info(f'Number of library instances: {self.nr_instances}.')

    def _determine_validations(
            self,
            xml_paths: List[Path],
            xsd_path: Optional[str|Path] = None,
            xsd_search_strategy: Optional[
                Literal['by_namespace', 'by_file_name']
                ] = None,
            base_url: Optional[str] = None
            ) -> Dict[Path, Path | None]:
        """
        Constructs a mapping between XML files and the XSD schemas to 
        use for their validation.

        This internal method is used during batch validation workflows 
        to determine which XSD schema (if any) should be used for each 
        XML file in a given set.

        Depending on the presence of `xsd_path` and 
        `xsd_search_strategy`, it supports the following resolution 
        strategies:

        1. Single schema (shared across all XML files).
        
        If `xsd_path` resolves to a single XSD file, that schema is 
        preloaded and reused for all target XML files.

        2. Dynamic schema matching (multiple schemas):

        If `xsd_path` resolves to a directory with multiple `.xsd` 
        files, each XML file is matched to a corresponding schema file.

        There are two ways in which `xsd_path` can resolve to a 
        directory:

        - Either because the passed `xsd_path` is a directory.
        - Or because no `xsd_path` has been passed (hence it is None), 
          but a (valid) `xsd_search_strategy` has been passed. In that 
          case it is assumed that the passed `xml_paths` is a list 
          holding one item that points to a folder holding not only XML 
          files, but also their accompanying XSD files. That path will, 
          therefore, be assigned to `xsd_path` within the method.

        XML and XSD files can be matched by either one of these 
        strategies:

        - 'by_namespace' (DEFAULT):
           Matches XSDs based on XML namespace compatibility.
        - 'by_file_name':
           Matches XML and XSD files based on identical stem (base 
           name).

        3. Fallback to default schema:

        If neither `xsd_path` nor `xsd_search_strategy` is provided, the 
        method assumes a default schema has already been set on the 
        class instance (i.e. during library initialization).

        Args:

        - xml_paths (List[Path]):
          A list of resolved paths to XML files that need validation.
        - xsd_path (str | Path, optional):
          Either a path to a single `.xsd` file or a directory 
          containing multiple `.xsd` files. If not provided, fallback 
          behavior applies.
        - xsd_search_strategy (Literal["by_namespace", "by_file_name"], optional):
          Specifies how to dynamically map each XML file to a schema 
          when multiple `.xsd` files are present. Required when 
          `xsd_path` is a folder.
        - base_url (str, optional):
          An optional base path or URL used when resolving `import` or 
          `include` statements within XSD files.

        Returns:

        - Dict[Path, Path | None]:
          A dictionary mapping each XML file path to its corresponding 
          XSD schema path (or to None if the default schema should be 
          used).

        Raises:

        - SystemError:
          Raised if schema loading fails during single-schema or dynamic 
          resolution. The raised error includes parsing failure details.

        Notes:

        - If an XML file cannot be matched to a schema in dynamic 
          matching mode, a `FileNotFoundError` is mapped to that file 
          path in the return dictionary.
        - If a malformed XMl file is encountered, the resulting parse 
          error will be caught and mapped to the path of that file, in the 
          return dictionary.
        - This method does not perform validation — only resolution of 
          schema-to-XML associations.
        - The returned result is passed to `_validate_xml()` during 
          batch validation to apply the resolved schema to each XML.
        """
        # Initialize the return dict.
        validations: dict[Path, Path | None] = {}
        # If no xsd_path is provided, but an xsd_search_strategy IS provided.
        if not xsd_path and xsd_search_strategy:
            # Then assume the XSD file(s) to reside in the XML folder
            xsd_path = xml_paths[0].parent
        # The xsd_path can be either an XSD file or a dir holding the file(s).
        if xsd_path:
            # Determine and resolve the XSD file path(s).
            xsd_paths, is_single_xsd_file = (
                self.validator_utils.get_file_paths(xsd_path, 'xsd')
                )
            # All XML files are to be validated against a single XSD schema.
            if is_single_xsd_file:
                # Load the schema as default schema to use.
                result = self._ensure_schema(xsd_paths[0], base_url)
                # Handle a load error.
                if not result.success:
                    raise SystemError(
                        f"Loading of schema failed: {result.error}."
                        )
                # Ensure downstream schema loading will be skipped.
                xsd_file_paths: List[Path|None] = [None] * len(xml_paths)
                # Create the XML/XSD map.
                validations = dict(
                    zip( xml_paths, xsd_file_paths )
                    )
            # We got a set of XSDs, that need to be dynamically mapped to XMLs.
            else:
                # Map the XSD files to the XML files.
                validations = self._find_schemas(
                    xml_paths,
                    xsd_paths,
                    xsd_search_strategy if xsd_search_strategy else 'by_namespace',
                    base_url
                    )
        # No XSD path or search strategy given: assume schema set during init.
        else:
            # Ensure default schema is loaded; raises exception otherwise.
            result = self._ensure_schema(None, None)
            # Ensure downstream schema loading will now be skipped.
            xsd_file_paths: List[Path|None] = [None] * len(xml_paths)
            # Create the XML/XSD map.
            validations = dict(
                zip( xml_paths, xsd_file_paths )
                )
        return validations

    def _ensure_schema(
            self,
            xsd_path: Optional[Path] = None,
            base_url: Optional[str] = None
            ) -> ValidatorResult:
        """
        Ensures that a schema is available for validation.

        This internal method guarantees that the `XmlValidator` instance 
        has access to an XSD schema.

        It checks whether a schema is already loaded (in `self.schema`) 
        or whether one should be loaded from the provided `xsd_path`.

        If no `xsd_path` is given but a schema is already loaded (in 
        self.schema), that existing schema is simply reused.

        If a new path is passed, it is always loaded via 
        `_load_schema()`, replacing an existing schema (if any).

        If no `xsd_path` is given and no schema was loaded earlier 
        (self.schema is None), the method raises a ValueError.

        Args:

        - xsd_path (str or Path, optional):
          Path to the XSD schema to load and set as default. Overrides 
          any previously loaded schema.

        - base_url (str, optional):
          Optional base path used for resolving `import` and `include` 
          statements in the schema.

        Returns:

        - ValidatorResult:
          A result object indicating whether a valid schema is available 
          for XML validation.
          - If `success=True`:
            - The `value` field holds the loaded `XMLSchema` object from 
              the `xmlschema` library.
            - This schema can be used to validate one or more XML files 
              and will typically be assigned to `self.schema`.
          - If `success=False`:
            - The `error` field contains structured information about 
              the reason for failure (e.g., schema file not found, parse 
              error).

        Raises:

        - ValueError:
          - Raised if neither a schema has been preloaded nor an 
            `xsd_path` is provided. In such cases, the method cannot 
            proceed and explicitly requires a schema to be available.
          - Note: other schema-related failures (e.g., parsing errors, 
            I/O issues) are not raised here. Any such failures are 
            captured by _load_schema and then returned as part of a 
            `ValidatorResult` object.

        Notes:

        - This method does not raise exceptions directly; it wraps 
          schema loading results using `ValidatorResult`.
        - Used internally in validation and schema resolution workflows.
        - This method relies on `_load_schema` for the actual schema 
          loading process, which validates and parses the XSD schema.
        """
        if not (self.schema or xsd_path):
            raise ValueError(
                "No schema: provide an XSD path during keyword call(s)."
                )
        if self.schema and not xsd_path :
            logger.info(
                f'No new schema set: keeping existing schema {self.schema}.'
                )
            return ValidatorResult(success=True, value=self.schema)
        if not self.schema and xsd_path:
            logger.info(f'Setting schema file: {xsd_path}.', also_console=True)
        if self.schema and xsd_path:
            logger.info(
                f'Setting new schema file: {xsd_path}.',
                also_console=True
                )
        return self._load_schema(xsd_path, base_url) # pyright: ignore

    def _find_schemas(
            self,
            xml_file_paths: List[Path],
            xsd_file_paths: List[Path],
            search_by: Literal[
                'by_namespace',
                'by_file_name'
                ] = 'by_namespace',
            base_url: Optional[str] = None
            ) -> Dict[ Path, Path | None ]:
        """
        Finds matching XSD schemas for XML files using the specified 
        search strategy.

        This internal method performs schema-to-XML matching for batch 
        validation workflows, returning a dictionary that maps each XML 
        file to its corresponding XSD file. If no match is found for a 
        given file, that file is mapped to `None`.

        Two matching strategies are supported:

        1. by_namespace (default):
           - Extracts the set of declared namespaces from each XML file.
           - Compares them to the `targetNamespace` declaration (and 
             related declarations) of/in each XSD file.
           - Matches the first schema that shares at least one 
             namespace.
        2. by_file_name:
           - Matches based on file name stem (i.e. file name without 
             extension), e.g., `invoice.xml` ↔ `invoice.xsd`.
           - Matches the first schema with a matching base name (if 
             any).
        
        If an XML file cannot be matched to a schema in dynamic matching 
        mode, a `FileNotFoundError` is mapped to that file path in the 
        return dictionary.

        If a malformed XMl file is encountered, the resulting parse 
        error will be caught and mapped to the path of that file, in the 
        return dictionary.
        
        Args:

        - xml_file_paths (List[Path]):
          A list of paths to XML files to be matched with schemas.
        - xsd_file_paths (List[Path]):
          A list of paths to candidate XSD schema files.
        - search_by (Literal["by_namespace", "by_file_name"], optional):
          The strategy to use for matching XML files to schemas. 
          Defaults to `"by_namespace"`.
        - base_url (str, optional):
          An optional base URL used to resolve imports and includes 
          during namespace-based schema parsing.
        
        Returns:

        - Dict[Path, Path | None | FileNotFoundError]:
          A mapping from each XML file path to:
          - A matching XSD file path if found.
          - None, if no match is applicable.
          - A `FileNotFoundError` object if the schema lookup failed due 
            to loading or parsing errors.
        
        Notes:
        										 
        - This method does not perform validation — it only establishes 
          schema associations, which are later consumed by 
          `_validate_xml()`.
        - Errors during XML parsing or namespace extraction are caught 
          and logged and the corresponding file is assigned `None`.
        - XSD schema loading failures (e.g., invalid file, parse error) 
          result in a `FileNotFoundError` marker.
        """
        # Prepare the return dictionary.
        validations = {}
        # For each XML file, try to find a matching XSD file.
        logger.info(
            f"Mapping XML files to schemata {search_by.replace('_', ' ')}.",
            also_console=True
            )
        for xml_file_path in xml_file_paths:
            logger.info(f"\tSearching schema for: {xml_file_path.stem}.")
            # Initialize the dict entry with None.
            validations[xml_file_path] = None
            # Namespace-based matching.
            if search_by == "by_namespace":
                # Get the XML's namespace(s).
                try:
                    # Get the XML root element.
                    xml_root = etree.parse( # pylint: disable=I1101:c-extension-no-member
                        str(xml_file_path),
                        parser=etree.XMLParser() # pylint: disable=I1101:c-extension-no-member
                        ).getroot()
                    # Get the namespaces from the root element.
                    xml_namespaces = ValidatorUtils.extract_xml_namespaces(
                            xml_root,
                            include_nested=False
                            )
                # Catch and handle any exception.
                except Exception as err: # pylint: disable=W0718:broad-exception-caught
                    # Inform the user.
                    logger.warn('Processing XML file failed.')
                    # Collect the error to be mapped to the xml file.
                    validations[xml_file_path] = err
                    continue
                # Test each XSD file for a matching namespace.
                for xsd_file_path in xsd_file_paths:
                    logger.info(f"Testing schema: {xsd_file_path}.")
                    # Load the schema.
                    result = self._load_schema(
                        xsd_file_path, base_url=base_url
                        )
                    # Log an error, and continue (instead of failing).
                    if not result.success:
                        logger.warn(
                            f"Matching attempt failed due to exception: {result.error}."
                            )
                        continue
                    # Use match_namespace_to_schema for matching logic.
                    match = self.validator_utils.match_namespace_to_schema(
                        result.value, # type: ignore
                        xml_namespaces, # type: ignore
                        )
                    # If succesful, flag the xsd file as match & end loop.
                    if match:
                        logger.info(f"\t\t\tMatch found with: {xsd_file_path}.")
                        validations[xml_file_path] = xsd_file_path
                        break
            # Filename-based matching.
            elif search_by == "by_file_name":
                for xsd_file_path in xsd_file_paths:
                    # Log informative.
                    logger.info(f"\t\t\tTesting file name: {xsd_file_path}.")
                    # Compare the XSD/XML file names.
                    if xsd_file_path.stem == xml_file_path.stem:
                        logger.info("\t\t\tFound match.")
                        # Assign current XSD path in case of a match & break.
                        validations[xml_file_path] = xsd_file_path
                        break
                    # Locating matching schema failed: go to the next xsd file.
                    logger.info("\t\t\tNo match: trying next schema file.")
                    continue
            # Handle unsupported/incorrect search strategy.
            else:
                raise ValueError(f"Unsupported search strategy: {search_by}.")
            # If no match has been found.
            if not validations[xml_file_path]:
                logger.info(f"No valid XSD found for {xml_file_path}.")
                validations[xml_file_path] = FileNotFoundError(
                    f'No matching XSD found for: {xml_file_path.stem}.'
                    )
        return validations

    def _load_schema(
            self,
            xsd_path: Path,
            base_url: Optional[str] = None
            ) -> ValidatorResult:
        """
        This method is responsible for initializing a schema object, 
        using the `xmlschema` library.
        
        As such, it parses and loads an XSD schema from a given file 
        path, with support for resolving relative paths via the 
        `base_url` parameter.

        If the parse/load attempt of a schema file results in any error 
        (e.g. a parse error), that error will be caught, wrapped in a 
        ValidatorResult object and returned. See for the latter the 
        'Returns' section below.

        Args:

        - xsd_path (Path):
          Path to a `.xsd` schema file to load.
        - base_url (str, optional):
          An optional base path or URL for resolving `import` and 
          `include` references inside the XSD schema.

        Returns:

        - ValidatorResult:
          A result object indicating whether schema loading succeeded.
          - If `success=True`:
            - The `value` field contains a fully parsed `XMLSchema` 
              object.
          - If `success=False`:
            - The `error` field contains structured error information 
              describing what failed and why (e.g., file unreadable, not 
              well-formed, parse error, etc.).

        Notes:

        - This method never raises exceptions directly; all errors are 
          captured and wrapped in a `ValidatorResult`.
        - Used internally by `_ensure_schema()` and `_find_schemas()` to 
          guarantee schema readiness.
        """
        # Load the XSD schema (with base_url, if provided).
        try:
            self.schema = XMLSchema( xsd_path, base_url=base_url )
            return ValidatorResult( success=True, value=self.schema )
        # Catcherrors to propagate them upstream.
        except Exception as e: # pylint: disable=W0718:broad-exception-caught
            return ValidatorResult(
                success=False, error={"XMLSchemaValidationError": e}
                )

    def _validate_xml(self, # pylint: disable=R0913:too-many-arguments disable=R0917:too-many-positional-arguments
                      xml_file_path: Path,
                      xsd_file_path: Optional[Path] = None,
                      base_url: Optional[str] = None,
                      error_facets: Optional[ List[str] ] = None,
                      pre_parse: Optional[bool] = True
                      ) -> Tuple[
                          bool, Optional[
                              List[ dict[str, Any] ]
                              ]
                            ]:
        """
        Validates an XML file against the currently loaded or provided 
        XSD schema.

        This method performs the core XML validation logic and is 
        invoked by the public `validate_xml_file` method. It checks an 
        XML file for conformance with the structural and datatype rules 
        defined in the XSD schema.

        It focuses exclusively on validation and generating errors based 
        on the specified facets.

        Errors that are collected and returned can be categorized as 
        follows:

        1. XSD Schema violations.

        The following types of XSD schema violations are detected during 
        validation:

        1. Detects missing or extra elements that violate cardinality 
           rules, e.g.:
           - Verifies that all mandatory elements (minOccurs > 0) are 
             present in the XML.
           - Ensures that optional elements (minOccurs = 0) do not 
             exceed their maximum allowed occurrences (maxOccurs).

        2. Sequence and Order Violations:
           - Validates the order of child elements within a parent 
             element if the schema specifies a sequence model 
             (`<xsd:sequence>`).
           - Detects elements that are out of order or missing in a 
             sequence.

        3. Datatype Violations:
           - Ensures that element and attribute values conform to their 
             specified datatypes (e.g., xs:string, xs:integer, 
             xs:dateTime).
           - Identifies invalid formats, such as incorrect date or time 
             formats for xs:date and xs:dateTime.

        4. Pattern and Enumeration Violations:
           - Checks that values conform to patterns defined using 
             `<xsd:pattern>`.
           - Ensures that values fall within allowed enumerations 
             specified in the schema.

        5. Attribute Validation:
           - Verifies that required attributes are present.
           - Ensures that attribute values adhere to their declared 
             datatypes and constraints.

        6. Namespace Compliance:
           - Validates that elements and attributes belong to the 
             correct namespaces as defined in the schema.
           - Detects namespace mismatches or missing namespace 
             declarations.

        7. Group Model Violations:
           - Validates conformance with `<xsd:choice>` and `<xsd:all>` 
             group models, ensuring correct usage of child elements as 
             per the schema.

        8. Referential Constraints:
           - Checks for violations in `<xsd:key>`, `<xsd:keyref>`, and 
             `<xsd:unique>` constraints.

        9. Document Structure and Completeness:
           - Ensures that the XML document adheres to the hierarchical 
             structure defined by the schema.
           - Detects incomplete or improperly nested elements.

        10. General Schema Violations:
            - Detects schema-level issues, such as invalid imports or 
              includes, during schema compilation if they affect 
              validation.

        2. Errors following from malformed XML and/or XSD files.

          The method checks whether upstream handling of the involved 
          XML file (e.g. during dynamic schema matching) resulted in an 
          error. For instance a FileNotFound error or a ParseError.
          
          The method does this by checking whether the coresponding 
          xsd_file_path is an instance of BaseException. In that case, 
          the method returns early, propagating the error to the 
          downstream error collection & reporting.

          The method tself performs a additonal sanity check on the 
          involved XML/XSD files, calling the sanity_check_files() 
          utility method on both. The latter checks each file whether:

          - it exists
          - is not empty
          - is of the correct file type
          - is well-formed (syntactycally correct)
          
          In case of a failing check, the method returns early, 
          propagating the involved error to downstream error collection 
          & reporting.
        
        3. Invalid XSD schema.

           If schema loading fails, the method returns early, 
           propagating the involved error to downstream error collection 
           & reporting.

        Args:

        - xml_path (str or Path):
          Path to the XML file to validate.

        - xsd_path (str or Path, optional):
          Path to an alternative XSD schema file to use for this 
          validation. If not provided, the schema loaded during 
          initialization will be used.

        - error_facets (list, optional):
          Specifies which attributes of the XMLSchemaValidationError 
          should be included in the error output.
          This provides flexibility in tailoring the level of detail in 
          the error messages.

          Supported Attributes:

          add_note, args, elem, expected, get_elem_as_string, 
          get_obj_as_string, index, invalid_child, invalid_tag, 
          message, msg, namespaces, obj, occurs, origin_url, 
          particle, path, reason, root, schema_url, source, 
          sourceline, stack_trace, validator, with_traceback

          Defaults to ['path', 'reason'].

        Returns:

        - tuple (is_valid, errors):
          - is_valid (bool):
            True if the XML file conforms to the schema, False 
            otherwise.
          - errors (list of dict):
            A list of detailed error facets/aspects, each represented as  
            dictionary. The dictionary keys depend on the `error_facets` 
            argument.
        """
        # Log informative.
        logger.info(
            f"Validating '{xml_file_path.stem}'.", also_console=True
            )
        # Check upstream XSD matching led to an err pertaining to the XML.
        if isinstance(xsd_file_path, BaseException):
            return False, [{
                facet: str(xsd_file_path) if facet == 'reason' else ''
                for facet in (error_facets or self.error_facets)
            }]
        # Sanity check the target (XML/XSD) files.
        sanity_check_result = self.validator_utils.sanity_check_files(
            [file_path for file_path in [
                xml_file_path, xsd_file_path
                ] if isinstance(file_path, Path) and file_path],
            base_url=base_url,
            parse_files=pre_parse
            )
        if not sanity_check_result.success:
            # Abort validation if one or more sanity checks failed.
            logger.warn("File(s) failed basic sanity check.")
            return False, sanity_check_result.error
        # Ensure a valid schema is loaded.
        loading_result = self._ensure_schema(
            xsd_file_path, base_url
            )
        if not loading_result.success:
            # Abort the validation if schema loading failed.
            logger.warn("Schema loading failed.")
            return False, loading_result.error
        # Validate the XML against the XSD schema.
        errors = [
            {
                # Collect the details/facets for each XSD violation.
                facet: getattr(err, facet, None)
                # Error facets to collect determined by arg or instance.
                for facet in (error_facets or self.error_facets)
            }
            # Generate an err obj (with err details) per encountered violation.
            for err in loading_result.value.iter_errors(xml_file_path) # pyright: ignore
            ]
        # Determine validity based on the presence of errors.
        return (True, None) if len(errors) == 0 else (False, errors)

    @keyword
    def get_error_facets(self) -> List[str]:
        """
        .. raw:: html

            <span style="text-decoration: underline; font-size: 15px;">Description</span>

        Returns the currently configured error facets.

        Error facets determine which attributes are extracted from 
        validation errors (instances of XMLSchemaValidationError).
        
        These attributes control the structure and detail level of the 
        error dictionaries returned during XML validation.

        .. raw:: html

            <span style="text-decoration: underline; font-size: 15px;">Returns</span>

        A list of active error facets, e.g. ["path", "reason"].
        """
        return self.error_facets

    @keyword
    def get_schema(
        self,
        return_schema_name: bool = True
        ) -> Optional[str|XMLSchema]:
        """
        .. raw:: html

            <span style="text-decoration: underline; font-size: 15px;">Description</span>

        Returns the currently loaded schema.

        If no schema is loaded, returns None.
        
        Otherwise, returns either the schema's `name` or the full schema 
        object, depending on the `return_schema_name` flag.

        .. raw:: html

            <span style="text-decoration: underline; font-size: 15px;">Arguments</span>

        return_schema_name:

        - If True (default), returns the schema's name attribute.
        - If False, returns the actual XMLSchema object.

        .. raw:: html

            <span style="text-decoration: underline; font-size: 15px;">Returns</span>

        The name of the loaded schema, the schema object itself, or None 
        if no schema is available.
        """
        if not self.schema:
            return None
        if return_schema_name:
            return getattr(self.schema, "name", None)
        return self.schema

    @keyword
    def log_schema(self, log_name: bool = True):
        """
        .. raw:: html

            <span style="text-decoration: underline; font-size: 15px;">Description</span>

        Prints schema information to the console and writes it to the 
        Robot Framework log.
        
        If `log_name` is True, the schema's name is printed (if 
        available); otherwise, the full schema object is logged.

        .. raw:: html

            <span style="text-decoration: underline; font-size: 15px;">Arguments</span>

        log_name:
        
        - If True (default), log only the schema's name.
        - If False, log the full XMLSchema object.
        """
        if self.schema and log_name:
            logger.info(
                f"Schema currently loaded: {self.schema.name}.",
                also_console=True
                )
        logger.info(
            f"Schema currently loaded: {self.schema}.",
            also_console=True
            )

    @keyword
    def reset_error_facets(self):
        """
        Resets the error facets to their default values.

        By default, only the 'path' and 'reason' attributes of 
        validation errors are collected. This method discards any 
        customizations and reverts to those defaults.

        Prints the the change to the console and in the Robot Framework 
        log.
        """
        self.error_facets = ['path', 'reason']
        logger.info(
            f"Error facets restored to default: {', '.join(self.error_facets)}.",
            also_console=True
            )

    @keyword
    def reset_errors(self):
        """
        Clears all previously stored validation results.

        This keyword resets the internal `ValidatorResultRecorder` 
        instance, discarding any errors, warnings, or file status data 
        collected during validation.

        A confirmation message is logged to the Robot Framework log.
        """
        self.validator_results.reset()
        logger.info("Error collector has been reset.", also_console=True)

    @keyword
    def reset_schema(self):
        """
        Unloads the currently loaded schema.

        This keyword clears the cached schema reference by setting it to 
        None. Future validation calls must provide a new schema.

        A message confirming schema reset is logged to the Robot Framework 
        log.
        """
        self.schema = None
        logger.info("Schema attribute reset: no schema loaded.", also_console=True)

    @keyword
    def validate_xml_files( # pylint: disable=R0913:too-many-arguments disable=R0914:too-many-locals disable=R0917:too-many-positional-arguments
        self,
        xml_path: str | Path,
        xsd_path: Optional[str | Path] = None,
        xsd_search_strategy: Optional[
            Literal['by_namespace', 'by_file_name']
            ] = None,
        base_url: Optional[str] = None,
        error_facets: Optional[ List[str] ] = None,
        pre_parse: Optional[bool] = True,
        write_to_csv: Optional[bool] = True,
        timestamped: Optional[bool] = True,
        reset_errors: bool = True,
        fail_on_errors: Optional[bool] = False
        ) -> Tuple[
            List[ Dict[str, Any] ],
            str | None
            ]:
        """
        **Introduction**

        Please make sure to have read the ``Introduction`` to the 
        `keyword doc <https://github.com/MichaelHallik/robotframework-xmlvalidator/blob/main/docs/XmlValidator.html>`_.
        
        That section contains information that is essential to the 
        effective usage of the ``Validate Xml Files`` keyword and that 
        will not be repeated here, to avoid redundancy. 

        This keyword supports *single file* validation, *batch* validation 
        and *dynamic schema mapping*.

        It also supports comprehensive and *configurable* error reporting 
        and the *export* of all collected errors to CSV files.

        **Basic use cases**

        +---+----------------------------+------------------------+------------------------+------------------------------------------------------------+
        |   | xsd_path passed with       | xml_path points to     | xsd_path points to     | Keyword call result                                        |
        +===+============================+========================+========================+============================================================+
        | 1 | Library Import             | Single XML File        | Single XSD File        | XML file validated against preloaded schema.               |
        +---+----------------------------+------------------------+------------------------+------------------------------------------------------------+
        | 2 | Library Import             | Folder of XMLs         | Single XSD File        | Each XML in folder validated against preloaded schema.     |
        +---+----------------------------+------------------------+------------------------+------------------------------------------------------------+
        | 4 | Keyword Call               | Single XML File        | Single XSD File        | XML file validated against the passed schema.              |
        +---+----------------------------+------------------------+------------------------+------------------------------------------------------------+
        | 5 | Keyword Call               | Folder of XMLs         | Single XSD File        | Each XML in folder validated against the provided schema.  |
        +---+----------------------------+------------------------+------------------------+------------------------------------------------------------+
        | 5 | Keyword Call               | Single XML File        | Folder of XSDs         | Keyword attempts to find a matching XSD file, either by    |
        |   |                            |                        |                        | namespace or by filename. The latter is determined by arg  |
        |   |                            |                        |                        | ``xsd_search_strategy``. If a match is found, the XML file |
        |   |                            |                        |                        | is validated against it. If no match is found, this fact   |
        |   |                            |                        |                        | is added to the error report.                              |
        +---+----------------------------+------------------------+------------------------+------------------------------------------------------------+
        | 6 | Keyword Call               | Folder of XMLs         | Folder of XSDs         | The keyword attempts to match each XML to one of the       |
        |   |                            |                        |                        | schema files in the folder, either by namespace or by      |
        |   |                            |                        |                        | filename. The latter is determined by arg                  |
        |   |                            |                        |                        | ``xsd_search_strategy``. For each XML that has a matching  |
        |   |                            |                        |                        | XSD, the XML is validated. Each XML without a matching XSD |
        |   |                            |                        |                        | is added to the error report, with an appropriate 'reason'.|
        +---+----------------------------+------------------------+------------------------+------------------------------------------------------------+

        **Error collecting and reporting**       

        Validation errors fall into three main categories:

        - XSD violations:
         
         - Captures cardinality issues, datatype mismatches, enumeration 
           violations, pattern mismatches, namespace errors, etc.

        - Malformed XML:
         
         - Any syntax/parse issues.

        - File-level issues:        
         
         - Detects empty, non-existent, or .
         - Uses sanity checks to validate syntax and type before XSD validation.
        
        - Schema issues:
        
         - Handles cases of invalid, unreadable, or unmatchable schema files.

        All collected errors can optionally be written to a CSV file. 
        Each row includes error details and the associated file name.

        **Arguments**   

        ``xml_path``

        Path to an XML file or a directory containing `.xml` files.

        ``xsd_path``
        
        Path to a single `.xsd` file or a directory containing one or more 
        `.xsd` files. Required for dynamic schema resolution or schema 
        overrides. Defaults to None.

        ``xsd_search_strategy``

        Strategy for dynamic schema resolution when validating against 
        multiple schemas. Required if `xsd_path` is a directory or not 
        passed at all.
        
        Defaults to 'by_namespace'.

        ``base_url``
        
        Base directory for resolving schema imports and includes.
        Defaults to None.

        ``error_facets``
        
        List of error details/attributes to include in the collecting 
        and reporting of errors.

        Defaults to ['path', 'reason'].

        ``pre_parse``
        
        If True, performs well-formedness checks on all XML/XSD files 
        before schema validation. Defaults to True.

        ``write_to_csv``
        
        If True, writes all collected errors to a CSV file in the same 
        folder as the validated XML(s). Defaults to True.

        ``timestamped``
        
        Appends a timestamp to the CSV filename for uniqueness.
        Defaults to True.

        ``reset_errors``
        
        Clears previously stored validation results before this run.
        Defaults to True.

        ``fail_on_errors``

        Fails a test cases if, after checking the entire batch of one or 
        XML files, one or more errors have been reported. Error 
        reporting and exporting will not change.

        **Returns**

        A tuple, holding:

          - A list of dictionaries:
            A list of all validation errors found during the run. Each 
            error is a dictionary with items that are based on the 
            `error_facets`.
          - A string or None:
            The path to the generated CSV file if there are errors and 
            `write_to_csv=True`; otherwise None.

        **Raises**

        Since the keyword's purpose is to catch and collect various 
        types of errors, for these errors no exceptions will be raised.

        However, in certain situations the keyword may raise certain 
        exceptions. For instance:

        ``FileNotFoundError``
        
        For instance if the passed ``xml_path`` is non-existing, points 
        to a non-xml file or points to an empty folder.
        
        ``IOError``
        
        If writing the CSV file fails due to filesystem restrictions.
        """
        # Reset attributes, if requested.
        if reset_errors:
            self.validator_results.reset()
        # Determine and resolve/normalize the XML file path(s).
        xml_file_paths, is_single_xml_file = (
            self.validator_utils.get_file_paths(
                xml_path, 'xml'
                )
            )
        # Pair each XML file with it's proper XSD counterpart.
        validations = self._determine_validations(
            xml_file_paths,
            xsd_path=xsd_path,
            xsd_search_strategy=xsd_search_strategy,
            base_url=base_url
            )
        # Validate each XML file with the corresponding schema.
        for xml_file_path, xsd_file_path in validations.items():
            # The actual validation.
            is_valid, errors = self._validate_xml(
                xml_file_path,
                xsd_file_path=xsd_file_path,
                base_url=base_url,
                error_facets=error_facets,
                pre_parse=pre_parse
                )
            # Process the validation results.
            if is_valid:
                self.validator_results.add_valid_file(xml_file_path)
            else:
                self.validator_results.add_invalid_file(xml_file_path)
                self.validator_results.add_file_errors(xml_file_path, errors)
                self.validator_results.log_file_errors(errors) # type: ignore
        # Write errors to a single CSV file if requested.
        if write_to_csv and self.validator_results.errors_by_file:
            csv_path = self.validator_results.write_errors_to_csv(
                self.validator_results.errors_by_file,
                xml_file_paths[0].parent
                    if is_single_xml_file else xml_file_paths[0],
                include_timestamp=timestamped,
                file_name_column="file_name"
                )
        else:
            csv_path = None
        # Log a summary of the test run.
        self.validator_results.log_summary()
        if fail_on_errors and self.validator_results.errors_by_file:
            raise Failure(
                f"{len(self.validator_results.errors_by_file)} errors have been detected."
                )
        return (
            self.validator_results.errors_by_file,
            csv_path if csv_path else None
            )
