# Execute all test suites in a Folder

## Syntax
robot path/to/folder

## Description
Runs all *.robot test suite files inside a given folder and its subdirectories. This command will recursively execute all .robot files within the specified folder. The test results are saved in log.html, report.html, and output.xml in the same directory unless otherwise specified.

## Example
robot tests/

Executes all .robot files inside the tests/ directory.

# Execute a specific test suite file

## Syntax
robot path/to/test_suite.robot

## Description
To specify a single test suite file to execute. Runs only the specified .robot test suite file. Other test suites in the directory are ignored.

## Example
robot tests/login_tests.robot

Executes only the login_tests.robot file.

# Execute specific test cases from a test suite

## Syntax
robot --test "Test Case Name" path/to/test_suite.robot

## Description
Robot Framework allows running specific test cases within a test suite. The --test (or -t) option runs only the specified test case(s). You can use multiple --test arguments to run multiple test cases.

## Example
robot --test "Valid Login" tests/login_tests.robot

Runs only the Valid Login test case from login_tests.robot.

robot --test "Valid Login" --test "Invalid Login" tests/login_tests.robot

Runs both Valid Login and Invalid Login test cases.

# Execute specific test cases across multiple test suites

## Syntax
robot --test "Test Case Name" path/to/folder

## Description
To run test cases from multiple test suite files.

## Example

robot --test "Valid Login" --test "User Registration" tests/

Runs test cases "Valid Login" and "User Registration" from any test suite inside tests/.

# Execute test suites by tag

## Syntax
robot --include tagname path/to/folder

## Description
Tags help filter test execution based on categories.

## Example
robot --include smoke tests/

Runs only test cases tagged with smoke in any test suite inside tests/.

To run tests with multiple tags:

robot --include regression --include critical tests/

Runs test cases tagged regression or critical.

To exclude tests with a specific tag:

robot --exclude slow tests/

Runs all tests except those tagged slow.

# Other useful execution options (syntax/description/example)

-d path/to/output
Change output directory
robot -d results/ tests/

-L DEBUG
Set log level
robot -L DEBUG tests/

--dryrun
Check syntax without executing tests
robot --dryrun tests/

--variable VAR:value
Pass a variable to tests
robot --variable ENV:staging tests/

--rerunfailed output.xml
Rerun failed tests from previous execution
robot --rerunfailed output.xml

# Summary

Run all tests in a folder: robot tests/

Run a specific test suite: robot tests/login_tests.robot

Run a specific test case: robot --test "Valid Login" tests/login_tests.robot

Run multiple test cases: robot --test "Valid Login" --test "User Registration" tests/

Run test cases by tag: robot --include smoke tests/

Change output directory: robot -d results/ tests/

python -m robot -d ./Results/current_run -o ./output -l ./log -r ./report -b ./debug C:/Projects/robotframework-xmlvalidator/test/integration