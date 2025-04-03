# Running pytest on multiple files and test cases

## Run all tests in the project

python -m pytest test/

    Runs all test cases in all test_*.py files within the project.

## Run all tests in a specific test file

pytest test/test_xmlvalidator.py

    Runs all test cases inside test/test_xmlvalidator.py.

pytest test/test_xmlvalidator.py test/test_xml_validator_utils.py

    Runs all tests from multiple test files.

## Run specific test case(s) from one or more test files

You can run a single specific test case using pytest by specifying the test module name and the test function name.

Basic Syntax:

    pytest test/test_module.py::test_function_name

Examples:

    pytest test/test_xmlvalidator.py::test_find_schemas_namespace_matching_success

        Runs only the test_find_schemas_namespace_matching_success function inside test/test_xmlvalidator.py.

    pytest test/test_xmlvalidator.py::test_find_schemas_namespace_matching_success test/test_xml_validator_utils.py::test_match_namespace_to_schema_valid_target_namespace

        Runs two specific test cases from two different files.

# Advanced filtering & options

## Run tests with verbose output (-v)

pytest -v

Shows detailed test output (pass/fail status).

pytest -v test/test_xmlvalidator.py::test_find_schemas_namespace_matching_success

## Stop on first failure (-x)

pytest -x

Stops running when the first test fails.

pytest -x test/test_xmlvalidator.py::test_find_schemas_namespace_matching_success

## Display print statements (-s)

pytest -s

Shows print output inside tests.

pytest -s test/test_xmlvalidator.py::test_find_schemas_namespace_matching_success

## Show detailed traceback (--tb=long)

pytest --tb=long test/test_xmlvalidator.py::test_find_schemas_namespace_matching_success

## Run tests matching a pattern

pytest -k "schema"

Runs all tests where the function name contains "schema".