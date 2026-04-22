"""
export_to_desktop.py
--------------------
Copies the entire project to a clean folder on the user's Desktop.

Usage
~~~~~
    python export_to_desktop.py

What it does
~~~~~~~~~~~~
* Detects the Desktop path cross-platform (Windows / macOS / Linux).
* Copies all project files to ``Desktop/Bety/``.
* SKIPS the following to protect credentials and avoid bloat:

    - ``config.json``         — may contain API keys
    - ``venv/`` / ``env/``    — virtualenv (recreate with pip install -r)
    - ``__pycache__/``        — compiled bytecode
    - ``.git/``               — version control history
    - ``.cursor/``            — editor workspace state
    - ``build/``              — PyInstaller intermediate files
    - ``dist/``               — compiled executables (large binary blobs)

* Prints a clear success message with the full Desktop path.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEST_FOLDER_NAME = "Bety"

# Directories / files to never copy to the export destination.
IGNORED_NAMES: frozenset[str] = frozenset(
    {
        "venv",
        "env",
        ".venv",
        ".env",
        "ENV",
        "__pycache__",
        ".git",
        ".cursor",
        ".idea",
        ".vscode",
        "build",
        "dist",
        "config.json",   # ← Protect API keys
        ".DS_Store",
        "Thumbs.db",
    }
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_desktop() -> Path:
    """Return the path to the current user's Desktop directory.

    Works on Windows, macOS, and most Linux desktops.

    Returns:
        Path: The resolved Desktop directory path.

    Raises:
        FileNotFoundError: If no Desktop directory can be located.
    """
    # Windows: use USERPROFILE env or expanduser
    desktop = Path.home() / "Desktop"
    if desktop.is_dir():
        return desktop

    # macOS fallback (localized "Desktop" may differ)
    desktop = Path(os.path.expanduser("~/Desktop"))
    if desktop.is_dir():
        return desktop

    # XDG (Linux)
    xdg_desktop = os.environ.get("XDG_DESKTOP_DIR", "")
    if xdg_desktop and Path(xdg_desktop).is_dir():
        return Path(xdg_desktop)

    raise FileNotFoundError(
        "Could not locate your Desktop directory. "
        "Please set XDG_DESKTOP_DIR or run this script from a system "
        "with a standard Desktop folder."
    )


def _ignore_filter(
    src_dir: str,
    names: list[str],
) -> set[str]:
    """``shutil.copytree`` ignore callback.

    Args:
        src_dir: The directory currently being copied.
        names:   The list of child names inside *src_dir*.

    Returns:
        set[str]: Names that should be skipped.
    """
    return {name for name in names if name in IGNORED_NAMES}


# ---------------------------------------------------------------------------
# Main export logic
# ---------------------------------------------------------------------------

def export() -> None:
    """Copy the project to the Desktop, skipping sensitive and generated files.

    Raises:
        FileNotFoundError: If no Desktop directory is found.
        OSError: If the destination cannot be created or written.
    """
    src = Path(__file__).parent.resolve()

    try:
        desktop = _get_desktop()
    except FileNotFoundError as exc:
        print(f"❌  {exc}")
        sys.exit(1)

    dest = desktop / DEST_FOLDER_NAME

    print("=" * 62)
    print("  Bety: The Privacy-First Universal Dictator — Desktop Export")
    print("=" * 62)
    print(f"  Source : {src}")
    print(f"  Target : {dest}")
    print()

    # Remove a stale export if one exists from a previous run
    if dest.exists():
        print(f"  ⚠️   Removing existing '{DEST_FOLDER_NAME}' folder…")
        shutil.rmtree(dest)

    try:
        shutil.copytree(
            src=str(src),
            dst=str(dest),
            ignore=_ignore_filter,
            dirs_exist_ok=False,
        )
    except OSError as exc:
        print(f"\n❌  Export failed: {exc}")
        sys.exit(1)

    if not (dest / "bety_ui.py").exists():
        print("\n❌  Export appears incomplete — bety_ui.py not found in destination.")
        sys.exit(1)

    print("  ✅  EXPORT SUCCESSFUL\n")
    print(f"  Your project is ready at:\n  {dest}")
    print()
    print("  Skipped (not copied):")
    for name in sorted(IGNORED_NAMES):
        print(f"    • {name}")
    print("=" * 62)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    export()
