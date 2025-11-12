@echo off
REM Fix Failing CI Checks Command Wrapper for Windows

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is required but not installed
    exit /b 1
)

REM Check if GitHub CLI is available
gh --version >nul 2>&1
if errorlevel 1 (
    echo Error: GitHub CLI (gh) is required but not installed
    echo Please install it from: https://cli.github.com/
    exit /b 1
)

REM Run the Python script
python "%SCRIPT_DIR%fix-failing-ci-checks.py" --repo-path "%PROJECT_ROOT%" %*
