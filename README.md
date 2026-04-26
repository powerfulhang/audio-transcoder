# Audio Format Converter

Windows desktop audio converter written with Python `tkinter`.

## Requirements

- Python 3.12
- FFmpeg installed, configured in `ffmpeg_path.txt`, or available on `PATH`

## Run

From the project directory, run:

```powershell
.\run_converter.cmd
```

The launcher creates the project virtual environment at `.venv` when it is
missing, installs `requirements.txt`, then starts the app. The `.venv` directory
is intentionally not committed to Git.

If you prefer to set up the environment manually:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe audio_converter.py
```

The app accepts a file through the Browse button or by drag-and-drop. It writes
the converted file into the source file's directory and avoids overwriting
existing files by adding `_converted` or a numeric suffix.

## FFmpeg path

The app searches for FFmpeg in this order:

1. `AUDIO_CONVERTER_FFMPEG` environment variable
2. `ffmpeg_path.txt` in this project directory
3. `ffmpeg.exe` or `tools\ffmpeg\bin\ffmpeg.exe` inside this project
4. System `PATH`

On this machine, `ffmpeg_path.txt` points to the existing local FFmpeg executable.
