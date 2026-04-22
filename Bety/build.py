"""
build.py
--------
Compiles the Local Vibe-Voice Assistant into a standalone Windows .exe
using PyInstaller.

Usage
~~~~~
    python build.py

The finished executable will be placed in:
    dist/LocalVibeVoiceAssistant/LocalVibeVoiceAssistant.exe

Requirements
~~~~~~~~~~~~
* PyInstaller must be installed:  pip install pyinstaller
* Run this script from the project root directory.
* Build on the target platform (Windows) — PyInstaller does not
  cross-compile.
"""

from __future__ import annotations

import subprocess
import sys
import shutil
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

APP_NAME    = "Bety"
ENTRY_POINT = "bety_ui.py"
ICON_FILE   = "assets/icon.ico"

# ---------------------------------------------------------------------------
# PyInstaller arguments
# ---------------------------------------------------------------------------

def build() -> None:
    root = Path(__file__).parent.resolve()
    dist = root / "dist"
    build_dir = root / "build"

    print("=" * 62)
    print("  Local Vibe-Voice Assistant — PyInstaller Build")
    print("=" * 62)
    print(f"  Entry point : {ENTRY_POINT}")
    print(f"  Output dir  : {dist}")
    print()

    args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",                     # overwrite previous build silently
        "--clean",                         # wipe PyInstaller cache first
        "--onedir",                        # folder distribution (faster startup
                                           # than --onefile for large apps)
        "--windowed",                      # no console window on launch
        f"--name={APP_NAME}",

        # ----- customtkinter -------------------------------------------
        # Collect ALL customtkinter assets (themes, images, *.json files)
        "--collect-all", "customtkinter",

        # ----- faster-whisper / CTranslate2 ----------------------------
        "--collect-all", "faster_whisper",
        "--collect-all", "ctranslate2",    # faster-whisper backend

        # ----- sounddevice / PortAudio binaries ------------------------
        "--collect-all", "sounddevice",

        # ----- Hidden imports that PyInstaller may miss ----------------
        "--hidden-import", "scipy.io.wavfile",
        "--hidden-import", "sounddevice",
        "--hidden-import", "pystray",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL._tkinter_finder",
        "--hidden-import", "keyboard",
        "--hidden-import", "pyautogui",

        # ----- Whisper tokeniser assets --------------------------------
        "--collect-data", "faster_whisper",

        ENTRY_POINT,
    ]

    # Optionally include a custom .ico file
    if ICON_FILE and Path(root / ICON_FILE).exists():
        args += ["--icon", str(root / ICON_FILE)]

    print("Running PyInstaller…\n")
    result = subprocess.run(args, cwd=str(root))

    print()
    if result.returncode == 0:
        exe_path = dist / APP_NAME / f"{APP_NAME}.exe"
        print("=" * 62)
        print("  ✅  BUILD SUCCESSFUL")
        print(f"  Executable: {exe_path}")
        print()
        print("  To distribute the app, zip the entire folder:")
        print(f"  {dist / APP_NAME}")
        print("=" * 62)
    else:
        print("=" * 62)
        print("  ❌  BUILD FAILED")
        print("  Review the PyInstaller output above for details.")
        print("  Common fixes:")
        print("    • pip install pyinstaller --upgrade")
        print("    • Delete the 'build/' and 'dist/' folders and retry")
        print("    • Run from the project root directory")
        print("=" * 62)
        sys.exit(result.returncode)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    build()
