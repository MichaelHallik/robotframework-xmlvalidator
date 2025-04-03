@echo off
setlocal

set ENV_NAME=%1
set PACKAGE_VERSION=%2
set VENV_HOME=C:\Python-virt-envs

echo =========Create virt env========= "%ENV_NAME%"...
call mkvirtualenv %ENV_NAME%

echo =========Activate virt env========= "%ENV_NAME%"...
call workon %ENV_NAME%

echo Activated environment: %VIRTUAL_ENV%

echo =========Install robotframework-xmlvalidator==%PACKAGE_VERSION%=========
pip install --index-url https://test.pypi.org/simple --extra-index-url https://pypi.org/simple robotframework-xmlvalidator==%PACKAGE_VERSION%

echo =========Show package meta data=========
pip show robotframework-xmlvalidator

echo =========Importing package and get __version__=========
python -c "from xmlvalidator import XmlValidator; print(XmlValidator.__version__)"

echo =========Showing module file path=========
python -c "import xmlvalidator; print(xmlvalidator.__file__)"

@REM echo Generating keyword documentation with Libdoc...
@REM python -m robot.libdoc xmlvalidator.XmlValidator show

set TARGET_DIR=%VENV_HOME%\%ENV_NAME%\Lib\site-packages\xmlvalidator

setlocal ENABLEDELAYEDEXPANSION
set /p OPEN_FOLDER=Do you want to open the xmlvalidator folder in File Explorer? [y/N]: 
set "OPEN_FOLDER=!OPEN_FOLDER: =!"  & REM removes spaces

if /i "!OPEN_FOLDER!"=="y" (
    echo Opening folder: %TARGET_DIR%
    start "" "%TARGET_DIR%"
) else (
    echo Skipping folder open.
)
endlocal

endlocal