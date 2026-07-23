# Running pytest on multiple files and test cases

## Run all tests in the project

python -m pytest test/unit

    Runs all test cases in all test_*.py files within the project.

## Run all tests in a specific test file

python -m pytest test/unit/test_xmlvalidator.py

    Runs all test cases inside test/unit/test_xmlvalidator.py.

python -m pytest test/unit/test_xmlvalidator.py test/unit/test_namespaces.py

    Runs all tests from multiple test files.

## Run specific test case(s) from one or more test files

You can run a single specific test case using pytest by specifying the test module name and the test function name.

Basic Syntax:

    python -m pytest test/unit/test_module.py::test_function_name

Examples:

    python -m pytest test/unit/test_schema_resolver.py::test_match_xml_files_to_schemas_namespace_matching_success

        Runs only the test_match_xml_files_to_schemas_namespace_matching_success function inside test/unit/test_schema_resolver.py.

    python -m pytest test/unit/test_schema_resolver.py::test_match_xml_files_to_schemas_namespace_matching_success test/unit/test_namespaces.py::test_schema_matches_xml_namespaces_returns_true_for_matching_target_namespace

        Runs two specific test cases from two different files.

# Advanced filtering & options

## Run tests with verbose output (-v)

python -m pytest -v

Shows detailed test output (pass/fail status).

python -m pytest -v test/unit/test_schema_resolver.py::test_match_xml_files_to_schemas_namespace_matching_success

## Stop on first failure (-x)

python -m pytest -x

Stops running when the first test fails.

python -m pytest -x test/unit/test_schema_resolver.py::test_match_xml_files_to_schemas_namespace_matching_success

## Display print statements (-s)

python -m pytest -s

Shows print output inside tests.

python -m pytest -s test/unit/test_schema_resolver.py::test_match_xml_files_to_schemas_namespace_matching_success

## Show detailed traceback (--tb=long)

python -m pytest --tb=long test/unit/test_schema_resolver.py::test_match_xml_files_to_schemas_namespace_matching_success

## Run tests matching a pattern

python -m pytest -k "schema"

Runs all tests where the function name contains "schema".
