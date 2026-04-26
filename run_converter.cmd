@echo off
setlocal

set "PROJECT_DIR=%~dp0"
set "VENV_DIR=%PROJECT_DIR%.venv"
set "PYTHON_EXE=%PROJECT_DIR%.venv\Scripts\python.exe"
set "REQUIREMENTS=%PROJECT_DIR%requirements.txt"
set "REQUIREMENTS_MARKER=%VENV_DIR%\requirements.installed.txt"
set "FFMPEG_CONFIG=%PROJECT_DIR%ffmpeg_path.txt"
set "BASE_PYTHON="
set "INSTALL_REQUIREMENTS="

where python >nul 2>nul
if not errorlevel 1 set "BASE_PYTHON=python"
if not defined BASE_PYTHON (
    where py >nul 2>nul
    if not errorlevel 1 set "BASE_PYTHON=py -3"
)

if not exist "%PYTHON_EXE%" (
    if not defined BASE_PYTHON (
        echo Python was not found. Install Python 3.12 or newer, then run this file again.
        exit /b 1
    )

    echo Creating project virtual environment...
    rem Ref: Python docs, venv - Creation of virtual environments.
    %BASE_PYTHON% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Failed to create the project virtual environment.
        exit /b 1
    )
)

"%PYTHON_EXE%" -m pip --version >nul 2>nul
if errorlevel 1 (
    echo Installing pip into the project virtual environment...
    rem Ref: Python docs, ensurepip - Bootstrapping the pip installer.
    "%PYTHON_EXE%" -m ensurepip --upgrade --default-pip
    if errorlevel 1 (
        echo Failed to install pip into the project virtual environment.
        exit /b 1
    )
)

if exist "%REQUIREMENTS%" (
    if not exist "%REQUIREMENTS_MARKER%" set "INSTALL_REQUIREMENTS=1"
    if not defined INSTALL_REQUIREMENTS (
        fc /b "%REQUIREMENTS%" "%REQUIREMENTS_MARKER%" >nul 2>nul
        if errorlevel 1 set "INSTALL_REQUIREMENTS=1"
    )
    if defined INSTALL_REQUIREMENTS (
        echo Installing project dependencies...
        rem Ref: pip user guide, Installing Packages.
        "%PYTHON_EXE%" -m pip install -r "%REQUIREMENTS%"
        if errorlevel 1 (
            echo Failed to install project dependencies.
            exit /b 1
        )
        copy /y "%REQUIREMENTS%" "%REQUIREMENTS_MARKER%" >nul
    )
)
if /i "%~1"=="--setup-only" exit /b 0

if not defined AUDIO_CONVERTER_FFMPEG if exist "%FFMPEG_CONFIG%" (
    set /p AUDIO_CONVERTER_FFMPEG=<"%FFMPEG_CONFIG%"
)

"%PYTHON_EXE%" "%PROJECT_DIR%audio_converter.py"
exit /b %ERRORLEVEL%
