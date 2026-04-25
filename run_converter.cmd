@echo off
setlocal

set "PROJECT_DIR=%~dp0"
set "PYTHON_EXE=%PROJECT_DIR%.venv\Scripts\python.exe"
set "FFMPEG_CONFIG=%PROJECT_DIR%ffmpeg_path.txt"

if not exist "%PYTHON_EXE%" (
    echo Project virtual environment was not found.
    echo Run: python -m venv .venv
    exit /b 1
)

if not defined AUDIO_CONVERTER_FFMPEG if exist "%FFMPEG_CONFIG%" (
    set /p AUDIO_CONVERTER_FFMPEG=<"%FFMPEG_CONFIG%"
)

"%PYTHON_EXE%" "%PROJECT_DIR%audio_converter.py"
