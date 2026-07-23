# Copyright 2024-2026 Michael Hallik
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

# pylint: disable=C0103:invalid-name    # On account of the module name, that is not snake-cased (required by Robot Framework).
# pylint: disable=C0302:too-many-lines  # On account of the extensive docstrings and annotations.
# pylint: disable=C0301:line-too-long   # On account of tables in docstrings.
# pylint: disable=R0913:too-many-arguments
# pylint: disable=R0917:too-many-positional-arguments
# ruff: noqa: E501                      # On account of tables in docstrings.

# Standard library imports.
from pathlib import Path
from typing import Any, Literal

# Third party library imports.
from robot.api import Failure, logger
from robot.api.deco import keyword, library
from xmlschema import XMLSchema

# Local application imports.
from ._version import __version__
from .paths import get_file_paths
from .results import ValidatorResultRecorder
from .schema.manager import ValidatorSchemaManager
from .schema.resolver import ValidatorSchemaResolver
from .validation import XmlValidationRunner


@library(scope='GLOBAL', version=__version__, doc_format="REST")
class XmlValidator:  # pylint: disable=R0902:too-many-instance-attributes
    """
    XmlValidator is a `Robot Framework <https://robotframework.org/>`_
    test library for validating XML files against XSD schemas.

    The library leverages the power of the
    `xmlschema library <https://pypi.org/project/xmlschema/>`_ and is
    designed for both single-file and batch XML validation workflows.

    It provides structured and detailed reporting of XML parse errors
    (malformed XML content) and XSD violations, dynamic schema resolution
    and CSV exports of collected errors.

    Features are described in detail on the `project repo's landing page.
    <https://github.com/MichaelHallik/robotframework-xmlvalidator>`_.

    **Overview**

    The main keyword is ``Validate Xml Files``.

    The other keywords are convenience/helper functions, e.g. ``Reset
    Error Facets``.

    The ``Validate Xml Files`` validates one or more XML files against
    one or more XSD schema files and collects and reports all
    encountered errors.

    The type of error that the keyword can detect is not limited to XSD
    violations, but may also pertain to malformed XML files (e.g. parse
    errors), empty files, unmatched XML files (no XSD match found) and
    others.

    Errors that result from malformed XML files or from XSD violations
    support detailed error reporting. Using the ``error_facets``
    argument you may specify the details the keyword should collect and
    report about captured errors. By default, requested error facets
    whose value is ``None`` are reported as ``Unavailable``.

    When operating in batch mode, the ``Validate Xml Files`` keyword
    always validates the entire set of passed XML files. That is, when
    it encounters an error in a file, it does not simply then fail.
    Rather, it collects the error details (as determined by the
    error_facets arg) and then continues validating the current file as
    well as any subsequent file(s).

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
    either a 'by file name' strategy or a 'by namespace' strategy.

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

    - Captures malformed XML (e.g. missing closing tag, encoding
      issues).
    - Handles edge cases like empty files or XML files that could not be
      matched to an XSD schema file.
    - Does not immediately fail on errors, but collects all encountered
      errors in all files and reports them in a structured format in the
      console and RF log. Only *then* fails (assuming one or more
      errors have been collected).
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
    level (i.e. when calling the ``Validate Xml Files`` keyword).

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

    By default, facets whose value is ``None`` are included in the
    collected error dictionaries with the value ``Unavailable``. If you
    prefer to omit requested facets that have no value for a specific
    error, pass ``skip_none_error_facets=True`` to ``Validate Xml Files``.

    Error facets passed during library initialization will be overruled
    by error facets that are passed at the test case level, when calling
    the ``Validate Xml Files`` keyword.

    The values you can pass through the `error_facets` argument are
    based on the attributes of the error objects as returned by the
    XMLSchema.iter_errors() method, that is provided by the xmlschema
    library and the xmlvalidator library leverages. Said method yields
    instances of
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

    Use ``base_url`` when your XSD uses ``<xs:include>`` or ``<xs:import>``
    with relative paths.

    You can pass ``base_url`` with the library import (together with
    passing ``xsd_path``) and/or when calling ``Validate Xml Files``
    with ``xsd_path``.

    **Basic usage examples**

    For a comprehensive set of example test cases, please see the
    `Robot Framework integration tests <https://github.com/MichaelHallik/robotframework-xmlvalidator/tree/main/test/integration/>`_
    in the project's GitHub repository.

    The repo contains a
    `structured overview of all implemented tests <https://github.com/MichaelHallik/robotframework-xmlvalidator/blob/main/test/_doc/integration/overview.html>`_
    per topic (e.g. library import, schema matching strategies, etc.).

    It further contains a detailed instruction on
    `how to run Robot Framework tests <https://github.com/MichaelHallik/robotframework-xmlvalidator/blob/main/test/_doc/integration/README.md>`_.

    Finally, the repo also contains a `demo test suite file <https://github.com/MichaelHallik/robotframework-xmlvalidator/blob/main/test/demo/demo.robot>`_ containing
    self-contained test cases that demonstrate the following features:

    - Single and batch XML validation
    - Schema matching by filename and namespace
    - Custom error facets
    - Malformed XML handling
    - XSD includes/imports
    - CSV export

    A test suite file may look like the following:

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
        Mapping XML files to schemas by namespace.
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
        Validation errors exported to:
            'C:\\test\\01_Advanced_Validation\\errors_2025-03-29_13-54-46-552150.csv'.
        Total_files validated: 11.
        Valid files: 6.
        Invalid files: 5.
        01 Advanced Validation:: Demo XML validation | FAIL |
        21 errors have been detected.
        ========================================================
        01 Advanced Validation:: Demo XML validation | FAIL |
        1 test, 0 passed, 1 failed

    The corresponding CSV output will look like:

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

    nr_instances = 0

    @property
    def schema(self) -> XMLSchema | None:
        """
        Returns the currently loaded schema from the schema manager.
        """
        return self.schema_manager.schema

    @schema.setter
    def schema(self, value: XMLSchema | None) -> None:
        """
        Sets the currently loaded schema on the schema manager.
        """
        self.schema_manager.schema = value

    def __init__(
        self,
        xsd_path: str | Path | None = None,
        base_url: str | None = None,
        error_facets: list[str] | None = None,
        fail_on_errors: bool = True,
    ) -> None:
        """
        **Library Scope**

        The XmlValidator library has a ``GLOBAL``
        `library scope <https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#library-scope>`_


        **Library Arguments**

        +----------------+-------------+----------+---------------------------------------------------------------------------------------------+----------------+
        | Argument       | Type        | Required | Description                                                                                 | Default        |
        +================+=============+==========+=============================================================================================+================+
        | xsd_path       | str         | No       | Path to an XSD file or folder to preload during initialization.                             | None           |
        |                |             |          | In case of a folder, the folder must hold one file only.                                    |                |
        +----------------+-------------+----------+---------------------------------------------------------------------------------------------+----------------+
        | base_url       | str         | No       | Base path used to resolve includes/imports within the provided XSD schema.                  | None           |
        +----------------+-------------+----------+---------------------------------------------------------------------------------------------+----------------+
        | error_facets   | list of str | No       | The attributes of validation errors to collect and report. E.g. ``path``, ``reason``.       | [path, reason] |
        +----------------+-------------+----------+---------------------------------------------------------------------------------------------+----------------+
        | fail_on_errors | bool        | No       | Whether to fail the test case if one or more XML validation errors are found.               | True           |
        |                |             |          | Can be overridden per keyword call.                                                         |                |
        +----------------+-------------+----------+---------------------------------------------------------------------------------------------+----------------+

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
        overridden.

        If no schema has been set during initialization, then a path
        to an XSD schema file (or a folder holding one or more
        schema files) must be supplied in the very first call to
        ``Validate Xml Files`` to prevent the call from failing.

        If no schema has been set during library import or by a
        preceding call to ``Validate Xml Files``, then any call to
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

        ``fail_on_error``

        The ``fail_on_errors`` argument controls whether a test case
        should fail if one or more XML validation errors are detected.
        It defaults to True. A test case that has resulted in the
        collection of one or more errors (of whatever type) will then
        receive a status of FAIL.

        You can use the ``fail_on_errors`` argument to change this
        default behavior. When set to False, the test case status will
        always be PASS, regardless of whether errors were collected.

        This may be useful for:

        - Non-blocking checks in dashboards or QA reports.
        - Legacy or transitional systems where some invalid files are expected.
        - Schema discovery or diagnostics, where conformance is not yet enforced.
        - Soft rollout of stricter validation rules, allowing time to adapt.

        Note that with ``fail_on_error=True`` the library's batch
        validation behavior remains unchanged by the latter. That is,
        fail_on_errors=True does not short-circuit the validation
        process in any way.

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

        And also the `demo test suite file <https://github.com/MichaelHallik/robotframework-xmlvalidator/blob/main/test/demo/demo.robot>`_.

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
        # Use composition for collaborators that keep validation state.
        self.schema_manager = ValidatorSchemaManager()
        self.schema_resolver = ValidatorSchemaResolver(self.schema_manager)
        self.validation_runner = XmlValidationRunner(self.schema_manager)
        self.validator_results = ValidatorResultRecorder()
        # Initialize the xsd schema from the xsd_path, if provided.
        self.schema = self.schema_manager.try_load_initial_schema(
            xsd_path=xsd_path, base_url=base_url
        )
        # Set the error facets to collect for failed XML validations.
        self.error_facets = error_facets if error_facets else [
            'path', 'reason'
        ]
        logger.info(
            f"Collecting error facets: {self.error_facets}.",
            also_console=True
        )
        # Set the validation strictness.
        self.fail_on_errors = fail_on_errors
        logger.info(
            f"Fail on errors: {self.fail_on_errors}.", also_console=True
        )
        # Report readiness.
        logger.info("XML Validator ready for use!", also_console=True)
        self.nr_instances += 1
        logger.info(
            f'Number of library instances: {self.nr_instances}.'
        )

    @keyword
    def get_error_facets(self) -> list[str]:
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
    def get_schema(self,return_schema_name: bool = True
        ) -> str | XMLSchema | None:
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

        Prints the change to the console and in the Robot Framework log
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
    def validate_xml_files( # pylint: disable=R0914:too-many-locals
        self,
        xml_path: str | Path,
        xsd_path: str | Path | None = None,
        xsd_search_strategy: Literal['by_namespace', 'by_file_name'] | None = None,
        base_url: str | None = None,
        error_facets: list[str] | None = None,
        pre_parse: bool = True,
        write_to_csv: bool | None = True,
        timestamped: bool | None = True,
        reset_errors: bool = True,
        fail_on_errors: bool | None = None,
        error_table: bool | None = True,
        allow_declared_namespace_match: bool = False,
        skip_none_error_facets: bool = False
        ) -> tuple[
            list[dict[str, Any]],
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

         - Detects empty, non-existent or unsupported files.
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

        ``skip_none_error_facets``

        If True, omits requested error details whose value is None.
        Defaults to False. By default, every requested facet appears in
        the collected error dictionaries. Facets without an available
        value are reported as ``Unavailable``.

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

        Fails a test case if, after checking the entire batch of one or
        more XML files, one or more errors have been reported. Error
        reporting and exporting will not change.

        ``error_table``

        If True, writes all collected errors to a filterable table in
        the log file. Defaults to True.

        ``allow_declared_namespace_match``

        If True, dynamic namespace matching may fall back to
        non-infrastructure namespaces that are declared in an XSD, even
        if they are not the schema's target namespace or an explicitly
        imported namespace. Defaults to False.

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
        # Determine the validation strictness.
        fail_on_errors = (
            fail_on_errors \
                if fail_on_errors is not None \
                    else self.fail_on_errors
        )
        # Determine and resolve/normalize the XML file path(s).
        xml_file_paths, is_single_xml_file = (
                get_file_paths(
                xml_path, 'xml'
                )
            )
        # Pair each XML file with its proper XSD counterpart.
        validations = self.schema_resolver.build_validation_plan(
            xml_file_paths,
            xsd_path=xsd_path,
            xsd_search_strategy=xsd_search_strategy,
            base_url=base_url,
            allow_declared_namespace_match=allow_declared_namespace_match
            )
        # Execute the validation plan and record each file's result.
        self._run_validation_plan(
            validations,
            base_url,
            error_facets,
            pre_parse,
            skip_none_error_facets
        )
        # Export, report and return the completed validation results.
        return self._finalize_validation_run(
            xml_file_paths,
            is_single_xml_file,
            write_to_csv,
            timestamped,
            error_table,
            fail_on_errors
        )

    def _run_validation_plan(
        self,
        validations: dict[Path, Path | BaseException | None],
        base_url: str | None = None,
        error_facets: list[str] | None = None,
        pre_parse: bool = True,
        skip_none_error_facets: bool = False
    ) -> None:
        """
        Executes a prepared XML-to-XSD validation plan.

        The validation plan maps each XML file to the schema path that
        should be used for that file. A mapped value of ``None`` means
        that the currently loaded schema should be reused. A mapped
        exception represents an upstream schema-resolution error for
        that XML file.

        This method validates every planned XML file and records the
        result in ``validator_results``.
        """
        # Validate each XML file with the corresponding schema.
        for xml_file_path, xsd_file_path in validations.items():
            # The actual validation.
            is_valid, errors = self.validation_runner.validate_xml(
                xml_file_path,
                xsd_file_path=xsd_file_path,
                base_url=base_url,
                error_facets=error_facets,
                default_error_facets=self.error_facets,
                pre_parse=pre_parse,
                skip_none_error_facets=skip_none_error_facets
                )
            # Process the validation results.
            if is_valid:
                self.validator_results.add_valid_file(xml_file_path)
            else:
                self.validator_results.add_invalid_file(xml_file_path)
                self.validator_results.add_file_errors(xml_file_path, errors)
                self.validator_results.log_file_errors(errors) # type: ignore

    def _finalize_validation_run(
        self,
        xml_file_paths: list[Path],
        is_single_xml_file: bool,
        write_to_csv: bool | None,
        timestamped: bool | None,
        error_table: bool | None,
        fail_on_errors: bool
    ) -> tuple[list[dict[str, Any]], str | None]:
        """
        Finalizes a completed validation run.

        This method handles all post-validation reporting:

        - optionally exporting collected errors to CSV
        - optionally writing a filterable error table to the log
        - logging the run summary
        - failing the Robot Framework test if configured
        - returning collected errors and the CSV path
        """
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
        # Write errors to the log file as a table if requested.
        if error_table and self.validator_results.errors_by_file:
            self.validator_results.write_error_table_to_log(
                self.validator_results.errors_by_file,
            )
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
