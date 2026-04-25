#!/usr/bin/env python3
"""Small Windows desktop audio converter.

Target Python: 3.9+
Requires:
    - FFmpeg available on PATH
    - tkinterdnd2 for drag-and-drop file input
"""
from __future__ import annotations

import shutil
import subprocess
import threading
import tkinter as tk
import os
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

try:
    # Ref: https://pypi.org/project/tkinterdnd2/
    # The project documents TkinterDnD.Tk(), DND_FILES, drop_target_register(),
    # and dnd_bind("<<Drop>>", ...). Requires Python 3.6+.
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    DND_FILES = None
    TkinterDnD = None


APP_TITLE = "Audio Format Converter"
OUTPUT_FORMATS = ("mp3", "wav", "flac", "aac", "m4a", "ogg", "opus", "wma")
APP_DIR = Path(__file__).resolve().parent
FFMPEG_CONFIG_FILE = APP_DIR / "ffmpeg_path.txt"


class AudioConverterApp:
    """Tkinter UI for choosing, dropping, and converting one audio file."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.selected_file = tk.StringVar()
        self.output_format = tk.StringVar(value=OUTPUT_FORMATS[0])
        self.status_text = tk.StringVar(value="Select or drop an audio file.")
        self.convert_button: Optional[ttk.Button] = None

        self._build_window()
        self._configure_drop_target()

    def _build_window(self) -> None:
        self.root.title(APP_TITLE)
        self.root.minsize(620, 310)

        main = ttk.Frame(self.root, padding=18)
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main.columnconfigure(0, weight=1)

        title = ttk.Label(main, text=APP_TITLE, font=("Segoe UI", 16, "bold"))
        title.grid(row=0, column=0, sticky="w")

        hint = ttk.Label(
            main,
            text="Choose a file, or drag one onto the box below.",
            foreground="#555555",
        )
        hint.grid(row=1, column=0, sticky="w", pady=(4, 14))

        file_row = ttk.Frame(main)
        file_row.grid(row=2, column=0, sticky="ew")
        file_row.columnconfigure(0, weight=1)

        # Ref: https://docs.python.org/3/library/tkinter.html
        self.file_entry = ttk.Entry(
            file_row,
            textvariable=self.selected_file,
            state="readonly",
        )
        self.file_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        browse_button = ttk.Button(
            file_row,
            text="Browse...",
            command=self.select_file,
        )
        browse_button.grid(row=0, column=1)

        self.drop_label = tk.Label(
            main,
            text="Drop audio file here",
            relief="ridge",
            borderwidth=2,
            background="#f4f6f8",
            foreground="#333333",
            height=6,
        )
        self.drop_label.grid(row=3, column=0, sticky="ew", pady=14)

        options = ttk.Frame(main)
        options.grid(row=4, column=0, sticky="ew")
        options.columnconfigure(1, weight=1)

        ttk.Label(options, text="Export format").grid(row=0, column=0, sticky="w")

        # Ref: https://docs.python.org/3/library/tkinter.ttk.html#combobox
        format_box = ttk.Combobox(
            options,
            textvariable=self.output_format,
            values=OUTPUT_FORMATS,
            state="readonly",
            width=12,
        )
        format_box.grid(row=0, column=1, sticky="w", padx=(10, 0))

        self.convert_button = ttk.Button(
            options,
            text="Convert",
            command=self.start_conversion,
        )
        self.convert_button.grid(row=0, column=2, sticky="e")

        status = ttk.Label(main, textvariable=self.status_text, foreground="#555555")
        status.grid(row=5, column=0, sticky="ew", pady=(16, 0))

    def _configure_drop_target(self) -> None:
        if DND_FILES is None:
            self.drop_label.configure(
                text="Drag-and-drop needs tkinterdnd2. Use Browse instead.",
                foreground="#8a4b00",
            )
            return

        # Ref: https://pypi.org/project/tkinterdnd2/
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind("<<Drop>>", self.handle_drop)

    def select_file(self) -> None:
        # Ref: https://docs.python.org/3/library/dialog.html#tkinter.filedialog.askopenfilename
        file_name = filedialog.askopenfilename(
            title="Select audio file",
            filetypes=(
                ("Audio files", "*.mp3 *.wav *.flac *.aac *.m4a *.ogg *.opus *.wma"),
                ("All files", "*.*"),
            ),
        )
        if file_name:
            self.set_selected_file(Path(file_name))

    def handle_drop(self, event: tk.Event) -> None:
        # Ref: https://pypi.org/project/tkinterdnd2/
        # tk.splitlist handles Windows paths wrapped in braces by Tk DND.
        files = self.root.tk.splitlist(event.data)
        if not files:
            return
        self.set_selected_file(Path(files[0]))

    def set_selected_file(self, path: Path) -> None:
        if not path.is_file():
            messagebox.showerror("Invalid file", "Please choose an existing file.")
            return
        self.selected_file.set(str(path))
        self.status_text.set("Ready to convert.")

    def start_conversion(self) -> None:
        source_text = self.selected_file.get()
        if not source_text:
            messagebox.showwarning("No file", "Please choose an audio file first.")
            return

        ffmpeg_path = resolve_ffmpeg_path()
        if ffmpeg_path is None:
            messagebox.showerror(
                "FFmpeg not found",
                "FFmpeg was not found. Put ffmpeg.exe on PATH, place it in this "
                "project, or set ffmpeg_path.txt.",
            )
            return

        source = Path(source_text)
        target_format = self.output_format.get().lower()
        output = build_output_path(source, target_format)

        self._set_busy(True)
        self.status_text.set(f"Converting to {output.name}...")

        worker = threading.Thread(
            target=self._convert_in_background,
            args=(ffmpeg_path, source, output),
            daemon=True,
        )
        worker.start()

    def _convert_in_background(
        self,
        ffmpeg_path: str,
        source: Path,
        output: Path,
    ) -> None:
        try:
            convert_audio(ffmpeg_path, source, output)
        except subprocess.TimeoutExpired:
            self.root.after(
                0,
                self._conversion_failed,
                "Conversion timed out after 30 minutes.",
            )
        except subprocess.CalledProcessError as exc:
            message = exc.stderr.strip() or "FFmpeg reported an unknown error."
            self.root.after(0, self._conversion_failed, message)
        except OSError as exc:
            self.root.after(0, self._conversion_failed, str(exc))
        else:
            self.root.after(0, self._conversion_finished, output)

    def _conversion_finished(self, output: Path) -> None:
        self._set_busy(False)
        self.status_text.set(f"Done: {output}")
        messagebox.showinfo("Conversion complete", f"Created:\n{output}")

    def _conversion_failed(self, message: str) -> None:
        self._set_busy(False)
        self.status_text.set("Conversion failed.")
        messagebox.showerror("Conversion failed", message)

    def _set_busy(self, busy: bool) -> None:
        if self.convert_button is not None:
            self.convert_button.configure(state="disabled" if busy else "normal")


def build_output_path(source: Path, target_format: str) -> Path:
    """Return a non-overwriting output path in the source file directory.

    Ref: https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.with_suffix
    """
    suffix = f".{target_format}"
    base = source.with_suffix(suffix)

    if base == source or base.exists():
        base = source.with_name(f"{source.stem}_converted{suffix}")

    candidate = base
    counter = 1
    while candidate.exists():
        candidate = base.with_name(f"{base.stem}_{counter}{base.suffix}")
        counter += 1
    return candidate


def convert_audio(ffmpeg_path: str, source: Path, output: Path) -> None:
    """Convert audio by invoking FFmpeg.

    Ref: https://ffmpeg.org/documentation.html
         FFmpeg command-line tools use an input specified with -i followed by
         an output file.
    Ref: https://docs.python.org/3/library/subprocess.html#subprocess.run
         subprocess.run accepts argument lists, check, capture_output, text,
         and timeout.
    """
    subprocess.run(
        [
            ffmpeg_path,
            "-hide_banner",
            "-y",
            "-i",
            str(source),
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=1800,
    )


def resolve_ffmpeg_path() -> Optional[str]:
    """Find the FFmpeg executable for this project.

    Ref: https://docs.python.org/3/library/os.html#os.environ
    Ref: https://docs.python.org/3/library/shutil.html#shutil.which
    Ref: https://docs.python.org/3/library/pathlib.html#pathlib.Path.is_file
    """
    configured_paths = [
        os.environ.get("AUDIO_CONVERTER_FFMPEG"),
        read_configured_ffmpeg_path(),
        str(APP_DIR / "ffmpeg.exe"),
        str(APP_DIR / "tools" / "ffmpeg.exe"),
        str(APP_DIR / "tools" / "ffmpeg" / "ffmpeg.exe"),
        str(APP_DIR / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe"),
        shutil.which("ffmpeg"),
    ]

    for candidate in configured_paths:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if path.is_file():
            return str(path)
    return None


def read_configured_ffmpeg_path() -> Optional[str]:
    """Read a project-local FFmpeg path override.

    Ref: https://docs.python.org/3/library/pathlib.html#pathlib.Path.read_text
         Text file reads should use an explicit encoding.
    """
    if not FFMPEG_CONFIG_FILE.is_file():
        return None
    configured = FFMPEG_CONFIG_FILE.read_text(encoding="utf-8").strip()
    if not configured or configured.startswith("#"):
        return None
    return configured


def create_root() -> tk.Tk:
    if TkinterDnD is not None:
        return TkinterDnD.Tk()
    return tk.Tk()


def main() -> None:
    root = create_root()
    AudioConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
